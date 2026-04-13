import os
from emergentintegrations.llm.chat import LlmChat, UserMessage

class AISuggestionService:
    """AI-powered code fix suggestions using GPT-5.2"""
    
    def __init__(self):
        self.api_key = os.getenv('EMERGENT_LLM_KEY')
        if not self.api_key:
            print("Warning: EMERGENT_LLM_KEY not set. AI suggestions will be unavailable.")
    
    async def get_suggestion(self, issue: dict) -> str:
        """Get AI-powered fix suggestion for a code issue"""
        if not self.api_key:
            return "AI suggestions unavailable. Please configure EMERGENT_LLM_KEY."
        
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"suggestion_{issue['file']}_{issue['line']}",
                system_message="You are an expert code reviewer. Provide concise, actionable fix suggestions for code quality issues. Focus on best practices and security."
            )
            chat.with_model("openai", "gpt-5.2")
            
            prompt = f"""
Code Quality Issue:
- Type: {issue['type']}
- Severity: {issue['severity']}
- File: {issue['file']}
- Line: {issue['line']}
- Message: {issue['message']}
- Rule: {issue.get('rule_id', 'N/A')}

Provide a concise fix suggestion (2-3 sentences max) with a code example if applicable.
"""
            
            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            
            return response.strip()
            
        except Exception as e:
            return f"Error generating suggestion: {str(e)}"