import os
import re
import subprocess
import json
import tempfile
from typing import List, Dict
from pathlib import Path


class CodeScanner:
    """Comprehensive code scanner for multiple file types with ESLint integration"""

    def __init__(self):
        self.scanners = {
            '.js': self.scan_javascript,
            '.jsx': self.scan_javascript,
            '.ts': self.scan_typescript,
            '.tsx': self.scan_typescript,
            '.py': self.scan_python,
        }
        self.eslint_available = self._check_eslint()

    def _check_eslint(self) -> bool:
        """Check if ESLint is available"""
        try:
            result = subprocess.run(['eslint', '--version'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    async def scan_files(self, file_paths: List[str], custom_rules: List[Dict] = None) -> Dict:
        """Scan multiple files and aggregate results"""
        all_issues = []
        files_scanned = 0

        js_ts_files = []
        for file_path in file_paths:
            path = Path(file_path)
            if path.suffix in self.scanners:
                issues = await self.scanners[path.suffix](file_path)
                all_issues.extend(issues)
                files_scanned += 1

            if path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                js_ts_files.append(file_path)

            if custom_rules:
                custom_issues = self._apply_custom_rules(file_path, custom_rules)
                all_issues.extend(custom_issues)

        # Run ESLint on all JS/TS files in batch
        if self.eslint_available and js_ts_files:
            eslint_issues = self._run_eslint(js_ts_files)
            all_issues.extend(eslint_issues)

        # Deduplicate issues (same file+line+rule_id)
        all_issues = self._deduplicate_issues(all_issues)

        summary = self._generate_summary(all_issues, files_scanned)

        return {
            'summary': summary,
            'issues': all_issues
        }

    def _deduplicate_issues(self, issues: List[Dict]) -> List[Dict]:
        """Remove duplicate issues (same file, line, rule_id)"""
        seen = set()
        unique = []
        for issue in issues:
            key = (issue.get('file', ''), issue.get('line', 0), issue.get('rule_id', ''))
            if key not in seen:
                seen.add(key)
                unique.append(issue)
        return unique

    def _run_eslint(self, file_paths: List[str]) -> List[Dict]:
        """Run ESLint on JS/TS files and return structured issues"""
        issues = []

        # Create a minimal flat config file for ESLint
        eslint_config = """\
export default [
  {
    rules: {
      "no-unused-vars": "warn",
      "no-undef": "error",
      "no-const-assign": "error",
      "no-dupe-keys": "error",
      "no-duplicate-case": "error",
      "no-empty": "warn",
      "no-ex-assign": "error",
      "no-extra-boolean-cast": "warn",
      "no-func-assign": "error",
      "no-irregular-whitespace": "warn",
      "no-unreachable": "error",
      "no-unsafe-negation": "error",
      "use-isnan": "error",
      "valid-typeof": "error",
      "eqeqeq": "warn",
      "no-caller": "error",
      "no-extend-native": "error",
      "no-extra-bind": "warn",
      "no-implied-eval": "error",
      "no-iterator": "error",
      "no-lone-blocks": "warn",
      "no-loop-func": "warn",
      "no-multi-str": "warn",
      "no-new-wrappers": "error",
      "no-proto": "error",
      "no-redeclare": "error",
      "no-return-assign": "warn",
      "no-self-compare": "error",
      "no-sequences": "warn",
      "no-throw-literal": "error",
      "no-with": "error",
      "no-shadow-restricted-names": "error",
      "no-delete-var": "error",
      "no-label-var": "error",
    },
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: { jsx: true }
      }
    }
  }
];
"""
        try:
            # Create a temp directory for the config
            temp_config_dir = tempfile.mkdtemp()
            config_path = Path(temp_config_dir) / 'eslint.config.mjs'
            config_path.write_text(eslint_config)

            # Copy files to temp config dir so they're within the base path
            local_paths = []
            for fp in file_paths:
                dest = Path(temp_config_dir) / Path(fp).name
                import shutil
                shutil.copy2(fp, dest)
                local_paths.append(str(dest))

            # Run ESLint with JSON formatter
            cmd = [
                'eslint',
                '--no-config-lookup',
                '--config', str(config_path),
                '--format', 'json',
            ] + local_paths

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=temp_config_dir,
            )

            output = result.stdout.strip()
            if output:
                eslint_results = json.loads(output)
                for file_result in eslint_results:
                    file_path = file_result.get('filePath', '')
                    file_name = Path(file_path).name

                    for msg in file_result.get('messages', []):
                        if msg.get('message', '').startswith('File ignored'):
                            continue
                        severity_num = msg.get('severity', 1)
                        eslint_rule = msg.get('ruleId', 'parse-error')
                        if eslint_rule is None:
                            eslint_rule = 'parse-error'
                        severity = self._map_eslint_severity(severity_num, eslint_rule)

                        issues.append({
                            'type': f'eslint:{eslint_rule}',
                            'severity': severity,
                            'file': file_name,
                            'line': msg.get('line', 0),
                            'column': msg.get('column', 0),
                            'message': msg.get('message', 'ESLint issue'),
                            'rule_id': f'eslint/{eslint_rule}',
                        })

            # Cleanup
            import shutil as shutil_cleanup
            shutil_cleanup.rmtree(temp_config_dir)

        except subprocess.TimeoutExpired:
            pass
        except json.JSONDecodeError:
            pass
        except Exception as e:
            pass

        return issues

    def _map_eslint_severity(self, severity_num: int, rule_id: str) -> str:
        """Map ESLint severity to our severity levels"""
        critical_rules = ['no-undef', 'no-const-assign', 'no-func-assign', 'no-implied-eval', 'use-isnan']
        high_rules = ['no-unreachable', 'no-dupe-keys', 'no-duplicate-case', 'valid-typeof',
                       'no-unsafe-negation', 'no-redeclare', 'no-throw-literal', 'no-self-compare']

        if rule_id in critical_rules:
            return 'critical'
        if rule_id in high_rules:
            return 'high'
        if severity_num == 2:
            return 'high'
        return 'medium'

    def _apply_custom_rules(self, file_path: str, custom_rules: List[Dict]) -> List[Dict]:
        """Apply user-defined custom pattern rules"""
        issues = []
        path = Path(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.read().split('\n')

            for rule in custom_rules:
                pattern = rule.get('pattern')
                file_types = rule.get('file_types', [])

                if file_types and path.suffix not in file_types:
                    continue

                if not pattern:
                    continue

                try:
                    compiled = re.compile(pattern)
                    for i, line in enumerate(lines, 1):
                        if compiled.search(line):
                            issues.append({
                                'type': rule.get('name', 'custom_rule'),
                                'severity': rule.get('severity', 'medium'),
                                'file': path.name,
                                'line': i,
                                'message': rule.get('description', 'Custom rule violation'),
                                'rule_id': rule.get('rule_id', 'custom')
                            })
                except re.error:
                    pass
        except Exception:
            pass

        return issues

    def _generate_summary(self, issues: List[Dict], files_scanned: int) -> Dict:
        """Generate summary statistics"""
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}

        for issue in issues:
            severity = issue.get('severity', 'low')
            if severity in severity_counts:
                severity_counts[severity] += 1

        return {
            'total_files': files_scanned,
            'total_issues': len(issues),
            **severity_counts
        }

    async def scan_javascript(self, file_path: str) -> List[Dict]:
        """Scan JavaScript/JSX files with pattern-based checks"""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            issues.extend(self._check_console_logs(file_path, lines))
            issues.extend(self._check_debugger_statements(file_path, lines))
            issues.extend(self._check_unused_imports(file_path, lines))
            issues.extend(self._check_var_declarations(file_path, lines))
            issues.extend(self._check_exposed_secrets(file_path, lines))
            issues.extend(self._check_eval_usage(file_path, lines))

        except Exception:
            pass

        return issues

    async def scan_typescript(self, file_path: str) -> List[Dict]:
        """Scan TypeScript/TSX files"""
        issues = await self.scan_javascript(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            issues.extend(self._check_any_type(file_path, lines))
            issues.extend(self._check_non_null_assertion(file_path, lines))

        except Exception:
            pass

        return issues

    async def scan_python(self, file_path: str) -> List[Dict]:
        """Scan Python files"""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            issues.extend(self._check_print_statements(file_path, lines))
            issues.extend(self._check_exposed_secrets(file_path, lines))
            issues.extend(self._check_bare_except(file_path, lines))
            issues.extend(self._check_mutable_defaults(file_path, lines))

        except Exception:
            pass

        return issues

    def _check_console_logs(self, file_path: str, lines: List[str]) -> List[Dict]:
        issues = []
        console_pattern = re.compile(r'console\.(log|debug|info|warn|error)')
        for i, line in enumerate(lines, 1):
            if console_pattern.search(line) and not line.strip().startswith('//'):
                issues.append({'type': 'console_statement', 'severity': 'low', 'file': Path(file_path).name, 'line': i, 'message': 'Console statement found. Remove before production.', 'rule_id': 'no-console'})
        return issues

    def _check_debugger_statements(self, file_path: str, lines: List[str]) -> List[Dict]:
        issues = []
        for i, line in enumerate(lines, 1):
            if 'debugger' in line and not line.strip().startswith('//'):
                issues.append({'type': 'debugger_statement', 'severity': 'high', 'file': Path(file_path).name, 'line': i, 'message': 'Debugger statement found. Remove before committing.', 'rule_id': 'no-debugger'})
        return issues

    def _check_unused_imports(self, file_path: str, lines: List[str]) -> List[Dict]:
        issues = []
        imports = []
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('import '):
                match = re.search(r'import\s+(?:{([^}]+)}|([^\s]+))', line)
                if match:
                    imported = match.group(1) or match.group(2)
                    if imported:
                        imports.append((i, imported.strip()))
        content = '\n'.join(lines)
        for line_num, imported_name in imports:
            names = [n.strip() for n in imported_name.split(',')]
            for name in names:
                clean_name = name.split(' as ')[0].strip()
                if clean_name and content.count(clean_name) == 1:
                    issues.append({'type': 'unused_import', 'severity': 'low', 'file': Path(file_path).name, 'line': line_num, 'message': f'Potentially unused import: {clean_name}', 'rule_id': 'no-unused-imports'})
        return issues

    def _check_var_declarations(self, file_path: str, lines: List[str]) -> List[Dict]:
        issues = []
        for i, line in enumerate(lines, 1):
            if re.match(r'^\s*var\s+', line) and not line.strip().startswith('//'):
                issues.append({'type': 'var_declaration', 'severity': 'medium', 'file': Path(file_path).name, 'line': i, 'message': 'Use let or const instead of var for better scoping.', 'rule_id': 'no-var'})
        return issues

    def _check_exposed_secrets(self, file_path: str, lines: List[str]) -> List[Dict]:
        issues = []
        secret_patterns = [
            (r'["\']?api[_-]?key["\']?\s*[:=]\s*["\'][\w-]{20,}["\']', 'API key'),
            (r'["\']?secret[_-]?key["\']?\s*[:=]\s*["\'][\w-]{20,}["\']', 'Secret key'),
            (r'["\']?password["\']?\s*[:=]\s*["\'][^"\'\\n]{6,}["\']', 'Password'),
            (r'["\']?token["\']?\s*[:=]\s*["\'][\w-]{20,}["\']', 'Token'),
            (r'sk-[a-zA-Z0-9]{32,}', 'OpenAI API key'),
            (r'ghp_[a-zA-Z0-9]{36}', 'GitHub token'),
        ]
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('#') or line.strip().startswith('//'):
                continue
            for pattern, secret_type in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    if 'process.env' not in line and 'os.environ' not in line and 'os.getenv' not in line:
                        issues.append({'type': 'exposed_secret', 'severity': 'critical', 'file': Path(file_path).name, 'line': i, 'message': f'Potential {secret_type} exposed in code. Use environment variables.', 'rule_id': 'no-secrets'})
                        break
        return issues

    def _check_eval_usage(self, file_path: str, lines: List[str]) -> List[Dict]:
        issues = []
        for i, line in enumerate(lines, 1):
            if re.search(r'\beval\s*\(', line) and not line.strip().startswith('//'):
                issues.append({'type': 'eval_usage', 'severity': 'critical', 'file': Path(file_path).name, 'line': i, 'message': 'eval() is dangerous and should be avoided. It can execute arbitrary code.', 'rule_id': 'no-eval'})
        return issues

    def _check_any_type(self, file_path: str, lines: List[str]) -> List[Dict]:
        issues = []
        for i, line in enumerate(lines, 1):
            if re.search(r':\s*any\b', line) and not line.strip().startswith('//'):
                issues.append({'type': 'any_type', 'severity': 'medium', 'file': Path(file_path).name, 'line': i, 'message': "Avoid using 'any' type. Use specific types for better type safety.", 'rule_id': 'no-any'})
        return issues

    def _check_non_null_assertion(self, file_path: str, lines: List[str]) -> List[Dict]:
        issues = []
        for i, line in enumerate(lines, 1):
            if re.search(r'!\s*\.', line) and not line.strip().startswith('//'):
                issues.append({'type': 'non_null_assertion', 'severity': 'medium', 'file': Path(file_path).name, 'line': i, 'message': 'Non-null assertion operator can cause runtime errors. Add proper null checks.', 'rule_id': 'no-non-null-assertion'})
        return issues

    def _check_print_statements(self, file_path: str, lines: List[str]) -> List[Dict]:
        issues = []
        for i, line in enumerate(lines, 1):
            if re.match(r'^\s*print\s*\(', line) and not line.strip().startswith('#'):
                issues.append({'type': 'print_statement', 'severity': 'low', 'file': Path(file_path).name, 'line': i, 'message': 'Print statement found. Use logging instead for better control.', 'rule_id': 'no-print'})
        return issues

    def _check_bare_except(self, file_path: str, lines: List[str]) -> List[Dict]:
        issues = []
        for i, line in enumerate(lines, 1):
            if re.match(r'^\s*except\s*:', line):
                issues.append({'type': 'bare_except', 'severity': 'high', 'file': Path(file_path).name, 'line': i, 'message': 'Bare except clause catches all exceptions. Specify exception types.', 'rule_id': 'no-bare-except'})
        return issues

    def _check_mutable_defaults(self, file_path: str, lines: List[str]) -> List[Dict]:
        issues = []
        for i, line in enumerate(lines, 1):
            if re.search(r'def\s+\w+\([^)]*=\s*[\[{]', line):
                issues.append({'type': 'mutable_default', 'severity': 'high', 'file': Path(file_path).name, 'line': i, 'message': 'Mutable default argument detected. Use None and initialize inside function.', 'rule_id': 'no-mutable-defaults'})
        return issues
