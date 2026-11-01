# AutoHeal Phase 8: AI SOC Copilot Architecture

## 1. Executive Overview

The **AI SOC Copilot** (`/soc-copilot`) is an intelligent, hallucination-resistant security investigation engine. Designed to act as a senior tier-3 security analyst assistant, the Copilot assists operational teams with:
- Rapid triage of confirmed and unconfirmed security incidents.
- Root cause analysis with mathematical confidence scoring.
- Rigorous separation of confirmed facts from investigative hypotheses.
- Actionable containment and remediation playbook recommendations.
- Automated generation of 12-section audit-ready incident reports.

```
+-----------------------------------------------------------------------------------------+
|                                AI SOC COPILOT ARCHITECTURE                              |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|   +-----------------------+     +------------------------+     +--------------------+   |
|   |  SOC Analyst Web UI   | <-> |  REST / Chat Endpoints | <-> | Copilot Pipeline   |   |
|   |  - Dual Chat Feed     |     |  /api/copilot/chat     |     | - Prompt Guard     |   |
|   |  - Findings Dossier   |     |  /api/copilot/invest.  |     | - Secret Redaction |   |
|   |  - Report Generator   |     |  /api/copilot/reports  |     | - Context Grounder |   |
|   +-----------------------+     +------------------------+     +--------------------+   |
|                                                                           │             |
|                                              ┌────────────────────────────┴────────┐    |
|                                              ▼                                     ▼    |
|                                  +-----------------------+             +----------------+
|                                  |   AIProviderManager   |             | Evidence       |
|                                  | - Dual-Mode Detection |             | Retriever      |
|                                  | - Gemini / OpenAI     |             | - 7 DB Sources |
|                                  | - Claude / Ollama     |             | - Citations    |
|                                  | - Grounded Fallback   |             | - MITRE ATT&CK |
|                                  +-----------------------+             +----------------+
+-----------------------------------------------------------------------------------------+
```

---

## 2. Core Engine Components

### 2.1 AIProviderManager
Manages connectivity to language models with zero simulation. If no remote LLM credentials are provided, it automatically engages the **Deterministic Grounded Analyst Engine**:
- Dynamically probes environment variables (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OLLAMA_BASE_URL`).
- Accurately reports provider status via `/api/copilot/provider-status` without faking external connectivity.
- Executes structured prompts against configured providers with streaming and retry resilience.

### 2.2 EvidenceRetriever
The grounding backbone of the Copilot. Queries 7 distinct database tables to assemble a complete forensic packet for any incident:
1. `security_incidents`: Title, category, severity, status, timestamps, affected scopes.
2. `security_events`: Raw HTTP request methods, paths, status codes, and timestamps.
3. `self_healing_executions`: Autonomous patches applied, verification results, rollback states.
4. `soar_executions`: Automated playbooks invoked, execution logs.
5. `blocked_clients`: Active firewall enforcements, expiration times.
6. `RULE_METADATA`: Canonical rule descriptions, CVEs, CWE references, and MITRE IDs.
7. `threat_intel`: Synthetic external intelligence telemetry (AbuseIPDB, VirusTotal, ASN).

### 2.3 CopilotInvestigationPipeline
Orchestrates end-to-end investigation workflows:
- Extracts chronological attack paths.
- Computes calibrated confidence scores ($0.0 \to 1.0$) using evidence volume and verification states.
- Generates 4-part structured dossiers:
  - **Tab 1: Confirmed Facts** (Empirically verified logs).
  - **Tab 2: Root Cause & Attack Path** (Vulnerability exploited and mechanics).
  - **Tab 3: Hypotheses & Inferences** (Speculative or secondary lateral possibilities).
  - **Tab 4: Recommended Next Steps** (SOAR playbooks and preventative code patches).

### 2.4 IncidentReportGenerator
Compiles audit-ready, 12-section formal incident reports persisted in Table 26 (`incident_reports`). Generates exportable JSON and printable HTML/PDF output with cryptographic audit hashes.

---

## 3. Session & State Management

Conversations are persisted in Table 25 (`soc_copilot_conversations`):
- Every interaction belongs to a `session_id` tied to an analyst ID and optional incident context.
- Conversation history preserves up to 50 message exchanges per session.
- Messages are sanitized and checked for secret leaks prior to SQLite insertion.

---

## 4. UI Dossier Tab Architecture

The Copilot findings panel organizes investigation results into 4 discrete tabs:

```
[ Tab 1: Confirmed Facts ]   [ Tab 2: Root Cause ]   [ Tab 3: Hypotheses ]   [ Tab 4: Playbooks ]
-------------------------------------------------------------------------------------------------
- Verified HTTP 403 on       - SQL Injection in      - Potential credential  - Execute SOAR
  /api/cart at 15:24:10        CartService via         spraying attempt        Playbook: Block IP
- Source IP: 198.51.100.99     product_id parameter    from adjacent /24       - Apply AST Patch
- Rule: SQLI-001 (High)      - Bypassed basic filter   subnet (Score: 0.65)      VULN-FIN-001
- Firewall Block: Active       prior to patch V3.2
```

This strict architectural separation prevents speculative AI assumptions from being misinterpreted as verified forensic findings by security leadership.
