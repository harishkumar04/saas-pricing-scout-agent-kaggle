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
from dotenv import load_dotenv
import google.auth
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.tools import FunctionTool

# Load env file
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

# Enforce robust GCP config fallback for local environment
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "releaseradar-hackathon")
try:
    _, credentials_project = google.auth.default()
    if credentials_project:
        project_id = credentials_project
except Exception:
    # Fallback silently for local key-based dev or playground runs
    pass

os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "True")

# Import custom tools and safety plugins
from app.tools import save_intelligence_report, export_pricing_strategy
from app.safety import domain_safety_guard

# Import tools directly from our custom MCP Server implementation to run them programmatically
from app.mcp_server import fetch_web_page as mcp_fetch_web_page
from app.mcp_server import get_own_pricing_catalog as mcp_get_own_pricing_catalog

# Wrapper functions for MCP tools to ensure 100% compatibility with local evaluation serialization
async def fetch_web_page(url: str) -> dict:
    """Fetches a web page by URL, parses the HTML, and returns the cleaned text.

    Args:
        url: The absolute HTTP/HTTPS URL of the web page to fetch.
    """
    return await mcp_fetch_web_page(url)

def get_own_pricing_catalog() -> dict:
    """Returns our company's own product pricing catalog (plans, pricing, and features)."""
    return mcp_get_own_pricing_catalog()

# Define the shared Gemini model as a string to allow auto-routing to AI Studio or Vertex AI
shared_model = "gemini-3.5-flash"

# 1. Scout Agent: Crawls and summarizes competitor pricing web pages
scout_agent = Agent(
    name="scout_agent",
    model=shared_model,
    description="Crawls, fetches, and extracts raw pricing details from competitor URLs.",
    instruction="""You are the Scout Agent.
Your sole job is to fetch and extract raw pricing information from competitor pricing links using the fetch_web_page tool.
Provide a clean summary of the plan names, prices, billing frequency, and key features found.
Do not compare them to our own plans—just report the competitor facts.
Once you have fetched and summarized the competitor's pricing details, you MUST immediately call the transfer_to_agent tool to route control to the analyst_agent. Do not end your turn without transferring control.""",
    tools=[fetch_web_page],
    before_tool_callback=domain_safety_guard
)

# 2. Analyst Agent: Accesses internal catalog and compares plans
analyst_agent = Agent(
    name="analyst_agent",
    model=shared_model,
    description="Queries our internal pricing catalog and performs mathematical comparison analysis.",
    instruction="""You are the Analyst Agent.
Your job is to fetch our internal SaaS pricing catalog using the get_own_pricing_catalog tool.
Compare our plans side-by-side with the competitor pricing provided by the Scout Agent.
Calculate price differences (in percentages), identify features we lack, and highlight gaps or opportunities.
Once you have compared the pricing catalog, you MUST immediately call the transfer_to_agent tool to route control back to the coordinator_agent. Do not end your turn without transferring control.""",
    tools=[get_own_pricing_catalog]
)

# 3. Coordinator Agent: Orchestrates the work, creates reports, and manages sensitive actions
export_pricing_tool = FunctionTool(
    export_pricing_strategy,
    require_confirmation=True  # Secures active database modification with HIL gate
)

root_agent = Agent(
    name="coordinator_agent",
    model=shared_model,
    instruction="""You are the SaaS Pricing & Intelligence Coordinator.
Your mission is to perform competitive intelligence for our company.

When a user asks you to analyze a competitor pricing page (e.g., by URL):
1. Delegate to the scout_agent to fetch and summarize the competitor's pricing details.
2. Delegate to the analyst_agent to compare those details with our own internal catalog.
3. Combine their outputs to generate a comprehensive competitive intelligence report.
   The report must be in Markdown format and include:
   - Executive Summary
   - Side-by-Side Comparison Table (Competitor Tiers vs. Our Tiers)
   - Price Differentials (mathematical comparisons/percentage differences)
   - Identified Feature Gaps
   - Strategic Recommendations (e.g., optimize pricing, introduce a mid-tier, bundle features)
4. Call the save_intelligence_report tool immediately to save this report to a local file. You MUST invoke save_intelligence_report with the generated report content. This is a mandatory operational gate.
5. Present the saved report and its filepath to the user.
6. If the user approves of the recommended strategy, offer to call the export_pricing_strategy tool to write changes to production.""",
    sub_agents=[scout_agent, analyst_agent],
    tools=[save_intelligence_report, export_pricing_tool]
)

app = App(
    root_agent=root_agent,
    name="app",
)
