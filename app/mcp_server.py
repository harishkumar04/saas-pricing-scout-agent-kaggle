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
        ]
    }

if __name__ == "__main__":
    mcp.run()
