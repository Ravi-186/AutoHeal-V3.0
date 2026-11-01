# SOAR Node Type Reference Catalog

**Document ID:** NODE-CATALOG-001  
**Version:** 3.0.0  
**Phase:** 6 — Enterprise Security Orchestration, Automation, and Response  
**Security Classification:** Enterprise SOC Internal  
**Design Identity:** Obsidian Sentinel

---

## 1. Overview

The AutoHeal Visual SOAR Automation Builder provides 28 modular node types grouped across seven architectural categories:
1. **Triggers:** Entry points responding to system events, alerts, or analyst action.
2. **Lookups / Enrichment:** Context gathering from incidents, threat intelligence, and user directories.
3. **Conditions:** Parameterized logical tests evaluating execution context variables.
4. **Branches:** Directed routing points splitting execution into distinct downstream paths.
5. **Approvals:** Human-in-the-loop security checkpoints requiring operator authorization.
6. **Actions:** Automated response and containment operations executed on perimeter and host.
7. **Verifications:** Closed-loop active validation testing containment integrity.

---

## 2. Category 1: Triggers (Cyan `#38BDF8`)

| Node Type ID | Label | Description | Default Configuration | Outbound Handles |
| :--- | :--- | :--- | :--- | :--- |
| `trigger_incident` | New Incident Trigger | Fires when a security incident matching criteria is escalated. | `{"category": "ALL", "min_severity": "MEDIUM"}` | `["output"]` |
| `trigger_security_event` | Security Event Ingest | Fires upon ingestion of raw HTTP security event. | `{"event_type": "ALL", "severity": "ALL"}` | `["output"]` |
| `trigger_severity_change` | Severity Escalated | Fires when an existing incident's severity is increased. | `{"target_severity": "CRITICAL"}` | `["output"]` |
| `trigger_rule_matched` | Detection Rule Match | Fires when a specific AppSec detection rule is triggered. | `{"rule_id": "INJ-001"}` | `["output"]` |
| `trigger_manual` | Manual Analyst Ingress | Triggered on-demand by SOC analyst from Command Center. | `{}` | `["output"]` |

---

## 3. Category 2: Lookups & Enrichment (Sky `#0284C7`)

| Node Type ID | Label | Description | Execution Behavior | Outbound Handles |
| :--- | :--- | :--- | :--- | :--- |
| `lookup_incident` | Fetch Incident Dossier | Retrieves full SQLite record from `security_incidents`. | Loads evidence, timeline, and indicators into `context["incident"]`. | `["output"]` |
| `lookup_ip_info` | Attacker IP Enrichment | Enriches client IP with internal threat reputation score. | Populates `context["ip_reputation"]`. | `["output"]` |
| `lookup_user` | Query User Record | Inspects ShopSphere customer account status and role. | Loads user record into `context["user"]`. | `["output"]` |
| `lookup_threat_intel` | Threat Intel Feeds | Queries integrated indicators of compromise (IOCs). | Appends reputation tags to `context`. | `["output"]` |
| `lookup_evidence` | Tamper-Evident Hash | Generates SHA-256 integrity digest over incident evidence. | Validates non-repudiation of forensics. | `["output"]` |

---

## 4. Category 3: Conditions (Amber `#F59E0B`)

| Node Type ID | Label | Evaluated Fields | Supported Operators | Output Variable |
| :--- | :--- | :--- | :--- | :--- |
| `condition_severity` | Severity Evaluator | `incident.severity` | `EQUALS`, `IN_LIST`, `GREATER_EQUAL` | `context.execution_vars.last_condition` |
| `condition_category` | Category Filter | `incident.category` | `EQUALS`, `NOT_EQUALS`, `IN_LIST` | `context.execution_vars.last_condition` |
| `condition_ip` | IP Address Matcher | `source_ip` | `EQUALS`, `NOT_EQUALS`, `CIDR_MATCH` | `context.execution_vars.last_condition` |
| `condition_status` | Status Check | `incident.status` | `EQUALS`, `IN_LIST` | `context.execution_vars.last_condition` |
| `condition_confidence` | AI Confidence Gate | `incident.confidence` | `GREATER_EQUAL` (e.g. `>= 0.85`) | `context.execution_vars.last_condition` |
| `condition_expression` | General Expression | Configurable field | `EQUALS`, `NOT_EQUALS`, `CONTAINS` | `context.execution_vars.last_condition` |

