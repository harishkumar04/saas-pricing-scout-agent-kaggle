# Changelog

All notable changes to this project will be documented in this file.

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
