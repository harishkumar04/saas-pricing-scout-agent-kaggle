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

def save_intelligence_report(report_markdown: str, competitor_name: str) -> dict:
    """Saves the competitive intelligence report to a local markdown file and appends it to JSON history.

    Args:
        report_markdown: The markdown content of the generated report.
        competitor_name: The name or slug of the competitor (used to name the file).

    Returns:
        A dictionary containing the status and the path of the saved report.
    """
    try:
        import json
        import datetime

        # Create reports directory in the project root if it doesn't exist
        reports_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Clean the competitor name for a safe filename
        safe_name = "".join(c for c in competitor_name if c.isalnum() or c in ("-", "_")).rstrip()
        filename = f"pricing_scout_{safe_name.lower()}.md"
        filepath = os.path.join(reports_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_markdown)

        # Log entry to JSON history file for historical tracking
        history_file = os.path.join(reports_dir, "competitor_history.json")
        history_data = {}
        if os.path.exists(history_file):
            try:
                with open(history_file, encoding="utf-8") as hf:
                    history_data = json.load(hf)
            except Exception:
                pass

        competitor_key = safe_name.lower()
        if competitor_key not in history_data:
            history_data[competitor_key] = []

        history_data[competitor_key].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "report_markdown": report_markdown
        })

        with open(history_file, "w", encoding="utf-8") as hf:
            json.dump(history_data, hf, indent=2)
            
        return {
            "status": "success",
            "message": f"Successfully saved intelligence report to {filepath} and logged to history.",
            "filepath": filepath
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to save report: {str(e)}"
        }

def export_pricing_strategy(recommended_tiers: list) -> dict:
    """Simulates exporting the recommended strategic pricing tiers to the production catalog.
    
    WARNING: This is a sensitive action that updates active product pricing structures.

    Args:
        recommended_tiers: A list of dictionaries representing the recommended new/updated plans.
                           Each dict should contain 'name', 'price_monthly', and 'features'.

    Returns:
        A dictionary containing the export status.
    """
    try:
        # Simulate active database modification
        updated_plans = []
        for tier in recommended_tiers:
            name = tier.get("name")
            price = tier.get("price_monthly")
            if not name or price is None:
                raise ValueError("Each tier must have a 'name' and 'price_monthly' specified.")
            updated_plans.append(name)
            
        return {
            "status": "success",
            "message": f"Successfully exported updated pricing strategy to production for plans: {', '.join(updated_plans)}.",
            "plans_exported": recommended_tiers
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Export failed: {str(e)}"
        }

def post_slack_notification(competitor_name: str, brief_summary: str) -> dict:
    """Simulates sending a Slack webhook alert notification of competitor pricing changes.

    Args:
        competitor_name: The name of the competitor analyzed.
        brief_summary: A short, 1-2 sentence summary of pricing updates or insights.

    Returns:
        A dictionary containing the Slack webhook status.
    """
    print(f"\n[SLACK NOTIFICATION] Alert posted for competitor: {competitor_name}")
    print(f"[SLACK NOTIFICATION] Summary: {brief_summary}\n")
    return {
        "status": "success",
        "message": f"Successfully posted Slack notification alert for {competitor_name}.",
        "channel": "#marketing-pricing-alerts"
    }
