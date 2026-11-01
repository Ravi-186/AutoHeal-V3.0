# AutoHeal v3.0 — Phase 5: Incident Reporting, Dossier Generation & CSV Export

## 1. Executive Summary

Enterprise compliance frameworks (NIST SP 800-61r2, SOC 2 Type II, ISO/IEC 27001, PCI-DSS v4.0) mandate rigorous documentation, chain-of-custody tracking, and export capabilities for all security incidents. The AutoHeal v3.0 Incident Command Center delivers automated reporting, cryptographic forensic dossiers, and formula-safe CSV streaming.

---

## 2. Formula-Safe CSV Export Subsystem

Spreadsheet software (Microsoft Excel, LibreOffice Calc, Google Sheets) is vulnerable to **Formula Injection (CSV Injection)** when opening CSV files containing untrusted user strings that begin with formula trigger characters (`=`, `+`, `-`, `@`, `\t`, `\r`).

### Sanitization Implementation:
When generating CSV output via `GET /api/security/incidents?format=csv`, all textual cell values are sanitized through RFC-4180 formula immunization:

```python
def sanitize_csv_cell(value: Any) -> str:
    """Escapes leading formula trigger characters to prevent CSV injection."""
    if value is None:
        return ""
    str_val = str(value)
    # Check if cell begins with dangerous spreadsheet formula triggers
    if str_val and str_val[0] in ("=", "+", "-", "@", "\t", "\r"):
        # Prefix with single quote (') to force text evaluation in Excel/Calc
        return "'" + str_val
    return str_val
```

### Response Headers:
```http
HTTP/1.1 200 OK
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="autoheal_incidents_20261101_143000.csv"
Cache-Control: no-cache, no-store, must-revalidate
```

---

## 3. Cryptographic JSON Forensic Dossier

For formal regulatory disclosures or external legal forensics, the platform exports a comprehensive **Incident Forensic Dossier**:

```json
{
  "dossier_version": "3.0.0",
  "generated_at": "2026-11-01T09:12:34Z",
  "incident_metadata": {
    "incident_id": "INC-20261101-AUTH-001",
    "title": "Suspected SQL Injection in Authentication Endpoint",
    "severity": "CRITICAL",
    "priority": "CRITICAL",
    "status": "RESOLVED",
    "category": "INJECTION",
    "version": 4
  },
  "cryptographic_integrity": {
    "evidence_sha256": "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
    "tamper_evident_status": "VALID",
    "hash_algorithm": "SHA-256"
  },
  "telemetry": {
    "rule_id": "RULE-SQLI-001",
    "target_endpoint": "POST /api/auth/login",
    "attacker_ip": "198.51.100.42",
    "related_events_count": 8
  },
  "root_cause_analysis": {
    "suspected_entry_point": "POST /api/auth/login [username]",
    "contributing_conditions": "Dynamic SQL concatenation",
    "analyst_conclusions": "Remediated via AST Virtual Patch #VP-2026-081"
  },
  "verification_audit": {
    "verification_status": "VERIFIED_CONTAINED",
    "attacker_probe_response": 403,
    "benign_probe_response": 200
  },
  "activity_trail": [
    {"action_type": "STATUS_CHANGED", "author": "System", "content": "Transitioned to NEW"},
    {"action_type": "ANALYST_ASSIGNED", "author": "analyst.lead@soc.corp", "content": "Assigned to Alex Rivera"}
  ]
}
```

---

## 4. Markdown Executive Briefings

Analysts can generate standardized Markdown reports directly from the UI:
- **Executive Summary:** Plain-language synopsis of the threat and business impact.
- **Incident Chronology:** Tabular breakdown of the timeline from initial breach to resolution.
- **Root Cause & Remediations:** Technical documentation of the root cause and implemented defenses.
- **Post-Incident Action Items:** Hardening tasks for software engineering teams.
