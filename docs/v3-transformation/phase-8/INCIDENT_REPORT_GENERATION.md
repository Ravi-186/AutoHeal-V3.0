# AutoHeal Phase 8: Incident Report Generation Standard

## 1. Overview

The AutoHeal **Incident Report Generator** compiles comprehensive, executive- and audit-ready post-incident reports. Designed to satisfy compliance standards (SOC 2, ISO 27001, PCI-DSS 4.0), the generator automates the tedious task of documenting attack vectors, affected assets, autonomous remediations, root causes, and verification proofs.

Reports are persisted in Table 26 (`incident_reports`) and can be exported as structured JSON, formatted Markdown, or printable PDF documents.

---

## 2. The 12-Section Formal Incident Report Standard

Every generated report adheres to the following 12-section structure:

| Section # | Title | Purpose & Content |
| :---: | :--- | :--- |
| **1** | **Report Header & Audit Metadata** | Report ID (`REP-YYYYMMDD-...`), Classification, Generated Date, Author |
| **2** | **Executive Summary** | Non-technical executive summary for C-suite and leadership |
| **3** | **Incident Identification & Scope** | Incident ID, Rule ID, Severity, Status, Affected endpoints and databases |
| **4** | **Chronological Attack Timeline** | Granular second-by-second timeline of reconnaissance, probe, and exploit |
| **5** | **Attack Vector & Technical Mechanics** | HTTP methods, malicious payload strings, parameters targeted |
| **6** | **Root Cause Analysis (Facts vs Hypotheses)** | Strict demarcation between empirically verified facts and analytical hypotheses |
| **7** | **Threat Intelligence & Attribution** | AbuseIPDB reputation, ASN, Geolocation, MITRE ATT&CK tactic/technique |
| **8** | **Containment & Remediation Actions** | Firewall blocks, code patches applied, AST modifications, SOAR playbooks |
| **9** | **Independent Verification & Health** | Post-heal test suite execution, probe results, regression validation |
| **10**| **Preventative Recommendations** | Long-term code hardening, architectural controls, and playbook rules |
| **11**| **Regulatory & Compliance Impact** | Assessment of data exfiltration risk under GDPR, CCPA, and PCI-DSS |
| **12**| **Cryptographic Sign-Off & Audit Hash** | SHA256 integrity hash of raw evidence, sign-off status, audit signature |

---

## 3. Database Persistence (Table 26: `incident_reports`)

Reports are formally stored in SQLite for auditing and legal discovery:

```sql
CREATE TABLE IF NOT EXISTS incident_reports (
    report_id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    author TEXT DEFAULT 'AutoHeal AI SOC Copilot',
    title TEXT NOT NULL,
    status TEXT DEFAULT 'DRAFT', -- DRAFT, REVIEWED, APPROVED, ARCHIVED
    executive_summary TEXT NOT NULL,
    report_data_json TEXT NOT NULL, -- Full 12-section JSON payload
    compliance_tags_json TEXT DEFAULT '["SOC2","PCI-DSS","ISO27001"]',
    sign_off_analyst TEXT,
    sign_off_timestamp TIMESTAMP,
    audit_hash TEXT NOT NULL,
    FOREIGN KEY(incident_id) REFERENCES security_incidents(incident_id)
);
```

---

## 4. Report Generation Workflow

### 4.1 Triggering via REST API
```bash
curl -X POST "http://localhost:8000/api/copilot/reports/generate?incident_id=INC-1004&author=Lead%20Analyst"
```

### 4.2 Programmatic Generation in Python
```python
from src.appsec.copilot_engine import IncidentReportGenerator

generator = IncidentReportGenerator()
report = generator.generate_report(incident_id="INC-1004", author="Lead SOC Analyst")

print(f"Generated report: {report['report_id']}")
print(f"Audit Hash: {report['audit_metadata']['audit_hash']}")
```

---

## 5. Export Formats

1. **Structured JSON**: Machine-readable format suitable for SIEM/SOAR archival or downstream ticketing (Jira, ServiceNow).
2. **Markdown**: Standard format with GitHub Flavored Markdown tables and alert blocks, optimized for developer wiki documentation.
3. **Printable HTML / PDF**: Rendered in the browser with custom `@media print` stylesheets adhering to the Obsidian Sentinel corporate visual identity.
