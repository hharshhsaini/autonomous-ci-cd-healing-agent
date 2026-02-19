import os
import json
import re
import time
from datetime import datetime
from collections import defaultdict
from typing import Dict, Tuple, Optional
from openai import OpenAI
from ..state import AgentState

SYSTEM_PROMPTS = {
    "python": "You are an expert Python developer. Fix the errors. Return ONLY the complete corrected file. No markdown, no explanation, no code blocks. Raw Python only.",
    "javascript": "You are an expert JavaScript developer. Fix the errors. Return ONLY the complete corrected file. No markdown, no explanation. Raw JavaScript only.",
    "typescript": "You are an expert TypeScript developer. Fix the errors. Return ONLY the complete corrected file. No markdown, no explanation. Raw TypeScript only.",
    "go": "You are an expert Go developer. Fix the errors. Return ONLY the complete corrected file. No markdown, no explanation. Raw Go only.",
}

def get_ai_client() -> Tuple[Optional[OpenAI], Optional[str], str]:
    """Get AI client - Groq or OpenAI with fallback. Returns (client, model, api_name)."""
    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if groq_key:
        print("[FIX] Using Groq API (llama-3.3-70b-versatile)")
        return OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1"), "llama-3.3-70b-versatile", "Groq"
    elif openai_key:
        print("[FIX] Using OpenAI API (gpt-4o-mini)")
        return OpenAI(api_key=openai_key), "gpt-4o-mini", "OpenAI"
    else:
        return None, None, "None"

