from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Form
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

from services.code_scanner import CodeScanner
from services.ai_suggestions import AISuggestionService
from services.github_service import GitHubService
from models.schemas import (
    ScanRequest, ScanResult, GitHubPRRequest,
    ScanHistory, Issue, CustomRule
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="CodeQuality Gate", version="1.0.0")
api_router = APIRouter(prefix="/api")

code_scanner = CodeScanner()
ai_service = AISuggestionService()
github_service = GitHubService()

@api_router.get("/")
async def root():
    return {"message": "CodeQuality Gate API is running"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

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
        
        scan_result = await code_scanner.scan_files(file_paths)
        
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
        
        scan_result = await code_scanner.scan_files(file_paths)
        
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
            return FileResponse(
                temp_file.name,
                media_type='application/json',
                filename=f"scan_{scan_id}.json"
            )
        elif format == "html":
            html_content = generate_html_report(scan)
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html')
            temp_file.write(html_content)
            temp_file.close()
            return FileResponse(
                temp_file.name,
                media_type='text/html',
                filename=f"scan_{scan_id}.html"
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'html'")
            
    except Exception as e:
        logging.error(f"Error downloading report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_html_report(scan):
    """Generate HTML report from scan data"""
    issues_by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
    for issue in scan['issues']:
        severity = issue.get('severity', 'low')
        issues_by_severity[severity].append(issue)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Code Quality Report - {scan['scan_id']}</title>
        <style>
            body {{ font-family: 'IBM Plex Sans', sans-serif; margin: 40px; background: #F1F3F5; }}
            .header {{ background: #002FA7; color: white; padding: 20px; margin-bottom: 30px; }}
            .summary {{ background: white; padding: 20px; margin-bottom: 20px; border: 1px solid #E4E4E7; }}
            .issue {{ background: white; padding: 15px; margin-bottom: 10px; border-left: 4px solid; }}
            .critical {{ border-color: #FF2B2B; }}
            .high {{ border-color: #FFD500; }}
            .medium {{ border-color: #002FA7; }}
            .low {{ border-color: #00C853; }}
            .code {{ background: #F1F3F5; padding: 10px; font-family: 'IBM Plex Mono', monospace; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Code Quality Scan Report</h1>
            <p>Scan ID: {scan['scan_id']}</p>
            <p>Date: {scan['timestamp']}</p>
        </div>
        <div class="summary">
            <h2>Summary</h2>
            <p>Files Scanned: {scan['files_scanned']}</p>
            <p>Total Issues: {scan['issues_found']}</p>
            <p>Critical: {len(issues_by_severity['critical'])}</p>
            <p>High: {len(issues_by_severity['high'])}</p>
            <p>Medium: {len(issues_by_severity['medium'])}</p>
            <p>Low: {len(issues_by_severity['low'])}</p>
        </div>
        <h2>Issues</h2>
    """
    
    for severity in ['critical', 'high', 'medium', 'low']:
        for issue in issues_by_severity[severity]:
            html += f"""
        <div class="issue {severity}">
            <h3>{issue['type']} - {severity.upper()}</h3>
            <p><strong>File:</strong> {issue['file']}</p>
            <p><strong>Line:</strong> {issue['line']}</p>
            <p><strong>Message:</strong> {issue['message']}</p>
            {f'<div class="code"><strong>AI Suggestion:</strong><br>{issue.get("ai_suggestion", "N/A")}</div>' if issue.get('ai_suggestion') else ''}
        </div>
            """
    
    html += "</body></html>"
    return html

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