---

## 5. Category 4: Branches (Pink `#EC4899`)

| Node Type ID | Label | Description | Outbound Routing Handles |
| :--- | :--- | :--- | :--- |
| `branch_if_else` | If / Else Branch | Evaluates preceding condition boolean result. | `["true", "false"]` |
| `branch_multi` | Multi-Way Switch | Routes based on incident category or threat score. | `["branch_1", "branch_2", "default"]` |
| `branch_success_failure` | Execution Gate | Splits based on whether previous action succeeded. | `["success", "failure"]` |
| `branch_approval` | Approval Gate Route | Directs flow based on human approval decision. | `["approved", "rejected"]` |

---

## 6. Category 5: Approvals (Yellow `#EAB308`)

| Node Type ID | Label | Approver Role | Execution Pause Behavior | Single-Use Token |
| :--- | :--- | :--- | :--- | :--- |
| `approval_analyst` | Analyst Approval Gate | `soc:analyst` | Pauses workflow, creates row in `soar_approvals`. | Cryptographic token generated. |
| `approval_admin` | Admin Authorization | `soc:admin` | Pauses execution for system administrator sign-off. | Cryptographic token generated. |
| `approval_high_impact` | High-Impact Action Review | `soc:lead` | Enforces mandatory justification and review. | Cryptographic token generated. |

---

## 7. Category 6: Response Actions (Red `#EF4444`)

| Node Type ID | Label | Target Subsystem | Action Effect | Reversible |
| :--- | :--- | :--- | :--- | :--- |
| `action_block_ip` | Dynamic IP Quarantine | `AppSecProtectionMiddleware` | Inserts IP into `blocked_clients` table for specified duration. | Yes (`action_unblock_ip`) |
| `action_unblock_ip` | Release IP Quarantine | `AppSecProtectionMiddleware` | Removes IP from `blocked_clients` table. | N/A |
| `action_revoke_session` | Revoke User Session | `ShopSphere UserService` | Clears active token and expiry in `users` table. | No (requires re-login) |
| `action_disable_account` | Lockout Account | `ShopSphere UserService` | Sets user status to disabled/locked. | Yes |
| `action_apply_rate_limit`| Adaptive Rate-Limiting | `AppSecProtectionMiddleware` | Throttles IP requests to threshold requests/second. | Yes (time-decayed) |
| `action_create_incident` | Escalate New Incident | `security_incidents` | Inserts formal incident record into SQLite. | N/A |
| `action_add_note` | Add Incident Note | `incident_activity_log` | Appends forensic note signed by SOAR bot. | Append-only |
| `action_assign_incident` | Assign Incident Lead | `security_incidents` | Assigns analyst lead to active incident. | Yes |
| `action_notify_analyst` | Dispatch SOC Alert | `soar_audit_logs` | Logs high-priority alert in SOC notifications. | Immutable |
| `action_generate_report` | Generate Incident Report| Forensic Exporter | Compiles JSON/PDF incident dossier. | N/A |

---

## 8. Category 7: Verifications (Emerald `#10B981`)

| Node Type ID | Label | Verification Mechanism | Success Criteria |
| :--- | :--- | :--- | :--- |
| `verify_ip_blocked` | Verify Perimeter Block | Probes `is_client_blocked(ip)` | Client blocked status == True (HTTP 403) |
| `verify_session_revoked` | Verify Session Invalidation | Looks up session token in DB | Session token == NULL |
| `verify_account_disabled` | Verify Account Lockout | Checks account status in DB | Account status == DISABLED |
| `verify_rate_limited` | Verify Rate Limiter Active | Probes rate tracker | Requests above limit blocked |
| `verify_benign_traffic` | Verify Shopper Availability | HTTP GET `/api/shop/products` | Status == 200 OK & Latency < 50ms |
| `verify_remediation_outcome` | Closed-Loop Remediation | Dual-probe via `AppSecVerifier` | Adversary 403 AND Benign 200 |
