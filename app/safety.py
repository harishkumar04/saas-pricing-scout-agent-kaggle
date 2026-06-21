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

import os
import re
import yaml
from urllib.parse import urlparse
from google.adk.tools import BaseTool, ToolContext

class PolicyService:
    """A hybrid Policy Server designed to gate tool permissions and sanitize context."""

    def __init__(self):
        # Load policies configuration
        policies_path = os.path.join(os.path.dirname(__file__), "policies.yaml")
        try:
            with open(policies_path, encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        except Exception:
            # Safe default fallback
            self.config = {
                "roles": {},
                "security": {
                    "blocked_keywords": [],
                    "blocked_tlds": []
                }
            }

    def is_tool_allowed(self, agent_name: str, tool_name: str) -> bool:
        """Checks if a specific agent is authorized to call a given tool.

        Args:
            agent_name: The name of the ADK agent invoking the tool.
            tool_name: The name of the tool to be executed.

        Returns:
            True if the tool is allowed, False otherwise.
        """
        role_config = self.config.get("roles", {}).get(agent_name, {})
        allowed_tools = role_config.get("allowed_tools", [])
        # Always allow peer/parent handoff tool
        if tool_name == "transfer_to_agent":
            return True
        return tool_name in allowed_tools

    def resolve_context(self, template_str: str, override_state: dict = None) -> str:
        """Scans a template string for [[VARIABLE_NAME]] and replaces it with values from state or env.

        Args:
            template_str: The string containing potential placeholders.
            override_state: The current session state dictionary.

        Returns:
            The resolved and sanitized string.
        """
        if not template_str:
            return ""
        state_to_check = override_state or {}

        def replacement(match):
            var_name = match.group(1).strip()
            # 1. Prioritize runtime state overrides
            if var_name in state_to_check and state_to_check[var_name] is not None:
                return str(state_to_check[var_name])
            # 2. Fallback to validated environment variables
            elif var_name in os.environ and os.environ[var_name] is not None:
                return os.environ[var_name]
            # 3. Leave unresolved to prevent silent failures
            return match.group(0)

        return re.sub(r'\[\[([^\]]+)\]\]', replacement, template_str)

    def sanitize_tool_args(self, args: dict, state: dict) -> dict:
        """Recursively sanitizes tool arguments to resolve bracketed context placeholders.

        Args:
            args: The dictionary of arguments passed to the tool.
            state: The current session state.

        Returns:
            A sanitized dictionary of arguments.
        """
        resolved_args = {}
        for k, v in args.items():
            if isinstance(v, str):
                resolved_args[k] = self.resolve_context(v, state)
            elif isinstance(v, list):
                resolved_args[k] = [
                    self.resolve_context(i, state) if isinstance(i, str) else i
                    for i in v
                ]
            elif isinstance(v, dict):
                resolved_args[k] = self.sanitize_tool_args(v, state)
            else:
                resolved_args[k] = v
        return resolved_args

    def validate_tool_call(self, tool: BaseTool, args: dict, tool_context: ToolContext) -> dict | None:
        """Validates tool execution permissions, checks safety constraints, and sanitizes args.

        Args:
            tool: The tool being invoked.
            args: The arguments passed to the tool.
            tool_context: The ADK context for tool execution.

        Returns:
            A dictionary containing safety block info, or None to allow execution.
        """
        agent_name = tool_context.agent_name or "root_agent"

        # 1. Structural Gating: Check role authorization for the tool
        if not self.is_tool_allowed(agent_name, tool.name):
            return {
                "status": "blocked",
                "error_message": f"Security Guardrail: Agent '{agent_name}' is not authorized to execute tool '{tool.name}'."
            }

        # 2. Context Hygiene: Sanitize and resolve prompt-injected or bracketed placeholders
        sanitized = self.sanitize_tool_args(args, tool_context.state)
        args.clear()
        args.update(sanitized)

        # 3. Structural Gating: Safety checks for URL scraper tool
        if tool.name == "fetch_web_page":
            url = args.get("url", "")
            if not url:
                return {"status": "error", "error_message": "URL argument is missing."}

            parsed_url = urlparse(url)

            # Scheme validation
            if parsed_url.scheme not in ("http", "https"):
                return {
                    "status": "blocked",
                    "error_message": f"Security Guardrail: URL scheme '{parsed_url.scheme}' is not permitted. Only HTTP/HTTPS protocols are allowed."
                }

            netloc = parsed_url.netloc.lower()

            # Domain blacklist validation
            blocked_keywords = self.config.get("security", {}).get("blocked_keywords", [])
            for keyword in blocked_keywords:
                if keyword in netloc:
                    return {
                        "status": "blocked",
                        "error_message": f"Security Guardrail: Domain '{netloc}' is blocked because it is classified as a social network or non-business domain."
                    }

            # TLD blacklist validation
            blocked_tlds = self.config.get("security", {}).get("blocked_tlds", [])
            for tld in blocked_tlds:
                if netloc.endswith(tld):
                    return {
                        "status": "blocked",
                        "error_message": f"Security Guardrail: Top-level domain '{tld}' is blacklisted as suspicious or untrusted."
                    }

        return None

# Singleton service instance
policy_service = PolicyService()

async def domain_safety_guard(tool: BaseTool, args: dict, tool_context: ToolContext) -> dict | None:
    """Interceptors before executing a tool to enforce domain safety guardrails and policy constraints."""
    return policy_service.validate_tool_call(tool, args, tool_context)
