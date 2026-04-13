from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Form, Request, Body
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone
import tempfile
import shutil
import json
import hashlib
import hmac

from services.code_scanner import CodeScanner
from services.ai_suggestions import AISuggestionService
from services.github_service import GitHubService
from models.schemas import (
    ScanRequest, ScanResult, GitHubPRRequest,
    ScanHistory, Issue, CustomRule, CustomRuleCreate, CustomRuleUpdate,
    WebhookConfig
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="CodeQuality Gate", version="2.0.0")
api_router = APIRouter(prefix="/api")

code_scanner = CodeScanner()
ai_service = AISuggestionService()
github_service = GitHubService()

# ═══════════════════════════════════════════
# CORE ENDPOINTS
# ═══════════════════════════════════════════

@api_router.get("/")
async def root():
    return {"message": "CodeQuality Gate API is running"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# ═══════════════════════════════════════════
# SCAN ENDPOINTS
# ═══════════════════════════════════════════

@api_router.post("/scan/upload")
async def scan_uploaded_files(
    files: List[UploadFile] = File(...),
    enable_ai: bool = Form(default=True)
):
    """Scan uploaded files for code quality issues"""
    try:
        temp_dir = tempfile.mkdtemp()
        file_paths = []

        for file in files:
            file_path = Path(temp_dir) / file.filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            content = await file.read()
            file_path.write_bytes(content)
            file_paths.append(str(file_path))

        custom_rules = await _get_enabled_custom_rules()
        scan_result = await code_scanner.scan_files(file_paths, custom_rules=custom_rules)

        if enable_ai and scan_result['issues']:
            for issue in scan_result['issues']:
                suggestion = await ai_service.get_suggestion(issue)
                issue['ai_suggestion'] = suggestion

        scan_id = str(uuid.uuid4())
        scan_history = {
            'scan_id': scan_id,
            'type': 'file_upload',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'files_scanned': len(file_paths),
            'issues_found': len(scan_result['issues']),
            'summary': scan_result['summary'],
            'issues': scan_result['issues']
        }

        await db.scan_history.insert_one(scan_history)
        shutil.rmtree(temp_dir)

        return JSONResponse(content={
            'scan_id': scan_id,
            'summary': scan_result['summary'],
            'issues': scan_result['issues'],
            'timestamp': scan_history['timestamp']
        })

    except Exception as e:
        logging.error(f"Error scanning files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/scan/github-pr")
async def scan_github_pr(
    repo: str = Form(...),
    pr_number: int = Form(...),
    enable_ai: bool = Form(default=True)
):
    """Scan a GitHub PR for code quality issues"""
    try:
        pr_data = await github_service.get_pr_files(repo, pr_number)
        if not pr_data:
            raise HTTPException(status_code=404, detail="PR not found or GitHub token not configured")

        temp_dir = tempfile.mkdtemp()
        file_paths = []

        for file_info in pr_data['files']:
            if file_info.get('content'):
                file_path = Path(temp_dir) / file_info['filename']
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file_info['content'])
                file_paths.append(str(file_path))

        custom_rules = await _get_enabled_custom_rules()
        scan_result = await code_scanner.scan_files(file_paths, custom_rules=custom_rules)

        if enable_ai and scan_result['issues']:
            for issue in scan_result['issues']:
                suggestion = await ai_service.get_suggestion(issue)
                issue['ai_suggestion'] = suggestion

        scan_id = str(uuid.uuid4())
        scan_history = {
            'scan_id': scan_id,
            'type': 'github_pr',
            'repo': repo,
            'pr_number': pr_number,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'files_scanned': len(file_paths),
            'issues_found': len(scan_result['issues']),
            'summary': scan_result['summary'],
            'issues': scan_result['issues']
        }

        await db.scan_history.insert_one(scan_history)
        shutil.rmtree(temp_dir)

        return JSONResponse(content={
            'scan_id': scan_id,
            'pr_info': pr_data['pr_info'],
            'summary': scan_result['summary'],
            'issues': scan_result['issues'],
            'timestamp': scan_history['timestamp']
        })

    except Exception as e:
        logging.error(f"Error scanning GitHub PR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/scan/history")
