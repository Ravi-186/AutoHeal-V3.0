# SOAR Workflow Schema Reference

**Document ID:** SCHEMA-SOAR-001  
**Version:** 3.0.0  
**Phase:** 6 — Enterprise Security Orchestration, Automation, and Response  
**Security Classification:** Enterprise SOC Internal  
**Design Identity:** Obsidian Sentinel

---

## 1. Overview

The AutoHeal Visual SOAR platform uses a declarative JSON schema for playbooks, versioned graphs, execution contexts, and node configurations. This document defines the canonical specification enforced by `SOARValidator` and the SQLite persistence layer.

---

## 2. Playbook Definition Schema

Each playbook represents an operational response plan containing high-level metadata and a pointer to the active version.

```json
{
  "playbook_id": "PB-SQLI-CONTAINMENT",
  "name": "SQL Injection Autonomous Containment & Dual-Probe Verification",
  "description": "Automatic dynamic WAF quarantine and dual-probe perimeter verification for SQL injection attacks.",
  "category": "INJECTION",
  "status": "PUBLISHED",
  "current_version": 1,
  "trigger_type": "NEW_INCIDENT",
  "trigger_config": {
    "category": "INJECTION",
    "min_severity": "HIGH"
  },
  "owner": "admin@sentinel.sec",
  "required_permissions": ["soc:analyst", "soc:admin"],
  "created_at": "2026-11-01T10:00:00Z",
  "updated_at": "2026-11-01T12:00:00Z"
}
```

### Field Definitions

| Field | Type | Mandatory | Description / Constraints |
| :--- | :--- | :--- | :--- |
| `playbook_id` | String | Yes | Unique identifier prefixed with `PB-` (e.g. `PB-SQLI-CONTAINMENT`). Primary key. |
| `name` | String | Yes | Human-readable title (3–100 characters). |
| `description` | String | No | Technical operational summary (up to 1,000 characters). |
| `category` | String | Yes | Enum: `INJECTION`, `AUTHENTICATION`, `RATE_LIMIT`, `CONTAINMENT`, `INVESTIGATION`, `REMEDIATION`. |
| `status` | String | Yes | Enum: `DRAFT`, `PUBLISHED`, `ARCHIVED`. |
| `current_version` | Integer | Yes | Integer >= 1 denoting the currently active or drafting version. |
| `trigger_type` | String | Yes | Enum: `NEW_INCIDENT`, `SECURITY_EVENT`, `DETECTION_RULE_MATCHED`, `MANUAL`. |
| `trigger_config` | Object | No | Key-value filter parameters (e.g. `min_severity`, `rule_id`). |
| `owner` | String | Yes | Email or user identity of playbook maintainer. |
| `required_permissions` | Array<String> | Yes | RBAC roles required to execute or modify the playbook. |

---

## 3. Workflow Graph Schema (Version Graph)

Playbook graph structures are saved in `soar_playbook_versions` using three core structures: `nodes`, `edges`, and `viewport`.

```json
{
  "version": 1,
  "is_published": true,
  "change_summary": "Production baseline SQLi containment playbook",
  "viewport": {
    "x": 80,
    "y": 140,
    "zoom": 1.0
  },
  "nodes": [
    {
      "id": "node_trigger",
      "type": "trigger_incident",
      "category": "Trigger",
      "name": "SQLi Incident Trigger",
      "position": {"x": 80, "y": 180},
      "config": {
        "category": "INJECTION",
        "min_severity": "HIGH"
      }
    },
    {
      "id": "node_block_ip",
      "type": "action_block_ip",
      "category": "Action",
      "name": "Quarantine Offender IP",
      "position": {"x": 1040, "y": 100},
      "config": {
        "duration_seconds": 300,
        "reason": "SOAR Autonomous SQLi Block"
      }
    }
  ],
  "edges": [
    {
      "id": "e_trig_block",
      "source": "node_trigger",
      "target": "node_block_ip",
      "source_handle": "output",
      "target_handle": "input"
    }
  ]
}
```

### Node Specification

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `id` | String | Unique node identifier within the graph (e.g. `node_block_ip`, `act-1`). |
| `type` | String | Registered node type ID (must exist in `NODE_REGISTRY`). |
| `category` | String | Category label (`Trigger`, `Lookup`, `Condition`, `Branch`, `Approval`, `Action`, `Verification`). |
| `name` | String | Display name shown on canvas. |
| `position` | Object | `{ "x": float, "y": float }` canvas coordinates. |
| `config` | Object | Parameter dictionary specific to the node type. |

### Edge Specification

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `id` | String | Unique edge ID (e.g. `e1`, `e_src_tgt`). |
| `source` | String | Node `id` where connection originates. |
| `target` | String | Node `id` where connection terminates. |
| `source_handle` | String | Handle name on source (`output`, `true`, `false`, `approved`, `rejected`, `success`, `failure`). |
| `target_handle` | String | Handle name on destination (default `input`). |

---

## 4. Execution Context Schema

When a workflow runs, an execution context dictionary passes state between sequential nodes:

```json
{
  "execution_id": "EXEC-20261101-135AC657",
  "playbook_id": "PB-SQLI-CONTAINMENT",
  "execution_mode": "LIVE",
  "incident_id": "INC-20261101-001",
  "source_ip": "198.51.100.88",
  "username": "victim_shopper_01",
  "severity": "CRITICAL",
  "trigger_payload": {
    "source": "LIVE_TEST",
    "source_ip": "198.51.100.88",
    "severity": "CRITICAL"
  },
  "execution_vars": {
    "last_condition": true,
    "last_approval_decision": "APPROVED",
    "last_action_status": "COMPLETED"
  },
  "verification_outcomes": [true, true]
}
```

---

## 5. Security & Validation Rules

1. **Deterministic Hashing:** `SOARValidator` computes a SHA-256 validation digest `validation_hash` across canonicalized `{"nodes": nodes, "edges": edges}`. Publishing a version requires a matching `validation_hash`.
2. **Handle Whitelisting:** Edges originating from branching nodes MUST specify a recognized handle identifier matching the branch type.
3. **No Dangling References:** Every `source` and `target` in the `edges` list must correspond to an active node in the `nodes` list.
