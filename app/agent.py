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
from app.tools import save_intelligence_report, export_pricing_strategy, post_slack_notification
from app.safety import domain_safety_guard

# Import tools directly from our custom MCP Server implementation to run them programmatically
from app.mcp_server import fetch_web_page as mcp_fetch_web_page
from app.mcp_server import get_own_pricing_catalog as mcp_get_own_pricing_catalog
from app.mcp_server import get_competitor_history as mcp_get_competitor_history
from app.mcp_server import search_competitor_pricing_news as mcp_search_competitor_pricing_news

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

def get_competitor_history(competitor_name: str) -> dict:
    """Retrieves the recorded pricing history logs for a specific competitor.

    Args:
        competitor_name: The name or URL slug of the competitor.
    """
    return mcp_get_competitor_history(competitor_name)

def search_competitor_pricing_news(competitor_name: str) -> dict:
    """Searches the internet for news articles and reports regarding competitor pricing updates.

    Args:
        competitor_name: The name or domain of the competitor to search.
    """
    return mcp_search_competitor_pricing_news(competitor_name)

# Define the shared Gemini model as a string to allow auto-routing to AI Studio or Vertex AI
shared_model = "gemini-2.5-flash"

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
    description="Queries our internal pricing catalog, history logs, and pricing news to compare plans and analyze trends.",
    instruction="""You are the Analyst Agent.
Your job is to:
1. Fetch our internal SaaS pricing catalog using the get_own_pricing_catalog tool.
2. Query the competitor's historical pricing logs using the get_competitor_history tool.
3. Search for external competitor pricing news using the search_competitor_pricing_news tool.
4. Compare our plans side-by-side with the competitor pricing provided by the Scout Agent.
5. Calculate price differences (in percentages), identify features we lack, and highlight gaps or opportunities.
6. Synthesize the pricing history and news search results into a visual pricing timeline. You MUST build a Mermaid diagram (using a Gantt chart, flowchart, or timeline syntax, e.g. `gantt` or `graph TD` or `timeline`) illustrating the timeline of the competitor's pricing changes, dates, and amounts.
Once you have compared the pricing and built the timeline, you MUST immediately call the transfer_to_agent tool to route control back to the coordinator_agent. Do not end your turn without transferring control.""",
    tools=[get_own_pricing_catalog, get_competitor_history, search_competitor_pricing_news],
    before_tool_callback=domain_safety_guard
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
2. Delegate to the analyst_agent to compare those details with our own internal catalog, and to fetch competitor historical pricing and news timeline.
3. Combine their outputs to generate a comprehensive competitive intelligence report.
   The report must be in Markdown format and include:
   - Executive Summary
   - Side-by-Side Comparison Table (Competitor Tiers vs. Our Tiers)
   - Price Differentials (mathematical comparisons/percentage differences)
   - Identified Feature Gaps
   - Historical Pricing Timeline (A visual timeline rendered as a Mermaid diagram showing competitor pricing changes, dates, and amounts)
   - Strategic Recommendations (e.g., optimize pricing, introduce a mid-tier, bundle features)
4. Call the save_intelligence_report tool immediately to save this report to a local file. You MUST invoke save_intelligence_report with the generated report content. This is a mandatory operational gate.
5. Call the post_slack_notification tool immediately after saving the intelligence report to post a summary of the competitor changes to the marketing and sales teams.
6. Present the saved report and its filepath to the user.
7. If the user approves of the recommended strategy, offer to call the export_pricing_strategy tool to write changes to production.""",
    sub_agents=[scout_agent, analyst_agent],
    tools=[save_intelligence_report, export_pricing_tool, post_slack_notification],
    before_tool_callback=domain_safety_guard
)

app = App(
    root_agent=root_agent,
    name="app",
)
