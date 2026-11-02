"""
IP FORGE: Review Policy & Configuration Schema (.ip-forge.yaml).
Defines project architecture rules, required acceptance checks, and severity policies.
"""
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StateManagementConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    adapter: Literal["unspecified", "riverpod", "bloc", "provider", "native"] = "unspecified"
    exceptions: List[str] = Field(default_factory=list)


class CacheRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_scoped: bool = True
    clear_private_data_on_logout: bool = True
    max_age_seconds: int = 300


class CacheConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    policy: str = "stale_while_revalidate"
    requirements: CacheRequirements = Field(default_factory=CacheRequirements)


class FlowDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    test: str = Field(min_length=1)
    platforms: List[str] = Field(default_factory=lambda: ["web"])


class ReportConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fail_on: List[Literal["error", "warning", "info"]] = Field(default_factory=lambda: ["error"])
    fail_on_required_missing: bool = True


class ReviewPolicy(BaseModel):
    """
    Project-level review policy defining architectural boundaries and acceptance checks.
    """
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    flutter_root: str = "."
    platforms: List[str] = Field(default_factory=lambda: ["android", "ios", "web"])
    state_adapter: Literal["unspecified", "riverpod", "bloc", "provider", "native"] = "unspecified"
    state_management: Optional[StateManagementConfig] = None
    cache: Optional[CacheConfig] = None
    checks: Optional[Dict[str, str]] = None
    flows: List[FlowDefinition] = Field(default_factory=list)
    report: Optional[ReportConfig] = None
    required_checks: List[str] = Field(default_factory=lambda: ["analyze", "unit_widget"])
    fail_on: List[Literal["error", "warning", "info"]] = Field(default_factory=lambda: ["error"])

    @model_validator(mode="before")
    @classmethod
    def sync_legacy_and_yaml_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Sync state_management -> state_adapter
        if "state_management" in data and data["state_management"]:
            sm = data["state_management"]
            if isinstance(sm, dict) and "adapter" in sm:
                data.setdefault("state_adapter", sm["adapter"])

        # Sync checks dictionary -> required_checks
        if "checks" in data and isinstance(data["checks"], dict):
            reqs = [
                name
                for name, level in data["checks"].items()
                if level == "required"
            ]
            if reqs:
                data["required_checks"] = reqs

        # Sync report config -> fail_on
        if "report" in data and isinstance(data["report"], dict):
            if "fail_on" in data["report"]:
                data["fail_on"] = data["report"]["fail_on"]

        return data

    @model_validator(mode="after")
    def validate_checks(self):
        if not self.required_checks or any(not name.strip() for name in self.required_checks):
            raise ValueError("At least one nonempty required check is necessary")
        if len(set(self.required_checks)) != len(self.required_checks):
            raise ValueError("Required checks must be unique")
        # Ensure state_management sub-model is populated if state_adapter was set directly
        if self.state_management is None:
            self.state_management = StateManagementConfig(adapter=self.state_adapter)
        if self.report is None:
            self.report = ReportConfig(fail_on=self.fail_on)
        return self


    def unsupported_features(self) -> list[str]:
        """Fail closed for declarations the alpha cannot enforce."""
        features = []
        if self.flutter_root != '.':
            features.append('flutter_root (pass the project directory directly)')
        if self.state_adapter != 'unspecified' or self.state_management.adapter != 'unspecified' or self.state_management.exceptions:
            features.append('state_management rules')
        if self.cache is not None:
            features.append('cache requirements')
        if self.flows:
            features.append('registered flows')
        if 'platforms' in self.model_fields_set:
            features.append('platform selection')
        if self.checks is not None and any(level != 'required' for level in self.checks.values()):
            features.append('checks levels other than required')
        if not self.report.fail_on_required_missing:
            features.append('report.fail_on_required_missing=false')
        return features


def load_policy(source: Path | str | None = None) -> ReviewPolicy:
    """
    Loads ReviewPolicy from a .ip-forge.yaml file, directory, or returns default policy.
    """
    if source is None:
        candidate = Path(".ip-forge.yaml")
        if candidate.is_file():
            source = candidate
        else:
            candidate_alt = Path(".ip-forge.yml")
            if candidate_alt.is_file():
                source = candidate_alt
            else:
                return ReviewPolicy()

    p = Path(source)
    if p.is_dir():
        for candidate in [p / ".ip-forge.yaml", p / ".ip-forge.yml"]:
            if candidate.is_file():
                return load_policy(candidate)
        return ReviewPolicy()

    if not p.is_file():
        raise FileNotFoundError(f"Policy file not found: {p}")

    content = p.read_text(encoding="utf-8")
    data = yaml.safe_load(content) or {}
    return ReviewPolicy(**data)
