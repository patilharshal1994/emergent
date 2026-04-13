import requests
import sys
import json
import tempfile
import os
from datetime import datetime
from pathlib import Path

class CodeQualityAPITester:
    def __init__(self, base_url="https://quality-gate-15.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.scan_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                headers['Content-Type'] = 'application/json'
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_endpoint(self):
        """Test health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        return success and 'status' in response and response['status'] == 'healthy'

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API",
            "GET",
            "",
            200
        )
        return success and 'message' in response

    def create_test_js_file(self):
        """Create a test JavaScript file with various issues"""
        test_code = """
// Test JavaScript file with various code quality issues
var oldVariable = "should use let/const";
console.log("Debug statement");
debugger; // Should be removed
eval("dangerous code");

function testFunction() {
    var anotherVar = "more var usage";
    console.warn("Another console statement");
    return anotherVar;
}

// Unused import simulation
import { unusedFunction } from 'some-module';

// API key exposure
const apiKey = "sk-1234567890abcdef1234567890abcdef";
"""
        return test_code

    def create_test_python_file(self):
        """Create a test Python file with various issues"""
        test_code = """
# Test Python file with code quality issues
import os
import sys

def bad_function(mutable_list=[]):  # Mutable default
    print("Debug print statement")  # Should use logging
    try:
        risky_operation()
    except:  # Bare except
        pass
    
    # Exposed secret
    secret_key = "sk-abcdef1234567890abcdef1234567890"
    return mutable_list

def risky_operation():
    pass
"""
        return test_code

    def test_file_upload_scan(self):
        """Test file upload scanning"""
        # Create test files
        js_content = self.create_test_js_file()
        py_content = self.create_test_python_file()
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as js_file:
            js_file.write(js_content)
            js_file_path = js_file.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as py_file:
            py_file.write(py_content)
            py_file_path = py_file.name

        try:
            # Prepare files for upload
            files = [
                ('files', ('test.js', open(js_file_path, 'rb'), 'text/javascript')),
                ('files', ('test.py', open(py_file_path, 'rb'), 'text/x-python'))
            ]
            
            data = {'enable_ai': 'true'}
            
            success, response = self.run_test(
                "File Upload Scan",
                "POST",
                "scan/upload",
                200,
                data=data,
                files=files
            )
            
            # Close files
            for _, file_tuple in files:
                file_tuple[1].close()
            
            if success and 'scan_id' in response:
                self.scan_id = response['scan_id']
                print(f"   Scan ID: {self.scan_id}")
                print(f"   Issues found: {len(response.get('issues', []))}")
                return True
            return False
            
        finally:
            # Clean up temporary files
            try:
                os.unlink(js_file_path)
                os.unlink(py_file_path)
            except:
                pass

    def test_scan_history(self):
        """Test scan history endpoint"""
        success, response = self.run_test(
            "Scan History",
            "GET",
            "scan/history",
            200
        )
        
        if success and 'history' in response:
            history = response['history']
            print(f"   Found {len(history)} scans in history")
            return True
        return False

    def test_scan_details(self):
        """Test getting scan details by ID"""
        if not self.scan_id:
            print("❌ No scan ID available for testing scan details")
            return False
            
        success, response = self.run_test(
            "Scan Details",
            "GET",
            f"scan/{self.scan_id}",
            200
        )
        
        if success and 'scan_id' in response:
            print(f"   Retrieved scan: {response['scan_id']}")
            print(f"   Issues: {len(response.get('issues', []))}")
            return True
        return False

    def test_download_json_report(self):
        """Test downloading JSON report"""
        if not self.scan_id:
            print("❌ No scan ID available for testing JSON download")
            return False
            
        url = f"{self.api_url}/scan/{self.scan_id}/download"
        params = {'format': 'json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Download JSON Report...")
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                return True
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def test_download_html_report(self):
        """Test downloading HTML report"""
        if not self.scan_id:
            print("❌ No scan ID available for testing HTML download")
            return False
            
        url = f"{self.api_url}/scan/{self.scan_id}/download"
        params = {'format': 'html'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Download HTML Report...")
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                # Check if it's valid HTML
                if b'<!DOCTYPE html>' in response.content:
                    print("   ✅ Valid HTML format detected")
                return True
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def test_github_pr_scan(self):
        """Test GitHub PR scanning (expected to fail without token)"""
        # Use form data format as expected by the endpoint
        data = {
            'repo': 'facebook/react',
            'pr_number': '1',
            'enable_ai': 'true'
        }
        
        url = f"{self.api_url}/scan/github-pr"
        self.tests_run += 1
        print(f"\n🔍 Testing GitHub PR Scan (Expected to fail - no token)...")
        
        try:
            response = requests.post(url, data=data)
            
            # Should fail with 500 because GitHub token is not configured
            if response.status_code == 500:
                try:
                    error_data = response.json()
                    if 'GitHub token not configured' in error_data.get('detail', ''):
                        self.tests_passed += 1
                        print(f"✅ Passed - Status: {response.status_code}")
                        print("   ✅ Expected failure - GitHub token not configured")
                        return True
                except:
                    pass
            
            print(f"❌ Failed - Expected 500 with GitHub token error, got {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text}")
            return False
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    # ═══════════════════════════════════════════
    # NEW FEATURES TESTING (ITERATION 2)
    # ═══════════════════════════════════════════

    def test_get_rules(self):
        """Test GET /api/rules - should return 11 default rules"""
        success, response = self.run_test(
            "Get Rules (Default 11 rules)",
            "GET",
            "rules",
            200
        )
        
        if success and 'rules' in response:
            rules = response['rules']
            print(f"   Found {len(rules)} rules")
            if len(rules) >= 11:
                default_rules = [r for r in rules if r.get('category') != 'custom']
                print(f"   Default rules: {len(default_rules)}")
                if len(default_rules) == 11:
                    print("   ✅ Correct number of default rules (11)")
                    return True
                else:
                    print(f"   ❌ Expected 11 default rules, got {len(default_rules)}")
                    return False
            else:
                print(f"   ❌ Expected at least 11 rules, got {len(rules)}")
                return False
        return False

    def test_create_custom_rule(self):
        """Test POST /api/rules - create a new custom rule"""
        rule_data = {
            "name": "No TODO Comments",
            "description": "Detect TODO comments in code",
            "severity": "low",
            "pattern": "TODO|FIXME|HACK",
            "file_types": [".js", ".jsx", ".ts", ".tsx"],
            "category": "custom"
        }
        
        success, response = self.run_test(
            "Create Custom Rule",
            "POST",
            "rules",
            200,
            data=rule_data
        )
        
        if success and 'rule_id' in response:
            self.custom_rule_id = response['rule_id']
            print(f"   Created rule ID: {self.custom_rule_id}")
            return True
        return False

    def test_verify_custom_rule_in_list(self):
        """Test that custom rule appears in GET /api/rules"""
        success, response = self.run_test(
            "Verify Custom Rule in List",
            "GET",
            "rules",
            200
        )
        
        if success and 'rules' in response:
            rules = response['rules']
            custom_rules = [r for r in rules if r.get('category') == 'custom']
            print(f"   Found {len(custom_rules)} custom rules")
            if len(custom_rules) > 0:
                print("   ✅ Custom rule found in rules list")
                return True
            else:
                print("   ❌ No custom rules found")
                return False
        return False

    def test_toggle_rule_enabled(self):
        """Test PUT /api/rules/{rule_id} - toggle enabled state"""
        # Test with 'no-console' rule
        rule_id = "no-console"
        
        success, response = self.run_test(
            "Toggle Rule Enabled (no-console)",
            "PUT",
            f"rules/{rule_id}",
            200,
            data={"enabled": False}
        )
        
        if success:
            print("   ✅ Successfully toggled rule enabled state")
            return True
        return False

    def test_change_rule_severity(self):
        """Test PUT /api/rules/{rule_id} - change severity"""
        # Test changing 'no-console' from low to high
        rule_id = "no-console"
        
        success, response = self.run_test(
            "Change Rule Severity (no-console low->high)",
            "PUT",
            f"rules/{rule_id}",
            200,
            data={"severity": "high"}
        )
        
        if success:
            print("   ✅ Successfully changed rule severity")
            return True
        return False

    def test_delete_custom_rule(self):
        """Test DELETE /api/rules/{custom_rule_id} - delete custom rule"""
        if not hasattr(self, 'custom_rule_id'):
            print("❌ No custom rule ID available for deletion test")
            return False
            
        success, response = self.run_test(
            "Delete Custom Rule",
            "DELETE",
            f"rules/{self.custom_rule_id}",
            200
        )
        
        if success:
            print("   ✅ Successfully deleted custom rule")
            return True
        return False

    def test_delete_builtin_rule_fails(self):
        """Test DELETE /api/rules/no-console - should fail (cannot delete built-in)"""
        url = f"{self.api_url}/rules/no-console"
        self.tests_run += 1
        print(f"\n🔍 Testing Delete Built-in Rule (Expected to fail)...")
        
        try:
            response = requests.delete(url)
            
            # Should fail with 400 because built-in rules cannot be deleted
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    if 'Cannot delete built-in rules' in error_data.get('detail', ''):
                        self.tests_passed += 1
                        print(f"✅ Passed - Status: {response.status_code}")
                        print("   ✅ Expected failure - Cannot delete built-in rules")
                        return True
                except:
                    pass
            
            print(f"❌ Failed - Expected 400 with built-in rule error, got {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text}")
            return False
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def test_analytics_trends(self):
        """Test GET /api/analytics/trends - get analytics data"""
        success, response = self.run_test(
            "Analytics Trends",
            "GET",
            "analytics/trends",
            200
        )
        
        if success:
            required_fields = ['trends', 'severity_distribution', 'top_issues', 'totals']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                print("   ✅ All required analytics fields present")
                print(f"   Trends count: {len(response.get('trends', []))}")
                print(f"   Severity distribution: {len(response.get('severity_distribution', []))}")
                print(f"   Top issues: {len(response.get('top_issues', []))}")
                return True
            else:
                print(f"   ❌ Missing fields: {missing_fields}")
                return False
        return False

    def test_webhook_config(self):
        """Test GET /api/webhook/config - get webhook configuration"""
        success, response = self.run_test(
            "Webhook Config",
            "GET",
            "webhook/config",
            200
        )
        
        if success:
            required_fields = ['webhook_url', 'webhook_secret', 'enabled']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                print("   ✅ All required webhook config fields present")
                print(f"   Webhook URL: {response.get('webhook_url', '')[:50]}...")
                print(f"   Enabled: {response.get('enabled')}")
                return True
            else:
                print(f"   ❌ Missing fields: {missing_fields}")
                return False
        return False

    def test_update_webhook_config(self):
        """Test PUT /api/webhook/config - toggle enabled to false"""
        success, response = self.run_test(
            "Update Webhook Config (enabled=false)",
            "PUT",
            "webhook/config",
            200,
            data={"enabled": False}
        )
        
        if success and 'enabled' in response:
            if response['enabled'] == False:
                print("   ✅ Successfully disabled webhook")
                return True
            else:
                print(f"   ❌ Expected enabled=false, got {response['enabled']}")
                return False
        return False

    def test_github_actions_yaml(self):
        """Test GET /api/webhook/github-actions-yaml - get YAML content"""
        success, response = self.run_test(
            "GitHub Actions YAML",
            "GET",
            "webhook/github-actions-yaml",
            200
        )
        
        if success and 'yaml' in response:
            yaml_content = response['yaml']
            if 'name: CodeQuality Gate Scan' in yaml_content and 'on:' in yaml_content:
                print("   ✅ Valid GitHub Actions YAML content")
                print(f"   YAML length: {len(yaml_content)} characters")
                return True
            else:
                print("   ❌ Invalid YAML content structure")
                return False
        return False

    # ═══════════════════════════════════════════
    # NEW FEATURES TESTING (ITERATION 3) - ESLint Integration & Rule Import/Export
    # ═══════════════════════════════════════════

    def create_eslint_test_js_file(self):
        """Create a test JavaScript file specifically for ESLint testing"""
        test_code = """var x = 1;
console.log(x);
if (x == 1) {
    var y = 2;
}
var unused = "not used";
function test() {
    if (x == 1) {
        return true;
    }
}
"""
        return test_code

    def test_eslint_integration_scan(self):
        """Test ESLint integration with specific JS file containing ESLint issues"""
        # Create test file with specific ESLint issues
        js_content = self.create_eslint_test_js_file()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as js_file:
            js_file.write(js_content)
            js_file_path = js_file.name

        try:
            # Prepare files for upload
            files = [
                ('files', ('eslint_test.js', open(js_file_path, 'rb'), 'text/javascript'))
            ]
            
            data = {'enable_ai': 'false'}  # Disable AI for faster testing
            
            success, response = self.run_test(
                "ESLint Integration Scan",
                "POST",
                "scan/upload",
                200,
                data=data,
                files=files
            )
            
            # Close file
            files[0][1][1].close()
            
            if success and 'issues' in response:
                issues = response['issues']
                eslint_issues = [issue for issue in issues if issue.get('rule_id', '').startswith('eslint/')]
                
                print(f"   Total issues found: {len(issues)}")
                print(f"   ESLint issues found: {len(eslint_issues)}")
                
                # Check for specific ESLint rules
                eslint_rules_found = set()
                for issue in eslint_issues:
                    rule_id = issue.get('rule_id', '')
                    if rule_id.startswith('eslint/'):
                        eslint_rules_found.add(rule_id.replace('eslint/', ''))
                        print(f"   Found ESLint rule: {rule_id}")
                
                # Expected ESLint rules for our test code
                expected_rules = {'no-unused-vars', 'eqeqeq', 'no-var'}
                found_expected = eslint_rules_found.intersection(expected_rules)
                
                if len(found_expected) >= 2:  # At least 2 of the expected rules
                    print(f"   ✅ Found expected ESLint rules: {found_expected}")
                    self.eslint_scan_id = response.get('scan_id')
                    return True
                else:
                    print(f"   ❌ Expected ESLint rules {expected_rules}, found {eslint_rules_found}")
                    return False
            return False
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(js_file_path)
            except:
                pass

    def test_combined_pattern_eslint_scan(self):
        """Test that scan returns both pattern-based AND ESLint issues, deduped"""
        # Create test file with both pattern issues and ESLint issues
        js_content = """var x = 1;
console.log("Debug message");  // Pattern issue: console statement
if (x == 1) {  // ESLint issue: eqeqeq
    debugger;  // Pattern issue: debugger statement
}
var unused = "not used";  // ESLint issue: no-unused-vars
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as js_file:
            js_file.write(js_content)
            js_file_path = js_file.name

        try:
            files = [
                ('files', ('combined_test.js', open(js_file_path, 'rb'), 'text/javascript'))
            ]
            
            data = {'enable_ai': 'false'}
            
            success, response = self.run_test(
                "Combined Pattern + ESLint Scan",
                "POST",
                "scan/upload",
                200,
                data=data,
                files=files
            )
            
            files[0][1][1].close()
            
            if success and 'issues' in response:
                issues = response['issues']
                eslint_issues = [issue for issue in issues if issue.get('rule_id', '').startswith('eslint/')]
                pattern_issues = [issue for issue in issues if not issue.get('rule_id', '').startswith('eslint/')]
                
                print(f"   Total issues: {len(issues)}")
                print(f"   ESLint issues: {len(eslint_issues)}")
                print(f"   Pattern issues: {len(pattern_issues)}")
                
                # Should have both types of issues
                if len(eslint_issues) > 0 and len(pattern_issues) > 0:
                    print("   ✅ Found both ESLint and pattern-based issues")
                    return True
                else:
                    print("   ❌ Missing either ESLint or pattern-based issues")
                    return False
            return False
            
        finally:
            try:
                os.unlink(js_file_path)
            except:
                pass

    def test_rules_export(self):
        """Test GET /api/rules/export - export rules as JSON"""
        success, response = self.run_test(
            "Rules Export",
            "GET",
            "rules/export",
            200
        )
        
        if success:
            required_fields = ['version', 'exported_at', 'rules_count', 'rules']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                rules_count = response.get('rules_count', 0)
                rules_array = response.get('rules', [])
                
                print(f"   ✅ Export format valid")
                print(f"   Version: {response.get('version')}")
                print(f"   Rules count: {rules_count}")
                print(f"   Actual rules array length: {len(rules_array)}")
                
                if rules_count == len(rules_array) and rules_count > 0:
                    print("   ✅ Rules count matches array length")
                    # Store export data for import test
                    self.export_data = response
                    return True
                else:
                    print(f"   ❌ Rules count mismatch: {rules_count} vs {len(rules_array)}")
                    return False
            else:
                print(f"   ❌ Missing required fields: {missing_fields}")
                return False
        return False

    def test_rules_import(self):
        """Test POST /api/rules/import - import rules from JSON file"""
        if not hasattr(self, 'export_data'):
            print("❌ No export data available for import test")
            return False
        
        # Create a temporary JSON file with export data
        import_data = {
            "version": "2.0",
            "exported_at": datetime.now().isoformat(),
            "rules_count": 1,
            "rules": [
                {
                    "rule_id": "test-import-rule",
                    "name": "Test Import Rule",
                    "description": "Test rule for import functionality",
                    "severity": "medium",
                    "enabled": True,
                    "pattern": "TEST_PATTERN",
                    "file_types": [".js"],
                    "category": "custom"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as json_file:
            json.dump(import_data, json_file)
            json_file_path = json_file.name

        try:
            # Prepare file for upload
            files = [
                ('file', ('test_rules.json', open(json_file_path, 'rb'), 'application/json'))
            ]
            
            success, response = self.run_test(
                "Rules Import",
                "POST",
                "rules/import",
                200,
                files=files
            )
            
            files[0][1][1].close()
            
            if success:
                required_fields = ['message', 'imported', 'skipped']
                missing_fields = [field for field in required_fields if field not in response]
                
                if not missing_fields:
                    imported = response.get('imported', 0)
                    skipped = response.get('skipped', 0)
                    
                    print(f"   ✅ Import response valid")
                    print(f"   Imported: {imported}")
                    print(f"   Skipped: {skipped}")
                    print(f"   Message: {response.get('message')}")
                    
                    if imported > 0:
                        print("   ✅ Successfully imported rules")
                        return True
                    else:
                        print("   ❌ No rules were imported")
                        return False
                else:
                    print(f"   ❌ Missing response fields: {missing_fields}")
                    return False
            return False
            
        finally:
            try:
                os.unlink(json_file_path)
            except:
                pass

def main():
    print("🚀 Starting Code Quality API Tests - ITERATION 3 (ESLint Integration & Rule Import/Export)")
    print("=" * 80)
    
    # Setup
    tester = CodeQualityAPITester()
    
    # Run core tests first (to ensure basic functionality)
    core_tests = [
        tester.test_health_endpoint,
        tester.test_root_endpoint,
    ]
    
    # NEW FEATURES TESTS (ITERATION 3)
    new_feature_tests = [
        tester.test_eslint_integration_scan,
        tester.test_combined_pattern_eslint_scan,
        tester.test_rules_export,
        tester.test_rules_import,
    ]
    
    all_tests = core_tests + new_feature_tests
    failed_tests = []
    
    print("🔧 Running Core Tests...")
    print("-" * 50)
    
    for test in core_tests:
        try:
            if not test():
                failed_tests.append(test.__name__)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
            failed_tests.append(test.__name__)
    
    print("\n🆕 Running NEW Feature Tests (ESLint Integration & Rule Import/Export)...")
    print("-" * 70)
    
    for test in new_feature_tests:
        try:
            if not test():
                failed_tests.append(test.__name__)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
            failed_tests.append(test.__name__)
    
    # Print results
    print("\n" + "=" * 80)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if failed_tests:
        print(f"❌ Failed tests: {', '.join(failed_tests)}")
        return 1
    else:
        print("✅ All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())