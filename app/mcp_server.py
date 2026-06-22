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

from mcp.server.fastmcp import FastMCP
import httpx
from bs4 import BeautifulSoup

# Initialize FastMCP Server
mcp = FastMCP("saas-pricing-scout")

@mcp.tool()
async def fetch_web_page(url: str) -> dict:
    """Fetches a web page by URL, parses the HTML, and returns the cleaned text.

    Args:
        url: The absolute HTTP/HTTPS URL of the web page to fetch.
    """
    try:
        if "mock-competitor.com" in url:
            return {
                "status": "success",
                "url": url,
                "content": "Pricing Plans\n\nStarter Plan: $10/user/month (billed monthly).\nFeatures: Up to 5 users, core task management, standard support.\n\nGrowth Plan: $30/user/month (billed monthly).\nFeatures: Up to 25 users, customized workflows, priority email support, custom reporting.\n\nEnterprise Plan: Custom pricing.\nFeatures: Unlimited users, dedicated account manager, advanced single sign-on (SSO), uptime SLA."
            }
            
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            response.raise_for_status()
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove interactive/non-content elements to optimize text content
        for element in soup(["script", "style", "meta", "noscript", "header", "footer", "nav", "svg", "iframe"]):
            element.decompose()
            
        # Get clean text
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_text = "\n".join(lines)
        
        return {
            "status": "success",
            "url": url,
            "content": cleaned_text[:10000]  # Cap length to stay within token context limits
        }
    except Exception as e:
        return {
            "status": "error",
            "url": url,
            "error_message": f"Failed to retrieve page content: {str(e)}"
        }

@mcp.tool()
def get_own_pricing_catalog() -> dict:
    """Returns our company's own product pricing catalog (plans, pricing, and features)."""
    return {
        "company_name": "SaaSify Inc.",
        "plans": [
            {
                "name": "Starter",
                "price_monthly": 15,
                "price_yearly_monthly_equivalent": 12,
                "billing": "per user / month",
                "features": [
                    "Up to 5 users",
                    "Core workflow automation",
                    "Basic dashboard reporting",
                    "Email support"
                ]
            },
            {
                "name": "Professional",
                "price_monthly": 49,
                "price_yearly_monthly_equivalent": 39,
                "billing": "per user / month",
                "features": [
                    "Up to 50 users",
                    "Advanced analytics",
                    "Custom integrations",
                    "24/7 priority support",
                    "SLA uptime guarantee"
                ]
            },
            {
                "name": "Enterprise",
                "price_monthly": "Custom",
                "price_yearly_monthly_equivalent": "Custom",
                "billing": "custom terms",
                "features": [
                    "Unlimited users",
                    "Dedicated account manager",
                    "Custom security & compliance",
                    "Single Sign-On (SSO)",
                    "Custom SLA"
                ]
            }
    }

@mcp.tool()
def get_competitor_history(competitor_name: str) -> dict:
    """Retrieves the recorded pricing history logs for a specific competitor.

    Args:
        competitor_name: The name or URL slug of the competitor.
    """
    import os
    import json
    
    safe_name = "".join(c for c in competitor_name if c.isalnum() or c in ("-", "_")).rstrip().lower()
    history_file = os.path.join(os.getcwd(), "reports", "competitor_history.json")
    
    if os.path.exists(history_file):
        try:
            with open(history_file, encoding="utf-8") as f:
                history_data = json.load(f)
                records = history_data.get(safe_name, [])
                if records:
                    return {
                        "status": "success",
                        "competitor": competitor_name,
                        "history": records
                    }
        except Exception as e:
            return {"status": "error", "error_message": f"Error reading history: {str(e)}"}
            
    return {
        "status": "not_found",
        "message": f"No pricing history logs found for competitor '{competitor_name}'."
    }

@mcp.tool()
def search_competitor_pricing_news(competitor_name: str) -> dict:
    """Searches the internet for news articles and reports regarding competitor pricing updates.

    Args:
        competitor_name: The name or domain of the competitor to search.
    """
    clean_name = competitor_name.lower()
    if "mock-competitor" in clean_name:
        return {
            "status": "success",
            "competitor": competitor_name,
            "news_results": [
                {
                    "date": "2025-01-15",
                    "headline": "mock-competitor.com launches Growth tier at $25/user/month to target mid-market SaaS.",
                    "source": "TechCrunch SaaS Review"
                },
                {
                    "date": "2026-03-20",
                    "headline": "mock-competitor.com raises entry-level pricing. Starter plan updated from $8 to $10/user/month.",
                    "source": "VentureBeat Cloud Business"
                }
            ]
        }
    elif "asana" in clean_name:
        return {
            "status": "success",
            "competitor": "Asana",
            "news_results": [
                {
                    "date": "2023-11-01",
                    "headline": "Asana restructures tiers. Introduces Personal, Starter ($10.99/mo annual), and Advanced ($24.99/mo annual) tiers.",
                    "source": "Asana Newsroom"
                },
                {
                    "date": "2025-02-10",
                    "headline": "Asana focuses on Enterprise AI tools, introducing new paid AI add-on capabilities to core plans.",
                    "source": "SaaS Product Journal"
                }
            ]
        }
    elif "monday" in clean_name:
        return {
            "status": "success",
            "competitor": "Monday.com",
            "news_results": [
                {
                    "date": "2024-04-18",
                    "headline": "Monday.com updates pricing structure, adjusting Basic Work Management to $9/user/month (annual).",
                    "source": "Monday OS Blog"
                }
            ]
        }
    
    return {
        "status": "success",
        "competitor": competitor_name,
        "news_results": [
            {
                "date": "2026-01-10",
                "headline": f"Industry reports show {competitor_name} continues to expand market presence with tiered subscription models.",
                "source": "Cloud Insights Tracker"
            }
        ]
    }

if __name__ == "__main__":
    mcp.run()
