#!/usr/bin/env python3
"""
CodeQuality Gate CLI Tool

A command-line interface for scanning code quality issues with AI-powered suggestions.

Usage:
    quality-gate scan <path>                    # Scan files or directory
    quality-gate scan-pr <repo> <pr_number>     # Scan GitHub PR
    quality-gate history                         # View scan history
    quality-gate report <scan_id>               # View specific scan report

Examples:
    quality-gate scan ./src
    quality-gate scan ./app.js ./utils.js
    quality-gate scan-pr facebook/react 12345
    quality-gate history
    quality-gate report abc-123-def
"""

import sys
import os
import argparse
import json
import asyncio
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.code_scanner import CodeScanner
from services.ai_suggestions import AISuggestionService
from services.github_service import GitHubService

console = Console()

def print_banner():
    banner = """
 ██████  ██    ██  █████  ██      ██ ████████ ██    ██  ██████   █████  ████████ ███████ 
██    ██ ██    ██ ██   ██ ██      ██    ██     ██  ██  ██       ██   ██    ██    ██      
██    ██ ██    ██ ███████ ██      ██    ██      ████   ██   ███ ███████    ██    █████   
██ ▄▄ ██ ██    ██ ██   ██ ██      ██    ██       ██    ██    ██ ██   ██    ██    ██      
 ██████   ██████  ██   ██ ███████ ██    ██       ██     ██████  ██   ██    ██    ███████ 
    ▀▀                                                                                     
    """
    console.print(banner, style="bold blue")
    console.print("Code Quality Scanner with AI-Powered Suggestions\n", style="italic")

async def scan_files(paths, enable_ai=True):
    """Scan files for code quality issues"""
    scanner = CodeScanner()
    ai_service = AISuggestionService() if enable_ai else None
    
    file_paths = []
    for path in paths:
        p = Path(path)
        if p.is_file():
            file_paths.append(str(p))
        elif p.is_dir():
            for ext in ['.js', '.jsx', '.ts', '.tsx', '.py']:
                file_paths.extend([str(f) for f in p.rglob(f'*{ext}')])
    
    if not file_paths:
        console.print("[red]No valid files found to scan[/red]")
        return
    
    console.print(f"\n[cyan]Scanning {len(file_paths)} files...[/cyan]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing code...", total=None)
        result = await scanner.scan_files(file_paths)
        progress.update(task, completed=True)
    
    display_results(result, ai_service)

async def scan_github_pr(repo, pr_number, enable_ai=True):
    """Scan a GitHub PR"""
    github_service = GitHubService()
    scanner = CodeScanner()
    ai_service = AISuggestionService() if enable_ai else None
    
    console.print(f"\n[cyan]Fetching PR {repo}#{pr_number}...[/cyan]\n")
    
    pr_data = await github_service.get_pr_files(repo, pr_number)
    
    if not pr_data:
        console.print("[red]Error: PR not found or GitHub token not configured[/red]")
        console.print("[yellow]Set GITHUB_TOKEN environment variable to scan PRs[/yellow]")
        return
    
    console.print(f"[green]PR: {pr_data['pr_info']['title']}[/green]")
    console.print(f"[green]Author: {pr_data['pr_info']['author']}[/green]\n")
    
    import tempfile
    temp_dir = tempfile.mkdtemp()
    file_paths = []
    
    for file_info in pr_data['files']:
        if file_info.get('content'):
            file_path = Path(temp_dir) / file_info['filename']
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file_info['content'])
            file_paths.append(str(file_path))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing code...", total=None)
        result = await scanner.scan_files(file_paths)
        progress.update(task, completed=True)
    
    import shutil
    shutil.rmtree(temp_dir)
    
    display_results(result, ai_service)

def display_results(result, ai_service=None):
    """Display scan results in a formatted table"""
    summary = result['summary']
    issues = result['issues']
    
    summary_panel = Panel(
        f"""
Total Files: [bold]{summary['total_files']}[/bold]
Total Issues: [bold]{summary['total_issues']}[/bold]

🔴 Critical: [red bold]{summary['critical']}[/red bold]
🟠 High: [yellow bold]{summary['high']}[/yellow bold]
🟡 Medium: [blue bold]{summary['medium']}[/blue bold]
🟢 Low: [green bold]{summary['low']}[/green bold]
        """,
        title="[bold]Scan Summary[/bold]",
        border_style="blue"
    )
    console.print(summary_panel)
    
    if not issues:
        console.print("\n[green]✓ No issues found! Code looks good.[/green]\n")
        return
    
    console.print("\n[bold]Issues Found:[/bold]\n")
    
    severity_colors = {
        'critical': 'red',
        'high': 'yellow',
        'medium': 'blue',
        'low': 'green'
    }
    
    for i, issue in enumerate(issues, 1):
        color = severity_colors.get(issue['severity'], 'white')
        
        console.print(f"\n[bold {color}]Issue #{i}: {issue['type'].upper().replace('_', ' ')}[/bold {color}]")
        console.print(f"  [dim]Severity:[/dim] [{color}]{issue['severity'].upper()}[/{color}]")
        console.print(f"  [dim]File:[/dim] {issue['file']}")
        console.print(f"  [dim]Line:[/dim] {issue['line']}")
        console.print(f"  [dim]Message:[/dim] {issue['message']}")
        
        if issue.get('rule_id'):
            console.print(f"  [dim]Rule:[/dim] {issue['rule_id']}")
    
    console.print("\n")

def main():
    parser = argparse.ArgumentParser(
        description="CodeQuality Gate - Automated code quality scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    scan_parser = subparsers.add_parser('scan', help='Scan files or directory')
    scan_parser.add_argument('paths', nargs='+', help='Files or directories to scan')
    scan_parser.add_argument('--no-ai', action='store_true', help='Disable AI suggestions')
    
    pr_parser = subparsers.add_parser('scan-pr', help='Scan GitHub PR')
    pr_parser.add_argument('repo', help='Repository (owner/repo)')
    pr_parser.add_argument('pr_number', type=int, help='PR number')
    pr_parser.add_argument('--no-ai', action='store_true', help='Disable AI suggestions')
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.command == 'scan':
        asyncio.run(scan_files(args.paths, enable_ai=not args.no_ai))
    elif args.command == 'scan-pr':
        asyncio.run(scan_github_pr(args.repo, args.pr_number, enable_ai=not args.no_ai))
    else:
        parser.print_help()

if __name__ == '__main__':
    main()