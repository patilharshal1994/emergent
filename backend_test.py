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

def main():
    print("🚀 Starting Code Quality API Tests")
    print("=" * 50)
    
    # Setup
    tester = CodeQualityAPITester()
    
    # Run all tests
    tests = [
        tester.test_health_endpoint,
        tester.test_root_endpoint,
        tester.test_file_upload_scan,
        tester.test_scan_history,
        tester.test_scan_details,
        tester.test_download_json_report,
        tester.test_download_html_report,
        tester.test_github_pr_scan,
    ]
    
    failed_tests = []
    
    for test in tests:
        try:
            if not test():
                failed_tests.append(test.__name__)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
            failed_tests.append(test.__name__)
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if failed_tests:
        print(f"❌ Failed tests: {', '.join(failed_tests)}")
        return 1
    else:
        print("✅ All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())