async def get_scan_history():
    """Get scan history"""
    try:
        history = await db.scan_history.find({}, {"_id": 0}).sort("timestamp", -1).limit(50).to_list(50)
        return JSONResponse(content={"history": history})
    except Exception as e:
        logging.error(f"Error fetching scan history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/scan/{scan_id}")
async def get_scan_details(scan_id: str):
    """Get detailed scan results"""
    try:
        scan = await db.scan_history.find_one({"scan_id": scan_id}, {"_id": 0})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        return JSONResponse(content=scan)
    except Exception as e:
        logging.error(f"Error fetching scan details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/scan/{scan_id}/download")
async def download_scan_report(scan_id: str, format: str = "json"):
    """Download scan report in JSON or HTML format"""
    try:
        scan = await db.scan_history.find_one({"scan_id": scan_id}, {"_id": 0})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")

        if format == "json":
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
            json.dump(scan, temp_file, indent=2)
            temp_file.close()
            return FileResponse(temp_file.name, media_type='application/json', filename=f"scan_{scan_id}.json")
        elif format == "html":
            html_content = generate_html_report(scan)
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html')
            temp_file.write(html_content)
            temp_file.close()
            return FileResponse(temp_file.name, media_type='text/html', filename=f"scan_{scan_id}.html")
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'html'")

    except Exception as e:
        logging.error(f"Error downloading report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# CUSTOM RULES ENDPOINTS
# ═══════════════════════════════════════════

DEFAULT_RULES = [
    {"rule_id": "no-console", "name": "No Console Statements", "description": "Disallow console.log, console.debug, etc.", "severity": "low", "enabled": True, "pattern": None, "file_types": [".js", ".jsx", ".ts", ".tsx"], "category": "code-quality"},
    {"rule_id": "no-debugger", "name": "No Debugger", "description": "Disallow debugger statements", "severity": "high", "enabled": True, "pattern": None, "file_types": [".js", ".jsx", ".ts", ".tsx"], "category": "code-quality"},
    {"rule_id": "no-var", "name": "No Var", "description": "Use let or const instead of var", "severity": "medium", "enabled": True, "pattern": None, "file_types": [".js", ".jsx", ".ts", ".tsx"], "category": "code-quality"},
    {"rule_id": "no-eval", "name": "No Eval", "description": "Disallow eval() for security", "severity": "critical", "enabled": True, "pattern": None, "file_types": [".js", ".jsx", ".ts", ".tsx", ".py"], "category": "security"},
    {"rule_id": "no-secrets", "name": "No Exposed Secrets", "description": "Detect hardcoded API keys, tokens, passwords", "severity": "critical", "enabled": True, "pattern": None, "file_types": [".js", ".jsx", ".ts", ".tsx", ".py"], "category": "security"},
    {"rule_id": "no-unused-imports", "name": "No Unused Imports", "description": "Detect potentially unused imports", "severity": "low", "enabled": True, "pattern": None, "file_types": [".js", ".jsx", ".ts", ".tsx"], "category": "code-quality"},
    {"rule_id": "no-any", "name": "No Any Type", "description": "Avoid using TypeScript 'any' type", "severity": "medium", "enabled": True, "pattern": None, "file_types": [".ts", ".tsx"], "category": "typescript"},
    {"rule_id": "no-non-null-assertion", "name": "No Non-Null Assertion", "description": "Avoid non-null assertion operator", "severity": "medium", "enabled": True, "pattern": None, "file_types": [".ts", ".tsx"], "category": "typescript"},
    {"rule_id": "no-print", "name": "No Print Statements", "description": "Use logging instead of print()", "severity": "low", "enabled": True, "pattern": None, "file_types": [".py"], "category": "code-quality"},
    {"rule_id": "no-bare-except", "name": "No Bare Except", "description": "Specify exception types in except clauses", "severity": "high", "enabled": True, "pattern": None, "file_types": [".py"], "category": "code-quality"},
    {"rule_id": "no-mutable-defaults", "name": "No Mutable Defaults", "description": "Avoid mutable default function arguments", "severity": "high", "enabled": True, "pattern": None, "file_types": [".py"], "category": "code-quality"},
]


@api_router.get("/rules")
async def get_rules():
    """Get all scanning rules (default + custom)"""
    try:
        rules = await db.rules.find({}, {"_id": 0}).to_list(200)
        if not rules:
            for rule in DEFAULT_RULES:
                await db.rules.insert_one({**rule})
            rules = await db.rules.find({}, {"_id": 0}).to_list(200)
        return JSONResponse(content={"rules": rules})
    except Exception as e:
        logging.error(f"Error fetching rules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/rules")
async def create_rule(rule: CustomRuleCreate):
    """Create a new custom scanning rule"""
    try:
        rule_id = f"custom-{str(uuid.uuid4())[:8]}"
        new_rule = {
            "rule_id": rule_id,
            "name": rule.name,
            "description": rule.description,
            "severity": rule.severity,
            "enabled": True,
            "pattern": rule.pattern,
            "file_types": rule.file_types,
            "category": rule.category,
        }
        await db.rules.insert_one(new_rule)
        return JSONResponse(content={"rule_id": rule_id, "message": "Rule created successfully"})
    except Exception as e:
        logging.error(f"Error creating rule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/rules/{rule_id}")
async def update_rule(rule_id: str, update: CustomRuleUpdate):
    """Update a scanning rule (toggle, change severity, etc.)"""
    try:
        update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
        if not update_dict:
            raise HTTPException(status_code=400, detail="No update fields provided")

        result = await db.rules.update_one({"rule_id": rule_id}, {"$set": update_dict})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Rule not found")
        return JSONResponse(content={"message": "Rule updated successfully"})
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating rule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """Delete a custom rule (only custom rules can be deleted)"""
    try:
        rule = await db.rules.find_one({"rule_id": rule_id}, {"_id": 0})
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        if rule.get("category") != "custom":
            raise HTTPException(status_code=400, detail="Cannot delete built-in rules")

        await db.rules.delete_one({"rule_id": rule_id})
        return JSONResponse(content={"message": "Rule deleted successfully"})
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting rule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_enabled_custom_rules():
    """Get enabled custom pattern rules from DB"""
    rules = await db.rules.find({"enabled": True, "pattern": {"$ne": None}}, {"_id": 0}).to_list(100)
    return rules


# ═══════════════════════════════════════════
# WEBHOOK / CI/CD ENDPOINTS
# ═══════════════════════════════════════════

@api_router.get("/webhook/config")
async def get_webhook_config():
    """Get webhook configuration"""
    try:
        config = await db.webhook_config.find_one({}, {"_id": 0})
        if not config:
            backend_url = os.environ.get('CORS_ORIGINS', 'https://quality-gate-15.preview.emergentagent.com')
            webhook_secret = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:32]
            config = {
                "webhook_url": f"https://quality-gate-15.preview.emergentagent.com/api/webhook/github",
                "webhook_secret": webhook_secret,
                "enabled": True,
                "auto_scan": True,
                "enable_ai": True,
                "repos": [],
            }
            await db.webhook_config.insert_one({**config})
        return JSONResponse(content=config)
    except Exception as e:
        logging.error(f"Error fetching webhook config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/webhook/config")
