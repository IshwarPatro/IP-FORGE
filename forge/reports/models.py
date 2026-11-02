"""Reports never infer success from an absent or unexecuted check."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from forge.flutter.policy import ReviewPolicy


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Finding(StrictModel):
    rule_id: str = Field(min_length=1)
    severity: Literal['error', 'warning', 'info']
    message: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    evidence_kind: Literal['static_inference', 'reproduced_failure']
    file: str | None = None
    line: int | None = Field(default=None, ge=1)


class CheckResult(StrictModel):
    name: str = Field(min_length=1)
    status: Literal['passed', 'failed', 'not_run', 'unsupported', 'inconclusive', 'not_applicable', 'cancelled']
    summary: str = Field(min_length=1)
    findings: list[Finding] = Field(default_factory=list)


class ReviewReport(StrictModel):
    schema_version: Literal[1] = 1
    workspace: str = Field(min_length=1)
    tested_revision: str | None = None
    checks: list[CheckResult] = Field(default_factory=list)

    @model_validator(mode='after')
    def unique_results(self):
        names = [check.name for check in self.checks]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate check results are ambiguous')
        return self

    def exit_code(self, policy: ReviewPolicy) -> int:
        if any(c.status == 'failed' or any(f.severity in policy.fail_on for f in c.findings) for c in self.checks):
            return 1
        by_name = {c.name: c for c in self.checks}
        if any(name not in by_name or by_name[name].status != 'passed' for name in policy.required_checks):
            return 2
        return 0
