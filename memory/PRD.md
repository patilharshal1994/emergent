# CodeQuality Gate - PRD

## Original Problem Statement
Engineering manager needs a tool to automate code review tasks: checking for syntax issues, security vulnerabilities, code quality problems, TypeScript errors, unused imports, exposed secrets, and more. Tool should accept files/folders/GitHub PRs and produce reports with line numbers and AI fix suggestions.

## Architecture
- **Backend**: FastAPI (Python) on port 8001 with /api prefix
- **Frontend**: React on port 3000
- **Database**: MongoDB (scan history, results)
- **AI**: GPT-5.2 via Emergent LLM key for fix suggestions
- **GitHub**: PyGithub for PR integration

## User Personas
- Engineering Managers reviewing PRs
- Developers scanning code before committing
- Teams enforcing coding standards

## Core Requirements (Static)
- Multi-language code scanning (JS/TS/Python)
- Security vulnerability detection (exposed secrets)
- AI-powered fix suggestions
- GitHub PR integration
- Interactive web dashboard with filtering
- Downloadable reports (JSON/HTML)
- CLI tool for terminal usage
- Scan history tracking

## What's Been Implemented (April 2026)
- [x] Full backend API (scan/upload, scan/github-pr, history, download)
- [x] Code scanner engine (15+ rule types across JS/TS/Python)
- [x] AI suggestion service (GPT-5.2 via Emergent LLM)
- [x] GitHub PR integration (PyGithub)
- [x] Web dashboard (3 tabs: Upload/Folder, Paste Code, GitHub PR)
- [x] Scan results page (severity filter, search, issue cards with AI suggestions)
- [x] Scan history page
- [x] Report download (JSON/HTML)
- [x] CLI tool with Rich output
- [x] Live dashboard stats
- [x] Swiss Brutalist design (IBM Plex Sans, high contrast)

## Prioritized Backlog
### P0 (Done)
- File/folder upload scanning
- Code quality checks (console, debugger, var, secrets, eval)
- AI fix suggestions
- Web dashboard + results + history

### P1 (Next)
- Custom rule configuration UI
- CI/CD pipeline integration (GitHub Actions, GitLab CI)
- Slack/Teams notifications on scan completion
- Code quality trends and analytics charts

### P2 (Future)
- Multi-repository dashboard
- Team collaboration (shared rules, comments)
- Webhook support for auto-scanning on push
- IDE extension (VS Code)
- ESLint/Prettier deep integration

## Next Tasks
1. Add custom rule configuration page
2. Add CI/CD integration support
3. Add code quality trend analytics
4. Add more language support (Java, Go, Ruby)
