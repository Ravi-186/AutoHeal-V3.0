# AutoHeal Phase 8: Threat Intelligence and MITRE ATT&CK Integration

## 1. Overview

Effective incident investigation requires contextualizing local shop telemetry within the broader global threat landscape. AutoHeal integrates **MITRE ATT&CK Enterprise Matrix** mappings and external threat intelligence indicators directly into the 3D Threat Topology and AI SOC Copilot.

---

## 2. MITRE ATT&CK Enterprise Mapping

Every security rule in `RULE_METADATA` and every incident in `security_incidents` is mapped to canonical MITRE ATT&CK Tactics and Techniques:

| Rule ID | Threat Category | MITRE Tactic | MITRE Technique ID | MITRE Technique Name |
| :--- | :--- | :--- | :--- | :--- |
| `SQLI-001` | INJECTION | Initial Access (`TA0001`) | `T1190` | Exploit Public-Facing Application |
| `XSS-001` | INJECTION | Execution (`TA0002`) | `T1059.007` | JavaScript Execution |
| `CMD-001` | INJECTION | Execution (`TA0002`) | `T1059.004` | Command and Scripting Interpreter: Unix Shell |
| `PATH-001` | TRAVERSAL | Discovery (`TA0007`) | `T1083` | File and Directory Discovery |
| `AUTH-001` | CREDENTIAL_ACCESS | Credential Access (`TA0006`) | `T1110.001` | Brute Force: Password Guessing |
| `RATE-001` | DENIAL_OF_SERVICE | Impact (`TA0040`) | `T1498` | Network Denial of Service |
| `PRICE-001` | BUSINESS_LOGIC | Impact (`TA0040`) | `T1499` | Endpoint Denial of Service / Logic Abuse |

---

## 3. Threat Intelligence Data Model

When an external IP or domain is inspected in the 3D Topology or Copilot, the system synthesizes realistic, high-fidelity threat intelligence telemetry:

```json
{
  "client_ip": "198.51.100.99",
  "reputation": "MALICIOUS",
  "abuse_confidence_score": 94,
  "total_reports": 142,
  "last_reported_at": "2026-11-01T14:48:12",
  "country_code": "US",
  "country_name": "United States",
  "asn": "AS13335",
  "isp": "Cloudflare Test Infrastructure",
  "domain": "scanner-probe-node.net",
  "usage_type": "Data Center / Web Hosting / Transit",
  "threat_categories": [
    "Web Scanner",
    "SQLi Botnet Probe",
    "Automated Vulnerability Scanner"
  ]
}
```

---

## 4. Threat Scoring & Risk Multipliers

Threat intelligence directly influences the severity and prioritization of incidents via mathematical multipliers:

$$\text{RiskScore}_{\text{final}} = \text{SeverityBase} \times \left(1.0 + \frac{\text{AbuseScore}}{100} \times 0.5\right)$$

### Decision Matrix
- **Abuse Score $\ge 80\%$**: Immediate firewall containment recommended; automated SOAR block playbook marked high priority.
- **Abuse Score $50\% - 79\%$**: Flagged for heuristic monitoring; challenge with progressive rate limiting.
- **Abuse Score $< 50\%$**: Standard operational triage.

---

## 5. Visual Representation in 3D Topology

- High-reputation malicious IPs ($\ge 80\%$) are rendered as **Glowing Red Octahedrons** with pulsing outer threat rings.
- ASN clustering links related scanner IPs together using inferred purple dashed edges, visualizing distributed botnet infrastructure.
- In the **Inspector Drawer**, analysts can view historical abuse reports and click to trigger an IP-wide firewall drop.
