# CodeQuality Gate CLI

A powerful command-line tool for automated code quality scanning with AI-powered fix suggestions.

## Installation

```bash
cd /app/backend/cli
bash install.sh
```

## Usage

### Scan Local Files

Scan a single file:
```bash
quality-gate scan app.js
```

Scan multiple files:
```bash
quality-gate scan app.js utils.js
```

Scan an entire directory:
```bash
quality-gate scan ./src
```

Disable AI suggestions:
```bash
quality-gate scan ./src --no-ai
```

### Scan GitHub PRs

Scan a specific PR:
```bash
quality-gate scan-pr facebook/react 12345
```

**Note:** Requires GITHUB_TOKEN environment variable to be set.

## Features

- **Multi-language Support**: JavaScript, TypeScript, Python
- **Comprehensive Checks**:
  - Console statements and debugger
  - Unused imports
  - Var declarations (use let/const)
  - Exposed secrets and API keys
  - Security issues (eval usage)
  - TypeScript specific (any type, non-null assertions)
  - Python specific (print statements, bare except, mutable defaults)
- **AI-Powered Suggestions**: Get intelligent fix recommendations using GPT-5.2
- **GitHub Integration**: Scan pull requests directly
- **Beautiful CLI Output**: Color-coded severity levels and formatted tables

## Supported File Types

- JavaScript (.js)
- JSX (.jsx)
- TypeScript (.ts)
- TSX (.tsx)
- Python (.py)

## Severity Levels

- 🔴 **Critical**: Security vulnerabilities, exposed secrets
- 🟠 **High**: Major issues, bare exceptions, debugger statements
- 🟡 **Medium**: Code quality issues, var declarations, any types
- 🟢 **Low**: Minor issues, console logs, print statements

## Environment Variables

- `EMERGENT_LLM_KEY`: Required for AI-powered suggestions (already configured)
- `GITHUB_TOKEN`: Required for scanning GitHub PRs (optional)

## Examples Output

```
╭────────── Scan Summary ──────────╮
│                                  │
│ Total Files: 5                   │
│ Total Issues: 12                 │
│                                  │
│ 🔴 Critical: 2                   │
│ 🟠 High: 3                       │
│ 🟡 Medium: 4                     │
│ 🟢 Low: 3                        │
│                                  │
╰──────────────────────────────────╯
```

## License

MIT