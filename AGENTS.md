# AI Agent Coding Guidelines & Conventions

This file defines the engineering DNA, stack, rules, and best practices for any AI coding agent working on the **SaaS Pricing & Intelligence Scout** repository.

## The One-Line Mental Model
> **System Prompt** = Instinct  
> **AGENTS.md** = Project README/Guidelines  
> **Tools / MCP** = Hands/Capabilities  
> **RAG / Context** = Library  
> **Agent Skills** = The runbook from an experienced colleague that the AI never forgets.

## Core Rules of Engagement

1.  **Deep Thought Before Action**: Always state assumptions, surface potential trade-offs, and clarify ambiguity before writing code. Never guess silently.
2.  **Surgical Changes**: Restrict modifications strictly to the targeted lines of code. Preserve all unrelated syntax, comments, variables, and styling.
3.  **Minimal Code Footprint**: Write only the absolute minimum amount of code required to solve the immediate issue. Do not add unrequested helper abstractions, speculative features, or predictive configurations.
4.  **Google-Style Docstrings**: All Python functions must include Google-style docstrings with clear `Args`, `Returns`, and type hints to ensure the LLM can auto-introspect parameters correctly.
5.  **Zero Ambient Authority**: Never hardcode API keys, secrets, or file paths. Rely exclusively on environment variables and policies configured via the policy server.
6.  **Always Maintain Documentation**: If code functionality changes, update the corresponding `README.md` and `CHANGELOG.md` immediately.

## Tech Stack
*   **Engine**: Gemini SDK / Google ADK (Agent Development Kit)
*   **Runtime**: Python 3.11+ / FastAPI
*   **Scraper**: BeautifulSoup4 / HTTPX
*   **MCP Server**: FastMCP / stdio connection
*   **Testing**: Pytest / Agents CLI Eval
