# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from urllib.parse import urlparse
from google.adk.tools import BaseTool, ToolContext

# Define blocked domain keywords (e.g. social media, untrusted, or personal blogs)
BLOCKED_KEYWORDS = [
    "facebook.com", "twitter.com", "x.com", "instagram.com", 
    "linkedin.com", "reddit.com", "youtube.com", "tiktok.com",
    "pinterest.com", "tumblr.com"
]

# Blocked TLDs (often associated with spam, phishing, or non-business activities)
BLOCKED_TLDS = [
    ".xyz", ".top", ".click", ".gq", ".cf", ".tk", ".ml", ".fit", ".loan", ".work"
]

async def domain_safety_guard(tool: BaseTool, args: dict, tool_context: ToolContext) -> dict | None:
    """Interceptors before executing a tool to enforce domain safety guardrails.
    
    If the tool is 'fetch_web_page', it validates that the URL is safe, HTTP/HTTPS,
    and does not point to a blocked or suspicious domain.
    """
    # Check if the tool is the scraper tool
    if tool.name == "fetch_web_page":
        url = args.get("url", "")
        if not url:
            return {"status": "error", "error_message": "URL argument is missing."}
            
        parsed_url = urlparse(url)
        
        # 1. Enforce HTTPS/HTTP schemes only
        if parsed_url.scheme not in ("http", "https"):
            return {
                "status": "blocked", 
                "error_message": f"Security Guardrail: URL scheme '{parsed_url.scheme}' is not permitted. Only HTTP/HTTPS protocols are allowed."
            }
            
        netloc = parsed_url.netloc.lower()
        
        # 2. Block social networks and non-business domains
        for keyword in BLOCKED_KEYWORDS:
            if keyword in netloc:
                return {
                    "status": "blocked",
                    "error_message": f"Security Guardrail: Domain '{netloc}' is blocked because it is classified as a social network or non-business domain."
                }
                
        # 3. Block suspicious/untrusted TLDs
        for tld in BLOCKED_TLDS:
            if netloc.endswith(tld):
                return {
                    "status": "blocked",
                    "error_message": f"Security Guardrail: Top-level domain '{tld}' is blacklisted as suspicious or untrusted."
                }
                
    # Return None to let execution proceed normally for other tools or valid URLs
    return None
