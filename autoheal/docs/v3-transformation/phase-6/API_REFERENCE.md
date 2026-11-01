# Visual SOAR Automation Builder — REST API Reference

**Document ID:** API-SOAR-001  
**Version:** 3.0.0  
**Phase:** 6 — Enterprise Security Orchestration, Automation, and Response  
**Security Classification:** Enterprise SOC Internal  
**Design Identity:** Obsidian Sentinel

---

## 1. Overview & Authentication

All Phase 6 Visual SOAR endpoints are mounted under the base path `/api/soar`. The API accepts and returns `application/json` payloads and enforces strict parameter validation via Pydantic models.

---

## 2. API Endpoint Directory

### 2.1 Analytics & Catalog

#### `GET /api/soar/stats`
Returns aggregated real-time operational metrics across playbooks, executions, and pending approvals.
- **Response `200 OK`:**
  ```json
  {
    "total_playbooks": 4,
    "published_playbooks": 3,
    "draft_playbooks": 1,
    "total_executions": 24,
    "successful_executions": 21,
    "failed_executions": 3,
    "running_executions": 0,
    "pending_approvals": 2,
    "total_actions_enforced": 38,
    "success_rate": 87.5,
    "success_rate_pct": 87.5
  }
  ```

#### `GET /api/soar/node-types`
Returns the complete catalog of all 28 registered SOAR node types across all 7 categories.
- **Response `200 OK`:** Returns dictionary with `"node_types"` and individual node type specifications (`category`, `label`, `description`, `icon`, `color`, `default_config`, `handles`).

---

### 2.2 Playbook Management (CRUD & Versioning)

#### `GET /api/soar/playbooks`
Queries paginated playbooks with execution statistics.
- **Query Parameters:**
  - `search` (string, optional): Search keyword against ID, name, or description.
  - `category` (string, optional): Filter by category (`INJECTION`, `AUTHENTICATION`, `RATE_LIMIT`, etc.).
  - `status` (string, optional): Filter by status (`DRAFT`, `PUBLISHED`, `ARCHIVED`).
  - `page` (int, default: 1): Page number.
  - `page_size` (int, default: 15): Items per page.
  - `sort_by` (string, default: `updated_at`): Sort field (`name`, `status`, `executions`).
  - `sort_order` (string, default: `desc`): `asc` or `desc`.
- **Response `200 OK`:**
  ```json
  {
    "items": [...],
    "total": 4,
    "page": 1,
    "page_size": 15,
    "total_pages": 1
  }
  ```

#### `POST /api/soar/playbooks`
Creates a new playbook with an initial v1 draft.
- **Request Body:**
  ```json
  {
    "name": "SQL Injection Autonomous Containment",
    "description": "Dynamic WAF quarantine and verification.",
    "category": "INJECTION",
    "trigger_type": "NEW_INCIDENT",
    "trigger_config": {"category": "INJECTION"},
    "owner": "admin@sentinel.sec",
    "required_permissions": ["soc:analyst"]
  }
  ```
- **Response `200 OK` / `201 Created`:** Full created playbook record with `status: "DRAFT"` and `current_version: 1`.

#### `GET /api/soar/playbooks/{playbook_id}`
Retrieves full playbook details, active version graph (`nodes`, `edges`, `viewport`), and aggregate execution stats.
- **Query Parameters:** `version` (int, optional): Fetch a specific historical version instead of current.
- **Response `200 OK`:** Playbook details with `version_data`.
- **Response `404 Not Found`:** If playbook does not exist.

#### `PUT /api/soar/playbooks/{playbook_id}`
Updates high-level playbook metadata (name, description, category, trigger type, owner).
- **Request Body:** JSON dictionary with fields to update.
- **Response `200 OK`:** Updated playbook record.

#### `POST /api/soar/playbooks/{playbook_id}/duplicate`
Clones an existing playbook and its current version graph into a new `DRAFT` playbook.
- **Request Body (optional):** `{"new_name": "Copy of SQL Injection Containment"}`
- **Response `200 OK`:** Cloned playbook record with newly generated ID.

#### `POST /api/soar/playbooks/{playbook_id}/archive`
Soft archives a playbook.
- **Response `200 OK`:** `{"status": "success", "message": "Playbook PB-... archived."}`

#### `GET /api/soar/playbooks/{playbook_id}/versions`
Lists all historical version records for a playbook.
- **Response `200 OK`:** Array of versions (`version`, `is_published`, `change_summary`, `created_by`, `created_at`).

