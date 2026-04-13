# CodeQuality Gate 🛡️

A comprehensive code quality scanning tool designed for engineering managers and development teams. Automatically scan code for quality issues, security vulnerabilities, and get AI-powered fix suggestions.

## 🌟 Features

### Web Dashboard
- **File Upload Scanning**: Upload individual files or entire folders for analysis
- **GitHub PR Integration**: Scan pull requests directly from GitHub
- **AI-Powered Suggestions**: Get intelligent fix recommendations using GPT-5.2
- **Interactive Results**: Filter and search through issues with severity-based categorization
- **Downloadable Reports**: Export results as JSON or HTML
- **Scan History**: Track all previous scans with detailed summaries

### CLI Tool
- **Command-line scanning** for local files and directories
- **GitHub PR scanning** from the terminal
- **Beautiful output** with color-coded severity levels
- **Fast and efficient** batch processing

### Comprehensive Code Checks

#### JavaScript/TypeScript
- ✅ Console statements (console.log, console.debug, etc.)
- ✅ Debugger statements
- ✅ Unused imports
- ✅ Var declarations (should use let/const)
- ✅ TypeScript 'any' type usage
- ✅ Non-null assertion operators
- ✅ Eval() usage

#### Python
- ✅ Print statements
- ✅ Bare except clauses
- ✅ Mutable default arguments

#### Security
- ✅ Exposed API keys and secrets
- ✅ Hardcoded passwords and tokens
- ✅ GitHub tokens in code
- ✅ OpenAI API keys exposure

## 🚀 Quick Start

### Web Application

1. **Access the dashboard**:
   ```
   https://quality-gate-15.preview.emergentagent.com
   ```

2. **Upload files** or **enter GitHub PR details** (owner/repo and PR number)

3. **Enable AI suggestions** (optional) for intelligent fix recommendations

4. **View results** with detailed issue breakdown and severity levels

5. **Download reports** in JSON or HTML format

### CLI Tool

#### Installation

```bash
cd /app/backend/cli
bash install.sh
```

#### Usage

**Scan local files:**
```bash
quality-gate scan ./src
quality-gate scan app.js utils.js
```

**Scan GitHub PR:**
```bash
quality-gate scan-pr facebook/react 12345
```

**Disable AI suggestions:**
```bash
quality-gate scan ./src --no-ai
```

## 📊 Severity Levels

| Level | Icon | Description | Examples |
|-------|------|-------------|----------|
| **Critical** | 🔴 | Security vulnerabilities, exposed secrets | API keys in code, eval() usage |
| **High** | 🟠 | Major code quality issues | Debugger statements, bare except |
| **Medium** | 🔵 | Code quality improvements | Var declarations, any types |
| **Low** | 🟢 | Minor issues | Console logs, print statements |

## 🔧 Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **MongoDB**: Document database for scan history
- **PyGithub**: GitHub API integration
- **Emergent LLM**: AI-powered suggestions using GPT-5.2

### Frontend
- **React**: Modern UI library
- **Axios**: HTTP client for API requests
- **Phosphor Icons**: Beautiful icon library
- **Recharts**: Data visualization

### CLI
- **Python**: Core scripting language
- **Rich**: Beautiful terminal output
- **AsyncIO**: Asynchronous operations

## 🔐 Environment Variables

### Backend (.env)
```bash
EMERGENT_LLM_KEY=sk-emergent-eF7A300E36b789f712  # Pre-configured
GITHUB_TOKEN=                                      # Optional: Add for GitHub PR scanning
```

## 📖 API Endpoints

- `POST /api/scan/upload` - Scan uploaded files
- `POST /api/scan/github-pr` - Scan GitHub PR
- `GET /api/scan/{scan_id}` - Get scan results
- `GET /api/scan/history` - Get scan history
- `GET /api/scan/{scan_id}/download` - Download report

## 🎨 Design

Swiss Brutalist aesthetic with high contrast, IBM Plex fonts, and technical focus.

---

**Built for engineering managers and development teams**
