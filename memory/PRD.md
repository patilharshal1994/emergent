# CodeQuality Gate - PRD

## Original Problem Statement
Engineering manager needs a tool to automate code review tasks: checking for syntax issues, security vulnerabilities, code quality problems, TypeScript errors, unused imports, exposed secrets, and more. Tool should accept files/folders/GitHub PRs and produce reports with line numbers and AI fix suggestions.

## Architecture
- **Backend**: FastAPI (Python) on port 8001 with /api prefix
- **Frontend**: React on port 3000
- **Database**: MongoDB (scan history, rules, webhook config)
- **AI**: GPT-5.2 via Emergent LLM key
- **GitHub**: PyGithub for PR integration

## What's Been Implemented

### Phase 1 (April 12, 2026)
- [x] File/folder upload scanning
- [x] Paste code scanning
- [x] GitHub PR scanning
- [x] 15+ scanning rules (JS/TS/Python)
- [x] AI-powered fix suggestions (GPT-5.2)
- [x] Interactive results dashboard with filtering
- [x] Downloadable reports (JSON/HTML)
- [x] Scan history tracking
- [x] CLI tool

### Phase 2 (April 13, 2026)
- [x] CI/CD Integration: GitHub Actions webhook endpoint, auto-scan on PR creation, webhook config management, YAML generator
- [x] Custom Rule Configuration: CRUD endpoints, toggle rules on/off, change severity levels, create custom regex pattern rules, category grouping
- [x] Analytics Dashboard: Issues over time (line chart), severity distribution (donut chart), most common issues (bar chart), aggregate stats

## Backlog
### P1 (Next)
- Slack/Teams notifications on scan completion
- ESLint deep integration for JS/TS
- Rule import/export

### P2 (Future)
- Multi-repo dashboard
- Team collaboration
- IDE extension (VS Code)
- More languages (Java, Go, Ruby)
