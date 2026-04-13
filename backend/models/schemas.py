from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class ScanRequest(BaseModel):
    files: List[str]
    enable_ai: bool = True

class GitHubPRRequest(BaseModel):
    repo: str
    pr_number: int
    enable_ai: bool = True

class Issue(BaseModel):
    type: str
    severity: str
    file: str
    line: int
    column: Optional[int] = None
    message: str
    rule_id: Optional[str] = None
    ai_suggestion: Optional[str] = None

class ScanSummary(BaseModel):
    total_files: int
    total_issues: int
    critical: int
    high: int
    medium: int
    low: int

class ScanResult(BaseModel):
    scan_id: str
    timestamp: datetime
    summary: ScanSummary
    issues: List[Issue]

class ScanHistory(BaseModel):
    scan_id: str
    type: str
    timestamp: datetime
    files_scanned: int
    issues_found: int
    summary: Dict

class CustomRule(BaseModel):
    rule_id: str
    name: str
    description: str
    severity: str
    enabled: bool = True