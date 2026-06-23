# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0] - 2026-06-23

### Added
- **Local SQLite Competitor Database**: Implemented an SQLite-backed audit registry (`reports/competitor_pricing.db`) to record pricing plans, track version variations using MD5 hashes, and maintain generated report file paths.
- **db_analyst_agent**: Created a new sub-agent equipped with `query_pricing_db` and `generate_history_chart` tools to extract competitor logs and compile visual Mermaid-based price-history charts.
- **Comprehensive Unit Tests**: Introduced `tests/unit/test_pricing_scout.py` containing unit test cases to verify role gating policies, context hygiene resolution, SQLite schema initialization, and version-tracking hashes.

### Changed
- **app/tools.py**: Restructured `save_intelligence_report` to save generated reports under monthly folders (`reports/YYYY-MM/`) and log versioned structures to the SQLite database.
- **app/policies.yaml**: Granted tool permissions to the new `db_analyst_agent`.

## [0.2.0] - 2026-06-21

### Added
- **AGENTS.md**: Added standard coding rules, project guidelines, and the "one-line mental model" for AI agents.
- **BDD Specification**: Created Behavior-Driven Development specification in `specs/pricing_scout_spec.md` detailing Given/When/Then scenarios and a YAML architecture schema.
- **policies.yaml**: Created a declarative policy configuration mapping allowed tools and domain safety blocklists.
- **CHANGELOG.md**: Initialized the changelog repository.

### Changed
- **app/safety.py**: Refactored to implement the `PolicyService` Policy Server pattern and introduced `resolve_context` middleware to perform automated Context Hygiene (resolving `[[VARIABLE_NAME]]` placeholders).
- **app/agent.py**: Configured safety callbacks globally on all agents to ensure role-based tool restrictions and context hygiene are applied to all tool invocations.

### Fixed
- **Sub-Agent Handoffs**: Refined prompts for `scout_agent` and `analyst_agent` to ensure clean transitions via the `transfer_to_agent` tool.
- **CLI Eval Trace Parser**: Patched the local `_inference_runner.py` trace parser to correctly handle cases where the Vertex AI Evaluation SDK returns `agent_data` as a serialized JSON string.
