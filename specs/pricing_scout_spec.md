# BDD Specification: SaaS Pricing & Intelligence Scout

This document outlines the behavior-driven specifications and technical design of the **SaaS Pricing & Intelligence Scout** multi-agent system.

## 1. Technical Design Schema (YAML)

```yaml
system:
  name: saas-pricing-scout
  orchestration: Multi-Agent Delegation
  root_agent: coordinator_agent
  sub_agents:
    - scout_agent
    - analyst_agent
  environment:
    api_backend: Google AI Studio (Free Tier)
    default_model: gemini-3.5-flash
    gcp_fallback: Enabled

components:
  scout:
    allowed_tools:
      - fetch_web_page
    safety_callback: domain_safety_guard
  analyst:
    allowed_tools:
      - get_own_pricing_catalog
  coordinator:
    allowed_tools:
      - save_intelligence_report
      - export_pricing_strategy
    hil_gated_tools:
      - export_pricing_strategy
```

---

## 2. Behavior Scenarios (Gherkin Syntax)

### Feature: SaaS Competitive Pricing Intelligence
  As a Product Operations Manager
  I want to automatically analyze competitor pricing structures and compare them to our internal product catalogs
  So that we can identify gaps, calculate price differences, and export strategic pricing recommendations safely.

  Scenario: Analyze a safe competitor pricing page successfully
    Given the user provides a safe business domain URL "https://mock-competitor.com/pricing"
    When the coordinator_agent receives the request
    Then the coordinator_agent delegates execution to the scout_agent
    And the scout_agent fetches and extracts competitor pricing details using fetch_web_page
    And the scout_agent transfers control to the analyst_agent
    And the analyst_agent fetches the internal SaaS catalog using get_own_pricing_catalog
    And the analyst_agent calculates side-by-side differentials and feature gaps
    And the analyst_agent transfers control back to the coordinator_agent
    And the coordinator_agent compiles a Markdown report
    And the coordinator_agent automatically calls save_intelligence_report to save the file
    And the coordinator_agent presents the report to the user and offers to export recommendations

  Scenario: Blocked social media domain requests
    Given the user requests an analysis of "https://facebook.com/pricing-plans"
    When the scout_agent attempts to invoke fetch_web_page
    Then the domain_safety_guard callback intercepts the call
    And the domain is identified as social media (blacklisted in policies.yaml)
    And the callback blocks the tool execution and returns a "Security Guardrail" error
    And the coordinator_agent communicates the safety violation back to the user

  Scenario: Blocked untrusted TLD requests
    Given the user requests an analysis of "https://malicious-scam.xyz/plans"
    When the scout_agent attempts to invoke fetch_web_page
    Then the domain_safety_guard callback intercepts the call
    And the TLD is identified as untrusted (".xyz" is blacklisted in policies.yaml)
    And the callback blocks the tool execution and returns a "Security Guardrail" error
    And the coordinator_agent communicates the safety violation back to the user

  Scenario: Blocked non-HTTP URL scheme requests
    Given the user requests an analysis of "ftp://competitor.com/pricing.html"
    When the scout_agent attempts to invoke fetch_web_page
    Then the domain_safety_guard callback intercepts the call
    And the scheme "ftp" is identified as not allowed (only http/https allowed)
    And the callback blocks the tool execution and returns a "Security Guardrail" error
    And the coordinator_agent communicates the safety violation back to the user
