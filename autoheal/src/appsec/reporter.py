import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from src.appsec.models import get_security_incident, get_security_events, redact_sensitive_data
from src.appsec.pdf_generator import IncidentPDFGenerator


class AppSecReporter:
    """Generates forensic incident dossiers and audit reports in JSON, PDF, Markdown, and CSV formats."""

    @classmethod
    def generate_pdf_report(cls, incident_id: str) -> Optional[bytes]:
        """Produces a downloadable, formatted binary PDF incident report."""
        inc = get_security_incident(incident_id)
        if not inc:
            return None
        related_events = get_security_events(limit=10, client_ip=inc.get("source_ip"))
        return IncidentPDFGenerator.generate_pdf_report(inc, related_events)

    @classmethod
    def generate_markdown_report(cls, incident_id: str) -> str:
        """Produces a comprehensive forensic incident report in GitHub Flavored Markdown."""
        inc = get_security_incident(incident_id)
        if not inc:
            return f"# Incident Report: {incident_id}\n\n*Error: Incident not found in forensic database.*"

        created_at = inc.get("created_at", "Unknown")
        updated_at = inc.get("updated_at", created_at)
        rule_id = inc.get("rule_id", "POLICY-001")
        category = inc.get("category", "General Security")
        severity = inc.get("severity", "MEDIUM")
        status = inc.get("status", "OPEN")
        confidence = inc.get("confidence", 1.0)
        source_ip = inc.get("source_ip", "127.0.0.1")
        summary = inc.get("summary", "Security event recorded.")
        impact_actual = inc.get("impact_actual", "No verified impact.")
        impact_potential = inc.get("impact_potential", "Potential service compromise.")
        verif_status = inc.get("verification_status", "PENDING")
        remediation_details = inc.get("remediation_details", "No remediation details recorded.")

        evidence = inc.get("evidence", {})
        evidence_str = json.dumps(redact_sensitive_data(evidence), indent=2)
        mitigation_actions = inc.get("mitigation_actions", [])
        actions_str = json.dumps(mitigation_actions, indent=2)

        # AI Advisor & MITRE ATT&CK Enrichment
        from src.appsec.ai_advisor import AISecurityAdvisor
        mitre = AISecurityAdvisor.get_mitre_mapping(rule_id)
        target_ep = inc.get("target_endpoint") or (inc.get("affected_endpoints") or ["/api/shop"])[0]
        ai_analysis = AISecurityAdvisor.generate_grounded_summary(
            incident_id=incident_id,
            rule_id=rule_id,
            category=category,
            severity=severity,
            endpoint=target_ep,
            source_ip=source_ip,
            evidence=evidence
        )

        # Related events for timeline
        related_events = get_security_events(limit=10, client_ip=source_ip)
        timeline_rows = []
        for e in related_events:
            timeline_rows.append(f"| {e.get('timestamp')} | `{e.get('method')} {e.get('path')}` | {e.get('status_code')} | `{e.get('event_type')}` | **{e.get('action_taken')}** |")
        timeline_table = "\n".join(timeline_rows) if timeline_rows else "| *No historical telemetry recorded* | | | | |"

        recs_list = "\n".join(f"{idx+1}. {r}" for idx, r in enumerate(ai_analysis["remediation_plan"]))

        md = f"""# 🛡️ AutoHeal Forensic Incident Report
**Incident ID**: `{incident_id}`  
**Classification**: **{category}** ({rule_id})  
**Severity**: `{severity}` | **Confidence**: `{confidence * 100:.1f}%`  
**Current Status**: **{status}** | **Verification State**: `{verif_status}`  
**MITRE ATT&CK**: `{mitre['technique_id']} - {mitre['technique_name']}`  
**Generated At**: `{datetime.now(timezone.utc).isoformat()} (UTC)`

---

## 1. Executive Summary & Impact
{summary}

- **Observed Source IP**: `{source_ip}`
- **Target Endpoint**: `{target_ep}`
- **First Detected**: `{created_at}`
- **Last Updated**: `{updated_at}`
- **Actual Impact**: {impact_actual}
- **Potential Impact**: {impact_potential}

---

## 2. MITRE ATT&CK Enterprise Matrix Alignment
- **Tactic**: **{mitre['tactic_name']}** (`{mitre['tactic_id']}`)
- **Technique**: **{mitre['technique_name']}** (`{mitre['technique_id']}`)
- **Sub-Technique**: {mitre.get('subtechnique', 'N/A')}
- **CWE Weakness**: `{mitre.get('cwe_id', 'CWE-200')}`
- **NIST CSF Mapping**: `{mitre.get('nist_mapping', 'SI-4')}`
- **Threat Actor Objective**: {mitre.get('threat_actor_objective', 'Application probing')}

---

## 3. AI-Assisted Incident Analysis & Root Cause
{ai_analysis['executive_summary']}

**Root Cause Diagnosis**:
> {ai_analysis['root_cause_analysis']}

---

## 4. Detection Rule & Evidence Dossier
- **Rule Identifier**: `{rule_id}`
- **Detection Engine**: `AutoHeal AppSec Rule & Correlation Engine v1.0`
- **Why Flagged**: Automated pattern matching and request-level telemetry anomaly detection.

```json
{evidence_str}
```

---

## 5. AutoHeal Response & Mitigation Execution
The defensive policy engine executed the following containment and quarantine actions:

```json
{actions_str}
```

- **Remediation Result**: {remediation_details}
- **Autonomous Verification**: **{verif_status}**

---

## 6. Telemetry Event Timeline
| Timestamp (UTC) | Endpoint | Status | Event Type | Action Taken |
| :--- | :--- | :--- | :--- | :--- |
{timeline_table}

---

## 7. AI Prioritized Remediation Plan
{recs_list}

*Report automatically generated by AutoHeal Enterprise AppSec Platform with MITRE ATT&CK mapping.*
"""
        return md

    @classmethod
    def generate_json_dossier(cls, incident_id: str) -> Dict[str, Any]:
        """Produces a complete JSON dossier containing all telemetry and remediation evidence."""
        inc = get_security_incident(incident_id)
        if not inc:
            return {"error": "Incident not found", "incident_id": incident_id}

        from src.appsec.ai_advisor import AISecurityAdvisor
        rule_id = inc.get("rule_id", "AUTH-001")
        mitre = AISecurityAdvisor.get_mitre_mapping(rule_id)
        target_ep = inc.get("target_endpoint") or (inc.get("affected_endpoints") or ["/api/shop"])[0]

        ai_summary = AISecurityAdvisor.generate_grounded_summary(
            incident_id=incident_id,
            rule_id=rule_id,
            category=inc.get("category", "General"),
            severity=inc.get("severity", "HIGH"),
            endpoint=target_ep,
            source_ip=inc.get("source_ip", "127.0.0.1"),
            evidence=inc.get("evidence", {})
        )

        related_events = get_security_events(limit=25, client_ip=inc.get("source_ip"))
        return {
            "incident": inc,
            "mitre_attack_alignment": mitre,
            "ai_forensic_analysis": ai_summary,
            "associated_telemetry_events": related_events,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_version": "2.5.0-appsec-mitre"
        }

    @classmethod
    def generate_csv_events(cls, limit: int = 100) -> str:
        """Exports recent telemetry security events as CSV."""
        events = get_security_events(limit=limit)
        csv_lines = ["id,event_id,correlation_id,timestamp,client_ip,method,path,status_code,event_type,severity,action_taken"]
        for e in events:
            csv_lines.append(f"{e.get('id')},{e.get('event_id')},{e.get('correlation_id')},{e.get('timestamp')},{e.get('client_ip')},{e.get('method')},{e.get('path')},{e.get('status_code')},{e.get('event_type')},{e.get('severity')},{e.get('action_taken')}")
        return "\n".join(csv_lines)
