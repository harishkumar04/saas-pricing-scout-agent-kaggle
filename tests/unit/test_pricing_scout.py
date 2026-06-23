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
import sqlite3
import pytest
from unittest.mock import MagicMock

from app.safety import PolicyService
from app.tools import save_intelligence_report, export_pricing_strategy
from app.mcp_server import query_pricing_db, generate_history_chart

def test_policy_service_tool_permissions():
    """Tests that tools are correctly allowed or blocked based on agent roles."""
    service = PolicyService()
    
    # Scout agent allowed tools
    assert service.is_tool_allowed("scout_agent", "fetch_web_page") is True
    assert service.is_tool_allowed("scout_agent", "save_intelligence_report") is False
    
    # Analyst agent allowed tools
    assert service.is_tool_allowed("analyst_agent", "get_own_pricing_catalog") is True
    assert service.is_tool_allowed("analyst_agent", "export_pricing_strategy") is False
    
    # Coordinator agent allowed tools
    assert service.is_tool_allowed("coordinator_agent", "save_intelligence_report") is True
    assert service.is_tool_allowed("coordinator_agent", "fetch_web_page") is False

def test_policy_service_context_resolution():
    """Tests that bracketed placeholders are resolved correctly from env or state."""
    service = PolicyService()
    os.environ["TEST_ENV_VAR"] = "env_value"
    
    # Resolve from override state
    result_state = service.resolve_context("Hello [[NAME]]", {"NAME": "Alice"})
    assert result_state == "Hello Alice"
    
    # Resolve from environment variable
    result_env = service.resolve_context("Server: [[TEST_ENV_VAR]]")
    assert result_env == "Server: env_value"
    
    # Unresolved variables are preserved
    result_unresolved = service.resolve_context("Key [[UNRESOLVED_VAR]]")
    assert result_unresolved == "Key [[UNRESOLVED_VAR]]"

def test_policy_service_validation(monkeypatch):
    """Tests that fetch_web_page calls are validated against domain safety rules."""
    service = PolicyService()
    
    # Setup mock BaseTool and ToolContext
    mock_tool = MagicMock()
    mock_tool.name = "fetch_web_page"
    
    mock_context = MagicMock()
    mock_context.agent_name = "scout_agent"
    mock_context.state = {}
    
    # Allowed URL
    args = {"url": "https://trusted-competitor.com/pricing"}
    assert service.validate_tool_call(mock_tool, args, mock_context) is None
    
    # Blocked Social Media domain
    args_blocked_domain = {"url": "https://facebook.com/pricing"}
    res = service.validate_tool_call(mock_tool, args_blocked_domain, mock_context)
    assert res is not None
    assert res["status"] == "blocked"
    assert "social network" in res["error_message"]
    
    # Blocked suspicious TLD
    args_blocked_tld = {"url": "https://competitor.xyz/pricing"}
    res_tld = service.validate_tool_call(mock_tool, args_blocked_tld, mock_context)
    assert res_tld is not None
    assert res_tld["status"] == "blocked"
    assert "Top-level domain" in res_tld["error_message"]

def test_save_report_sqlite_integration(tmp_path, monkeypatch):
    """Verifies save_intelligence_report correctly records data in SQLite and tracks versions."""
    # Monkeypatch os.getcwd to redirect reports to tmp_path
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))
    
    competitor = "CompetitorOne"
    plans = [
        {"name": "Basic", "price_monthly": 19},
        {"name": "Plus", "price_monthly": 49}
    ]
    report_md = "# Intelligence Report for CompetitorOne"
    
    # First save (Version 1)
    res1 = save_intelligence_report(report_md, competitor, plans_list=plans)
    assert res1["status"] == "success"
    assert res1["version_id"] == 1
    assert res1["pricing_changed"] is True
    
    # Verify file saved
    assert os.path.exists(res1["filepath"])
    
    # Second save with identical plans (should NOT create a new version)
    res2 = save_intelligence_report(report_md, competitor, plans_list=plans)
    assert res2["status"] == "success"
    assert res2["version_id"] == 1
    assert res2["pricing_changed"] is False
    
    # Third save with modified plans (should create Version 2)
    modified_plans = [
        {"name": "Basic", "price_monthly": 24}, # Price changed from 19 to 24
        {"name": "Plus", "price_monthly": 49}
    ]
    res3 = save_intelligence_report(report_md, competitor, plans_list=modified_plans)
    assert res3["status"] == "success"
    assert res3["version_id"] == 2
    assert res3["pricing_changed"] is True
    
    # Verify SQLite database contains the records
    db_path = os.path.join(str(tmp_path), "reports", "competitor_pricing.db")
    assert os.path.exists(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM competitors")
    comps = cursor.fetchall()
    assert comps == [("competitorone",)]
    
    cursor.execute("SELECT id, version_hash FROM pricing_versions ORDER BY id ASC")
    versions = cursor.fetchall()
    assert len(versions) == 2
    
    cursor.execute("SELECT filepath FROM reports")
    reports_logged = cursor.fetchall()
    assert len(reports_logged) == 3
    conn.close()

def test_query_pricing_db_and_mermaid_chart(tmp_path, monkeypatch):
    """Tests db query and mermaid chart generation tool logic."""
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))
    
    competitor = "CompetitorTwo"
    plans = [{"name": "Standard", "price_monthly": 29}]
    report_md = "# Intelligence Report for CompetitorTwo"
    
    # Pre-populate SQLite db using save_intelligence_report
    save_intelligence_report(report_md, competitor, plans_list=plans)
    
    # Query database
    query_res = query_pricing_db(competitor)
    assert query_res["status"] == "success"
    assert query_res["competitor"] == "competitortwo"
    assert len(query_res["pricing_versions"]) == 1
    assert query_res["pricing_versions"][0]["plans"] == plans
    
    # Generate history chart
    chart_res = generate_history_chart(competitor)
    assert chart_res["status"] == "success"
    assert "mermaid" in chart_res["mermaid_chart"]
    assert "V1" in chart_res["mermaid_chart"]
    assert "Standard: $29" in chart_res["mermaid_chart"]
