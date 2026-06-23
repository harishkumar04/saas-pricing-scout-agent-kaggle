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

def save_intelligence_report(report_markdown: str, competitor_name: str, plans_list: list = None, domain: str = None) -> dict:
    """Saves the competitive intelligence report to a local markdown file, updates the SQLite database, and tracks versions.

    Args:
        report_markdown: The markdown content of the generated report.
        competitor_name: The name or slug of the competitor.
        plans_list: Optional list of dictionaries representing the scraped competitor plans.
                    E.g., [{'name': 'Starter', 'price_monthly': 10}, ...]
        domain: Optional competitor website domain URL.

    Returns:
        A dictionary containing the status, path of the saved report, and version tracking info.
    """
    try:
        import os
        import json
        import datetime
        import hashlib
        import sqlite3

        # Create reports directory in the project root if it doesn't exist
        reports_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Initialize SQLite database
        db_path = os.path.join(reports_dir, "competitor_pricing.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            domain TEXT NOT NULL,
            last_checked_at TEXT NOT NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pricing_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER NOT NULL,
            version_hash TEXT NOT NULL,
            plans_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(competitor_id) REFERENCES competitors(id)
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER NOT NULL,
            version_id INTEGER NOT NULL,
            filepath TEXT NOT NULL,
            report_markdown TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(competitor_id) REFERENCES competitors(id),
            FOREIGN KEY(version_id) REFERENCES pricing_versions(id)
        );
        """)
        conn.commit()

        # Clean competitor name for key
        safe_name = "".join(c for c in competitor_name if c.isalnum() or c in ("-", "_")).rstrip()
        competitor_key = safe_name.lower()
        if not domain:
            domain = f"https://{competitor_key}.com"

        now_str = datetime.datetime.now().isoformat()

        # Insert or update competitor check time
        cursor.execute("SELECT id FROM competitors WHERE name = ?", (competitor_key,))
        comp_row = cursor.fetchone()
        if comp_row:
            competitor_id = comp_row[0]
            cursor.execute("UPDATE competitors SET last_checked_at = ?, domain = ? WHERE id = ?", (now_str, domain, competitor_id))
        else:
            cursor.execute("INSERT INTO competitors (name, domain, last_checked_at) VALUES (?, ?, ?)", (competitor_key, domain, now_str))
            competitor_id = cursor.lastrowid
        conn.commit()

        # Compute version hash based on plans
        if plans_list:
            # Sort plans by name to prevent order/dict key ordering changes from changing the hash
            sorted_plans = sorted(plans_list, key=lambda x: str(x.get("name", "")))
            plans_str = json.dumps(sorted_plans, sort_keys=True)
        else:
            # Fallback to hashing the report content
            plans_str = report_markdown
        version_hash = hashlib.md5(plans_str.encode("utf-8")).hexdigest()

        # Check latest version for this competitor to see if pricing changed
        cursor.execute("""
        SELECT id, version_hash FROM pricing_versions 
        WHERE competitor_id = ? 
        ORDER BY id DESC LIMIT 1
        """, (competitor_id,))
        version_row = cursor.fetchone()

        plans_json_str = json.dumps(plans_list) if plans_list else "[]"

        if version_row and version_row[1] == version_hash:
            version_id = version_row[0]
            pricing_changed = False
        else:
            cursor.execute("""
            INSERT INTO pricing_versions (competitor_id, version_hash, plans_json, created_at)
            VALUES (?, ?, ?, ?)
            """, (competitor_id, version_hash, plans_json_str, now_str))
            version_id = cursor.lastrowid
            conn.commit()
            pricing_changed = True

        # Organize files month-wise
        now = datetime.datetime.now()
        year_month = now.strftime("%Y-%m")
        date_str = now.strftime("%Y%m%d")

        month_dir = os.path.join(reports_dir, year_month)
        os.makedirs(month_dir, exist_ok=True)

        filename = f"pricing_scout_{competitor_key}_{date_str}_v{version_id}.md"
        filepath = os.path.join(month_dir, filename)

        # Write markdown file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_markdown)

        # Insert report entry
        cursor.execute("""
        INSERT INTO reports (competitor_id, version_id, filepath, report_markdown, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (competitor_id, version_id, filepath, report_markdown, now_str))
        conn.commit()
        conn.close()

        status_msg = f"Logged pricing changes (Version {version_id}) and saved report." if pricing_changed else f"Pricing unchanged (Version {version_id}). Logged run and saved report."

        return {
            "status": "success",
            "message": f"Successfully saved intelligence report to {filepath}. {status_msg}",
            "filepath": filepath,
            "version_id": version_id,
            "pricing_changed": pricing_changed
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to save report to database: {str(e)}"
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
    """Sends a real Slack webhook alert notification of competitor pricing changes.

    Args:
        competitor_name: The name of the competitor analyzed.
        brief_summary: A short, 1-2 sentence summary of pricing updates or insights.

    Returns:
        A dictionary containing the Slack webhook status.
    """
    import os
    import httpx

    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return {
            "status": "error",
            "error_message": "Slack Webhook URL is not configured in the environment. Please add SLACK_WEBHOOK_URL to your app/.env file."
        }

    try:
        payload = {
            "text": f"🚨 *Competitor Pricing Alert* 🚨\n*Competitor:* {competitor_name}\n*Summary:* {brief_summary}"
        }
        with httpx.Client(timeout=10.0) as client:
            response = client.post(webhook_url, json=payload)
            response.raise_for_status()
            
        return {
            "status": "success",
            "message": f"Successfully sent Slack notification alert for {competitor_name} to channel.",
            "channel": "#marketing-pricing-alerts"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to post Slack notification: {str(e)}"
        }