#### `POST /api/soar/playbooks/{playbook_id}/versions/draft`
Saves updated canvas graph (`nodes`, `edges`, `viewport`) to draft. If current version is published, automatically forks a new draft version.
- **Request Body:**
  ```json
  {
    "nodes": [...],
    "edges": [...],
    "viewport": {"x": 0, "y": 0, "zoom": 1.0},
    "change_summary": "Added dual probe verification"
  }
  ```
- **Response `200 OK`:** Updated playbook version record.

#### `POST /api/soar/playbooks/{playbook_id}/publish`
Validates and publishes the active draft version, locking it immutably.
- **Request Body (optional):** `{"version": 1, "validation_hash": "..."}`
- **Response `200 OK`:** Updated playbook record with `status: "PUBLISHED"`.
- **Response `400 Bad Request`:** If graph contains validation errors or hash mismatch.

---

### 2.3 Workflow Validation & Execution

#### `POST /api/soar/playbooks/validate`
Performs server-side DAG structural, security, and topological validation without state mutation.
- **Request Body:**
  ```json
  {
    "nodes": [...],
    "edges": [...]
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "is_valid": true,
    "errors": [],
    "warnings": [],
    "affected_node_ids": [],
    "suggested_corrections": [],
    "validation_hash": "a1b2c3d4..."
  }
  ```

#### `POST /api/soar/playbooks/{playbook_id}/execute`
Executes a playbook in **LIVE** mode against the ShopSphere application environment.
- **Request Body:**
  ```json
  {
    "incident_id": "INC-20261101-001",
    "trigger_payload": {
      "source_ip": "198.51.100.88",
      "severity": "CRITICAL"
    }
  }
  ```
- **Response `200 OK`:** Full execution dossier (`status`, `execution_id`, `verification_status`, `duration_ms`, `nodes`, `is_dry_run: false`).

#### `POST /api/soar/playbooks/{playbook_id}/dry-run`
Executes a playbook in **DRY_RUN** mode, evaluating conditions and branches without mutating perimeter state or ShopSphere tables.
- **Request Body:** Identical to `/execute`.
- **Response `200 OK`:** Execution dossier with `is_dry_run: true` and simulated node outcomes.

#### `GET /api/soar/executions`
Retrieves paginated workflow execution history.
- **Query Parameters:** `playbook_id`, `incident_id`, `status`, `execution_mode`, `page`, `page_size`.
- **Response `200 OK`:** `{"items": [...], "executions": [...], "total": 24, "page": 1, "page_size": 20}`.

#### `GET /api/soar/executions/{execution_id}`
Retrieves detailed telemetry state and step-by-step node execution traces.
- **Response `200 OK`:** `{"execution": {...}, "nodes": [...], ...}`.
- **Response `404 Not Found`:** If execution does not exist.

#### `POST /api/soar/executions/{execution_id}/cancel`
Cancels an in-flight or approval-paused workflow execution.
- **Request Body (optional):** `{"reason": "Analyst manual cancellation"}`
- **Response `200 OK`:** `{"status": "CANCELLED", "execution_status": "CANCELLED", "message": "..."}`.

---

### 2.4 Human-in-the-Loop Approvals

#### `GET /api/soar/approvals` & `GET /api/soar/approvals/pending`
Lists all pending approval gates awaiting operator sign-off.
- **Query Parameters:** `execution_id` (optional).
- **Response `200 OK`:** Array of pending approval requests (`approval_id`, `execution_id`, `playbook_id`, `action_type`, `action_target`, `action_description`, `requested_at`).

#### `POST /api/soar/approvals/{approval_id}/decide`
Submits decision (`APPROVED` or `REJECTED`) and resumes paused workflow traversal.
- **Request Body:**
  ```json
  {
    "decision": "APPROVED",
    "reason": "Authorized emergency quarantine of compromised host.",
    "decided_by": "admin@sentinel.sec"
  }
  ```
- **Response `200 OK`:** Resumed execution record (`status: "COMPLETED"`, `approval_id`, `decision`).
- **Response `400 Bad Request`:** If approval already decided (replay defense) or invalid decision value.

---

### 2.5 Security Audit Logs

#### `GET /api/soar/audit-logs`
Retrieves immutable, append-only SOAR audit trail records.
- **Query Parameters:** `playbook_id`, `execution_id`, `page`, `page_size`.
- **Response `200 OK`:** `{"items": [...], "audit_logs": [...], "total": 50, "page": 1, "page_size": 25}`.
