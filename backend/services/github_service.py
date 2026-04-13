import os
from typing import Optional, Dict, List
import base64

try:
    from github import Github, Auth
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

class GitHubService:
    """Service for GitHub PR integration"""
    
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        self.github = None
        
        if self.token and GITHUB_AVAILABLE:
            try:
                auth = Auth.Token(self.token)
                self.github = Github(auth=auth)
            except Exception as e:
                print(f"Error initializing GitHub client: {str(e)}")
    
    async def get_pr_files(self, repo_name: str, pr_number: int) -> Optional[Dict]:
        """Get files from a GitHub PR"""
        if not self.github:
            return None
        
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            pr_info = {
                'title': pr.title,
                'author': pr.user.login,
                'created_at': pr.created_at.isoformat(),
                'state': pr.state,
                'files_changed': pr.changed_files,
                'additions': pr.additions,
                'deletions': pr.deletions
            }
            
            files = []
            for file in pr.get_files():
                file_info = {
                    'filename': file.filename,
                    'status': file.status,
                    'additions': file.additions,
                    'deletions': file.deletions,
                    'changes': file.changes
                }
                
                if file.status != 'removed':
                    try:
                        content_file = repo.get_contents(file.filename, ref=pr.head.sha)
                        if hasattr(content_file, 'content'):
                            content = base64.b64decode(content_file.content).decode('utf-8')
                            file_info['content'] = content
                    except Exception:
                        pass
                
                files.append(file_info)
            
            return {
                'pr_info': pr_info,
                'files': files
            }
            
        except Exception as e:
            print(f"Error fetching PR files: {str(e)}")
            return None