async def update_webhook_config(
    enabled: Optional[bool] = Body(None),
    auto_scan: Optional[bool] = Body(None),
    enable_ai: Optional[bool] = Body(None),
):
    """Update webhook configuration"""
    try:
        update_dict = {}
        if enabled is not None:
            update_dict["enabled"] = enabled
        if auto_scan is not None:
            update_dict["auto_scan"] = auto_scan
        if enable_ai is not None:
            update_dict["enable_ai"] = enable_ai

        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")

        config = await db.webhook_config.find_one({})
        if not config:
            await get_webhook_config()

        await db.webhook_config.update_one({}, {"$set": update_dict})
        updated = await db.webhook_config.find_one({}, {"_id": 0})
        return JSONResponse(content=updated)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating webhook config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/webhook/github")
async def github_webhook(request: Request):
    """Handle GitHub webhook events for auto-scanning PRs"""
    try:
        config = await db.webhook_config.find_one({}, {"_id": 0})
        if not config or not config.get("enabled"):
            return JSONResponse(content={"message": "Webhook disabled"}, status_code=200)

        body = await request.body()
        event_type = request.headers.get("X-GitHub-Event", "")

        sig = request.headers.get("X-Hub-Signature-256", "")
        if sig and config.get("webhook_secret"):
            expected = "sha256=" + hmac.new(
                config["webhook_secret"].encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(sig, expected):
                raise HTTPException(status_code=403, detail="Invalid signature")

        payload = json.loads(body)

        if event_type == "pull_request" and payload.get("action") in ["opened", "synchronize", "reopened"]:
            pr = payload["pull_request"]
            repo = payload["repository"]["full_name"]
            pr_number = pr["number"]

            logging.info(f"Webhook: Auto-scanning PR {repo}#{pr_number}")

            pr_data = await github_service.get_pr_files(repo, pr_number)
            if pr_data:
                temp_dir = tempfile.mkdtemp()
                file_paths = []

                for file_info in pr_data['files']:
                    if file_info.get('content'):
                        file_path = Path(temp_dir) / file_info['filename']
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_text(file_info['content'])
                        file_paths.append(str(file_path))

                custom_rules = await _get_enabled_custom_rules()
                scan_result = await code_scanner.scan_files(file_paths, custom_rules=custom_rules)

                if config.get("enable_ai") and scan_result['issues']:
                    for issue in scan_result['issues']:
                        suggestion = await ai_service.get_suggestion(issue)
                        issue['ai_suggestion'] = suggestion

                scan_id = str(uuid.uuid4())
                scan_history = {
                    'scan_id': scan_id,
                    'type': 'webhook',
                    'repo': repo,
                    'pr_number': pr_number,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'files_scanned': len(file_paths),
                    'issues_found': len(scan_result['issues']),
                    'summary': scan_result['summary'],
                    'issues': scan_result['issues']
                }
                await db.scan_history.insert_one(scan_history)
                shutil.rmtree(temp_dir)

                return JSONResponse(content={"scan_id": scan_id, "issues_found": len(scan_result['issues'])})

        return JSONResponse(content={"message": f"Event '{event_type}' received"})

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/webhook/github-actions-yaml")
async def get_github_actions_yaml():
    """Generate GitHub Actions YAML for CI/CD integration"""
    try:
        config = await db.webhook_config.find_one({}, {"_id": 0})
        if not config:
            config = (await get_webhook_config()).body
            config = json.loads(config)

        yaml_content = f"""name: CodeQuality Gate Scan

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  quality-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Trigger CodeQuality Gate Scan
        env:
          WEBHOOK_URL: {config.get('webhook_url', 'YOUR_WEBHOOK_URL')}
          WEBHOOK_SECRET: ${{{{ secrets.QUALITYGATE_WEBHOOK_SECRET }}}}
        run: |
          # Send webhook to CodeQuality Gate
          PAYLOAD='{{"action":"opened","pull_request":{{"number":'${{{{ github.event.pull_request.number }}}}'}}, "repository":{{"full_name":"'${{{{ github.repository }}}}'"}} }}'

          SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | sed 's/SHA2-256(stdin)= //')

          curl -X POST "$WEBHOOK_URL" \\
            -H "Content-Type: application/json" \\
            -H "X-GitHub-Event: pull_request" \\
            -H "X-Hub-Signature-256: sha256=$SIGNATURE" \\
            -d "$PAYLOAD"

      - name: Wait for scan results
        run: sleep 30

      - name: Check scan results
        run: |
          echo "Scan triggered successfully. Check results at:"
          echo "https://quality-gate-15.preview.emergentagent.com/history"
"""
        return JSONResponse(content={"yaml": yaml_content})
    except Exception as e:
        logging.error(f"Error generating YAML: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# ANALYTICS ENDPOINTS
# ═══════════════════════════════════════════

@api_router.get("/analytics/trends")
async def get_analytics_trends():
    """Get code quality trends over time"""
    try:
        history = await db.scan_history.find({}, {"_id": 0}).sort("timestamp", 1).to_list(500)

        trends = []
        severity_totals = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        issue_type_counts = {}
        total_issues = 0
        total_files = 0

        for scan in history:
            summary = scan.get("summary", {})
            ts = scan.get("timestamp", "")

            trends.append({
                "date": ts[:10] if ts else "",
                "timestamp": ts,
                "scan_id": scan.get("scan_id"),
                "type": scan.get("type", "unknown"),
                "total_issues": summary.get("total_issues", 0),
                "critical": summary.get("critical", 0),
                "high": summary.get("high", 0),
                "medium": summary.get("medium", 0),
                "low": summary.get("low", 0),
                "files_scanned": summary.get("total_files", 0),
            })

            severity_totals["critical"] += summary.get("critical", 0)
            severity_totals["high"] += summary.get("high", 0)
            severity_totals["medium"] += summary.get("medium", 0)
            severity_totals["low"] += summary.get("low", 0)
            total_issues += summary.get("total_issues", 0)
            total_files += summary.get("total_files", 0)

            for issue in scan.get("issues", []):
                itype = issue.get("type", "unknown")
                issue_type_counts[itype] = issue_type_counts.get(itype, 0) + 1

        top_issues = sorted(issue_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_issues_list = [{"type": t, "count": c} for t, c in top_issues]

        severity_distribution = [
            {"name": "Critical", "value": severity_totals["critical"], "color": "#FF2B2B"},
            {"name": "High", "value": severity_totals["high"], "color": "#FFD500"},
            {"name": "Medium", "value": severity_totals["medium"], "color": "#002FA7"},
            {"name": "Low", "value": severity_totals["low"], "color": "#00C853"},
        ]

        return JSONResponse(content={
            "trends": trends,
            "severity_distribution": severity_distribution,
            "top_issues": top_issues_list,
            "totals": {
                "total_scans": len(history),
                "total_issues": total_issues,
                "total_files": total_files,
                **severity_totals,
            }
        })
    except Exception as e:
        logging.error(f"Error fetching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════

def generate_html_report(scan):
    """Generate HTML report from scan data"""
    issues_by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
    for issue in scan['issues']:
        severity = issue.get('severity', 'low')
        issues_by_severity[severity].append(issue)

    html = f"""<!DOCTYPE html>
<html><head><title>Code Quality Report - {scan['scan_id']}</title>
<style>
body {{ font-family: 'IBM Plex Sans', sans-serif; margin: 40px; background: #F1F3F5; }}
.header {{ background: #002FA7; color: white; padding: 20px; margin-bottom: 30px; }}
.summary {{ background: white; padding: 20px; margin-bottom: 20px; border: 1px solid #E4E4E7; }}
.issue {{ background: white; padding: 15px; margin-bottom: 10px; border-left: 4px solid; }}
.critical {{ border-color: #FF2B2B; }} .high {{ border-color: #FFD500; }}
.medium {{ border-color: #002FA7; }} .low {{ border-color: #00C853; }}
.code {{ background: #F1F3F5; padding: 10px; font-family: monospace; margin-top: 10px; }}
</style></head><body>
<div class="header"><h1>Code Quality Scan Report</h1>
<p>Scan ID: {scan['scan_id']}</p><p>Date: {scan['timestamp']}</p></div>
<div class="summary"><h2>Summary</h2>
<p>Files Scanned: {scan['files_scanned']}</p><p>Total Issues: {scan['issues_found']}</p>
<p>Critical: {len(issues_by_severity['critical'])} | High: {len(issues_by_severity['high'])} | Medium: {len(issues_by_severity['medium'])} | Low: {len(issues_by_severity['low'])}</p></div>
<h2>Issues</h2>"""

    for severity in ['critical', 'high', 'medium', 'low']:
        for issue in issues_by_severity[severity]:
            ai_html = f'<div class="code"><strong>AI Suggestion:</strong><br>{issue.get("ai_suggestion", "N/A")}</div>' if issue.get('ai_suggestion') else ''
            html += f"""<div class="issue {severity}">
<h3>{issue['type']} - {severity.upper()}</h3>
<p><strong>File:</strong> {issue['file']} | <strong>Line:</strong> {issue['line']}</p>
<p>{issue['message']}</p>{ai_html}</div>"""

    html += "</body></html>"
    return html


# ═══════════════════════════════════════════
# APP SETUP
# ═══════════════════════════════════════════

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