def call_ai_with_retry(client: OpenAI, model: str, messages: list, api_name: str, max_retries: int = 5) -> Optional[str]:
    """Call AI API with exponential backoff retry logic. Will keep retrying until success or max attempts."""
    for attempt in range(max_retries):
        try:
            print(f"[FIX] {api_name} API call attempt {attempt + 1}/{max_retries}")
            
            response = client.chat.completions.create(
                model=model,
                temperature=0,
                max_tokens=4000,
                messages=messages
            )
            
            content = response.choices[0].message.content
            if content:
                print(f"[FIX] ✓ {api_name} API call successful")
                return content
            else:
                raise Exception("Empty response from API")
            
        except Exception as e:
            error_str = str(e)
            print(f"[FIX] ✗ Attempt {attempt + 1} failed: {error_str[:150]}")
            
            # Check if it's a rate limit error - retry with longer backoff
            if "429" in error_str or "rate_limit" in error_str.lower() or "rate limit" in error_str.lower():
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 3  # Exponential backoff: 3s, 6s, 12s, 24s, 48s
                    print(f"[FIX] ⏳ Rate limit hit, waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"{api_name} rate limit exceeded after {max_retries} attempts")
            
            # Check if it's a quota error - no point retrying
            if "quota" in error_str.lower() or "insufficient_quota" in error_str.lower():
                print(f"[FIX] ✗ {api_name} quota exceeded - cannot retry")
                raise Exception(f"{api_name} API quota exceeded - please add credits or check billing")
            
            # Check if it's an auth error - no point retrying
            if "401" in error_str or "authentication" in error_str.lower() or "invalid_api_key" in error_str.lower() or "api key" in error_str.lower():
                print(f"[FIX] ✗ {api_name} authentication failed - cannot retry")
                raise Exception(f"{api_name} API key is invalid or expired")
            
            # For network/timeout errors, retry with backoff
            if "timeout" in error_str.lower() or "connection" in error_str.lower() or "network" in error_str.lower():
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s, 16s, 32s
                    print(f"[FIX] ⏳ Network error, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            
            # For any other error, retry with standard backoff
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + 1  # 1s, 3s, 5s, 9s, 17s
                print(f"[FIX] ⏳ Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                # Last attempt failed
                raise Exception(f"{api_name} API failed after {max_retries} attempts: {error_str[:200]}")
    
    return None

def apply_fixes(state: AgentState) -> Dict:
    """Apply fixes to files using AI (Groq or OpenAI)."""
    try:
        # Get AI client
        client, model, api_name = get_ai_client()
        
        if not client:
            return {
                "fixes": state["fixes"],
                "errors_fixed": 0,
                "status": "failed",
                "error_message": "No API key configured (GROQ_API_KEY or OPENAI_API_KEY required)",
                "progress": 100
            }
        
        print(f"[FIX] Using {api_name} API with model: {model}")
        
        # Get language-specific system prompt
        lang = state.get("repo_language", "python")
        system_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS["python"])
        
        # Skip test files
        SKIP_PATTERNS = ['.test.js', '.spec.js', '.test.ts', '.spec.ts', 
                         '.test.jsx', '.spec.jsx', '_test.go', '_test.py',
                         'test_', '.test.', '.spec.', '/test/', '/tests/']
        
        # Group fixes by file
        files_map = defaultdict(list)
        for fix in state["fixes"]:
            if fix["status"] == "pending":
                if any(pattern in fix["file"].lower() for pattern in SKIP_PATTERNS):
                    fix["status"] = "skipped"
                    fix["fix_description"] = "Test file - skipped"
                else:
                    files_map[fix["file"]].append(fix)
        
        updated_fixes = state["fixes"].copy()
        errors_fixed = 0
        files_fixed = 0
        
        # Process each file
        for file_name, file_errors in files_map.items():
            try:
                # Read file
                file_path = os.path.join(state["repo_path"], file_name)
                
                # Skip if file doesn't exist
                if not os.path.exists(file_path):
                    for fix in file_errors:
                        fix["status"] = "failed"
                        fix["fix_description"] = "File not found"
                    continue
                
                # Read file content
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.read()
                except Exception as read_err:
                    for fix in file_errors:
                        fix["status"] = "failed"
                        fix["fix_description"] = f"Cannot read file: {str(read_err)}"
                    continue
                
                # Build prompt with all errors in this file
                errors_list = [
                    {
                        "line": fix["line"],
                        "type": fix["type"],
                        "message": fix["message"]
                    }
                    for fix in file_errors
                ]
                
                # Call AI with retry logic - WILL KEEP RETRYING UNTIL SUCCESS
                try:
                    print(f"[FIX] 🔧 Fixing {len(file_errors)} errors in {file_name} using {api_name}...")
                    
                    fixed_code = call_ai_with_retry(
                        client=client,
                        model=model,
                        api_name=api_name,
                        messages=[
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            {
                                "role": "user",
                                "content": f"""Fix ALL these errors in {file_name}:

Errors to fix:
{json.dumps(errors_list, indent=2)}

Current file content:
{file_content}

Return the COMPLETE corrected file. NO markdown, NO explanations, NO code blocks. Just the raw corrected code."""
                            }
                        ],
                        max_retries=5  # Will retry up to 5 times with exponential backoff
                    )
                    
                    if not fixed_code:
                        raise Exception("AI returned empty response")
                    
                    # Remove markdown code blocks if present
                    if "```" in fixed_code:
                        # Extract code from markdown blocks
                        code_match = re.search(r'```(?:python|javascript|typescript|java|go|rust)?\s*\n(.*?)```', fixed_code, re.DOTALL)
                        if code_match:
                            fixed_code = code_match.group(1)
                        else:
                            # Try without language specifier
                            code_match = re.search(r'```\s*\n(.*?)```', fixed_code, re.DOTALL)
                            if code_match:
                                fixed_code = code_match.group(1)
                    
                    # Strip leading/trailing whitespace but preserve internal structure
                    fixed_code = fixed_code.strip()
                    
                    # Ensure the file ends with a newline (standard practice)
                    if fixed_code and not fixed_code.endswith('\n'):
                        fixed_code += '\n'
                    
                    # Write back the fixed code
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_code)
                    
                    print(f"[FIX] ✓ Successfully fixed {len(file_errors)} errors in {file_name}")
                    
                    # Mark each error as fixed
                    for fix in file_errors:
                        fix["status"] = "fixed"
                        fix["fix_description"] = f"{api_name} AI corrected {fix['type']} issue"
                        fix["formatted"] = f"{fix['type']} error in {fix['file']} line {fix['line']} → Fix: {fix['fix_description']}"
                        errors_fixed += 1
                    
                    files_fixed += 1
                
                except Exception as ai_err:
                    error_str = str(ai_err)
                    print(f"[FIX] ✗ {api_name} error for {file_name}: {error_str[:200]}")
                    
                    # Mark errors in this file as failed
                    for fix in file_errors:
                        fix["status"] = "failed"
                        fix["fix_description"] = f"{api_name}: {error_str[:150]}"
            
            except Exception as e:
                # Mark errors in this file as failed
                for fix in file_errors:
                    fix["status"] = "failed"
                    fix["fix_description"] = f"Failed to fix: {str(e)[:200]}"
                print(f"[FIX] ✗ Error fixing {file_name}: {str(e)}")
        
        # Build result message
        if errors_fixed > 0:
            result_msg = f"Applied fixes to {files_fixed} files ({errors_fixed} errors) using {api_name} AI"
            status = "verifying"
            progress = 78
            current_agent = "Verify Agent"
            error_message = ""
        else:
            result_msg = f"✗ All fixes failed using {api_name} - check API key and quota"
            status = "failed"
            progress = 100
            current_agent = "Fix Agent"
            error_message = f"All fixes failed - check {api_name} API key and quota"
        
        return {
            "fixes": updated_fixes,
            "errors_fixed": errors_fixed,
            "status": status,
            "progress": progress,
            "current_agent": current_agent,
            "error_message": error_message,
            "timeline": state["timeline"] + [{
                "agent": "Fix Agent",
                "msg": result_msg,
                "timestamp": datetime.now().isoformat(),
                "iteration": state["retry_count"],
                "passed": errors_fixed > 0
            }]
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"[FIX] ✗ Fatal error: {error_msg}")
        
        # Determine which API was being used
        try:
            _, _, api_name = get_ai_client()
        except:
            api_name = "API"
        
        return {
            "fixes": state["fixes"],
            "errors_fixed": 0,
            "status": "failed",
            "error_message": f"Fix Agent failed ({api_name}): {error_msg[:200]}",
            "progress": 100,
            "timeline": state.get("timeline", []) + [{
                "agent": "Fix Agent",
                "msg": f"✗ Fatal error ({api_name}): {error_msg[:100]}",
                "timestamp": datetime.now().isoformat(),
                "iteration": state.get("retry_count", 0),
                "passed": False
            }]
        }
