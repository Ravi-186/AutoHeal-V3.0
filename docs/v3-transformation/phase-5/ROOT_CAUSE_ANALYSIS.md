# AutoHeal v3.0 — Phase 5: Root-Cause Analysis (RCA) & Forensic Diagnosis

## 1. Executive Summary

Incident remediation is only sustainable if the underlying technical defect is identified and eliminated. The **Root-Cause Analysis (RCA)** subsystem empowers SOC analysts and application security engineers to document entry points, environmental factors, and verified forensic conclusions directly into the incident record with full audit history and optimistic concurrency control.

---

## 2. Structured Forensic Root-Cause Framework

The RCA data model is structured across three core dimensions:

```
+----------------------------------------------------------------------------------------------------+
|  Structured Root-Cause Formulation                                                                 |
+---------------------------+------------------------------------------------------------------------+
| Dimension                 | Technical Scope & Expectations                                         |
+---------------------------+------------------------------------------------------------------------+
| Suspected Entry Point     | Exact URL, route, header, form field, or API parameter exploited       |
|                           | (e.g., `POST /api/products/search?q=`, `X-Forwarded-For` spoofing).    |
+---------------------------+------------------------------------------------------------------------+
| Contributing Conditions   | Environmental, framework, or architectural weaknesses that enabled     |
|                           | exploitation (e.g., dynamic SQL string concatenation, unpinned ORM).   |
+---------------------------+------------------------------------------------------------------------+
| Confirmed Analyst         | Formal analytical verdict verified by engineering team before          |
| Conclusions               | applying code-level patch or permanent rule modifications.             |
+---------------------------+------------------------------------------------------------------------+
```

---

## 3. Collaborative Persistence & Concurrency

Analyst updates to the root-cause record are handled via the dedicated REST endpoint:
- **Endpoint:** `POST /api/security/incidents/{incident_id}/root-cause`
- **Request Payload:**
  ```json
  {
    "suspected_entry_point": "POST /api/auth/login [username parameter]",
    "root_cause_summary": "Unparameterized raw SQL query in authentication controller",
    "contributing_conditions": "ORM bypass used for legacy authentication query; lacking input sanitization middleware",
    "analyst_conclusions": "Vulnerability remediated via parameterized statement and AST virtual patch",
    "expected_version": 2
  }
  ```

### Concurrency Protection:
The endpoint evaluates `expected_version` against the persisted database record `version`. If another analyst has committed an update concurrently, the API rejects the request with HTTP 409 Conflict, preventing accidental overwrites.

### Audit Accountability:
Every root-cause save automatically appends an entry to `incident_activity_logs` with `action_type = 'RCA_UPDATED'`, recording the author, timestamp, and field diffs.

---

## 4. AI-Generated Forensic Advisory Card

To accelerate analyst investigations without delegating critical decisions to autonomous black boxes, the workspace includes an **AI Forensic Advisory Card**:

```
+----------------------------------------------------------------------------------------------------+
|  [AI Advisory Assistant]                                          Confidence Score: 94.2% (High)   |
|  Notice: Advisory suggestions generated for triage assistance. Requires human verification.        |
+----------------------------------------------------------------------------------------------------+
|  Diagnosis:                                                                                        |
|  Taint analysis indicates user-supplied input to `username` reaches `sqlite3.execute()` without    |
|  parameter binding or quoting at `src/shopsphere/auth.py:84`.                                      |
|                                                                                                    |
|  Recommended Permanent Fix:                                                                        |
|  Replace string interpolation `f"SELECT * FROM users WHERE username = '{u}'"` with parameterized  |
|  execution `cursor.execute("SELECT * FROM users WHERE username = ?", (u,))`.                      |
+----------------------------------------------------------------------------------------------------+
```

- **Visual Guardrail:** Always highlighted with distinct Indigo styling and prominent advisory warning.
- **Human-in-the-Loop:** Suggestions serve as starting points; only human analyst conclusions are eligible to satisfy resolution prerequisites.
