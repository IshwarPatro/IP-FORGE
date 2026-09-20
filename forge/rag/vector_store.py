"""
IP FORGE: ChromaDB Codebase Vector Store
Stores and queries AST-indexed code symbols, enabling grounded repository RAG.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from pydantic import BaseModel, Field
from forge.config import settings, setup_logger
from forge.rag.ast_parser import ASTParser, ASTSymbol

logger = setup_logger("forge.rag.vector_store")


class SearchResult(BaseModel):
    """Normalized query match from the ChromaDB vector store."""
    symbol_name: str
    symbol_type: str
    file_path: str
    start_line: int
    end_line: int
    parent_class: Optional[str] = None
    signature: Optional[str] = None
    snippet: str
    similarity_score: float = 0.0


class CodebaseVectorStore:
    """Manages persistent ChromaDB collection for codebase AST symbols."""

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        self.persist_dir = Path(persist_dir or settings.CHROMA_PERSIST_DIR).resolve()
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME

        self.persist_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"Connecting to ChromaDB at: {self.persist_dir} "
            f"[Collection: {self.collection_name}]"
        )

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "AST Symbol Index for IP FORGE"}
        )

    def index_repository(self, repo_path: Optional[Path] = None) -> int:
        """Parses target repository AST and stores semantic chunks in ChromaDB."""
        target_path = (repo_path or settings.target_repo_absolute_path).resolve()
        logger.info(f"Beginning AST indexing of repository: {target_path}")

        parser = ASTParser()
        file_summaries = parser.parse_directory(target_path)

        symbols: List[ASTSymbol] = []
        for summary in file_summaries:
            symbols.extend(summary.symbols)

        if not symbols:
            logger.warning("No AST symbols found to index.")
            return 0

        # Prepare payloads
        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for sym in symbols:
            ids.append(sym.qualified_id)
            documents.append(sym.to_embedding_text())
            metadatas.append({
                "symbol_name": sym.name,
                "symbol_type": sym.symbol_type,
                "file_path": sym.file_path,
                "start_line": sym.start_line,
                "end_line": sym.end_line,
                "parent_class": sym.parent_class or "",
                "signature": sym.signature,
            })

        # Upsert in batches of 100 to prevent buffer overflow
        batch_size = 100
        total_indexed = 0
        for i in range(0, len(ids), batch_size):
            end_idx = min(i + batch_size, len(ids))
            self.collection.upsert(
                ids=ids[i:end_idx],
                documents=documents[i:end_idx],
                metadatas=metadatas[i:end_idx]
            )
            total_indexed += (end_idx - i)

        logger.info(f"Successfully indexed {total_indexed} AST symbols into ChromaDB.")
        return total_indexed

    def query_codebase(
        self,
        query: str,
        top_k: int = 5,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Queries the vector store for semantic code snippets matching the developer intent."""
        if self.collection.count() == 0:
            logger.warning("ChromaDB collection is empty. Please index target repository first.")
            return []

        kwargs: Dict[str, Any] = {
            "query_texts": [query],
            "n_results": min(top_k, self.collection.count()),
        }
        if where_filter:
            kwargs["where"] = where_filter

        results = self.collection.query(**kwargs)

        search_results: List[SearchResult] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return search_results

        ids = results["ids"][0]
        documents = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results.get("distances") else []

        for idx in range(len(ids)):
            meta = metadatas[idx] if idx < len(metadatas) else {}
            doc = documents[idx] if idx < len(documents) else ""
            dist = distances[idx] if idx < len(distances) else 0.0
            
            # Convert cosine distance to approximate similarity score
            similarity = max(0.0, 1.0 - (dist / 2.0))

            search_results.append(SearchResult(
                symbol_name=meta.get("symbol_name", ""),
                symbol_type=meta.get("symbol_type", ""),
                file_path=meta.get("file_path", ""),
                start_line=int(meta.get("start_line", 0)),
                end_line=int(meta.get("end_line", 0)),
                parent_class=meta.get("parent_class") or None,
                signature=meta.get("signature"),
                snippet=doc,
                similarity_score=round(similarity, 4)
            ))

        return search_results

    def reset_collection(self):
        """Clears all symbols from the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "AST Symbol Index for IP FORGE"}
        )
        logger.info(f"Reset ChromaDB collection: {self.collection_name}")


_default_store: Optional[CodebaseVectorStore] = None


def get_vector_store() -> CodebaseVectorStore:
    """Returns singleton CodebaseVectorStore instance."""
    global _default_store
    if _default_store is None:
        _default_store = CodebaseVectorStore()
    return _default_store
