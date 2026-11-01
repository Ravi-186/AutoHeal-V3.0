import json
import secrets
import math
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple

from shopsphere.database import get_db_connection


# =========================================================================
# SOAR METRICS & STATS
# =========================================================================

def get_soar_stats() -> Dict[str, Any]:
    """Computes real-time SOAR metrics directly from persisted SQLite records."""
    seed_default_playbooks_if_empty()
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Playbook totals
        cursor.execute("SELECT COUNT(*) AS total FROM soar_playbooks WHERE status != 'ARCHIVED'")
        total_playbooks = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM soar_playbooks WHERE status = 'PUBLISHED'")
        published_playbooks = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM soar_playbooks WHERE status = 'DRAFT'")
        draft_playbooks = cursor.fetchone()["total"]

        # Execution totals
        cursor.execute("SELECT COUNT(*) AS total FROM soar_executions")
        total_executions = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM soar_executions WHERE status = 'COMPLETED'")
        successful_executions = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM soar_executions WHERE status IN ('FAILED', 'VERIFICATION_FAILED')")
        failed_executions = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM soar_executions WHERE status = 'RUNNING'")
        running_executions = cursor.fetchone()["total"]

        # Approvals
        cursor.execute("SELECT COUNT(*) AS total FROM soar_approvals WHERE status = 'PENDING'")
        pending_approvals = cursor.fetchone()["total"]

        # Actions Enforced (completed action nodes)
        cursor.execute("""
        SELECT COUNT(*) AS total FROM soar_node_executions 
        WHERE status = 'COMPLETED' AND node_type LIKE 'action_%'
        """)
        total_actions_enforced = cursor.fetchone()["total"]

        success_rate = 0.0
        if total_executions > 0:
            success_rate = round((successful_executions / total_executions) * 100, 1)

        return {
            "total_playbooks": total_playbooks,
            "published_playbooks": published_playbooks,
            "draft_playbooks": draft_playbooks,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "running_executions": running_executions,
            "pending_approvals": pending_approvals,
            "total_actions_enforced": total_actions_enforced,
            "success_rate": success_rate,
            "success_rate_pct": success_rate
        }


# =========================================================================
# PLAYBOOK REGISTRY & QUERIES
# =========================================================================

def query_playbooks_paginated(
    search: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 15,
    sort_by: str = "updated_at",
    sort_order: str = "desc"
) -> Dict[str, Any]:
    """Queries SOAR playbooks with compound filters, search, execution stats, and pagination."""
    seed_default_playbooks_if_empty()
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size

    allowed_sort_fields = {
        "updated_at": "p.updated_at",
        "created_at": "p.created_at",
        "name": "p.name",
        "status": "p.status",
        "category": "p.category",
        "executions": "exec_count"
    }
    sort_column = allowed_sort_fields.get(sort_by, "p.updated_at")
    sort_dir = "ASC" if sort_order.lower() == "asc" else "DESC"

    where_clauses = ["p.status != 'ARCHIVED'"]
    params: List[Any] = []

    if search and search.strip():
        term = f"%{search.strip()}%"
        where_clauses.append("(p.playbook_id LIKE ? OR p.name LIKE ? OR p.description LIKE ?)")
        params.extend([term, term, term])

    if category and category.strip() and category.upper() != "ALL":
        where_clauses.append("p.category = ?")
        params.append(category.strip().upper())

    if status and status.strip() and status.upper() != "ALL":
        where_clauses.append("p.status = ?")
        params.append(status.strip().upper())

    where_sql = " AND ".join(where_clauses)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Count total matching records
        count_query = f"SELECT COUNT(*) AS total FROM soar_playbooks p WHERE {where_sql}"
        cursor.execute(count_query, params)
        total_items = cursor.fetchone()["total"]
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

        # Fetch playbooks with aggregate execution metrics
        data_query = f"""
        SELECT 
            p.*,
            COALESCE(e.total_execs, 0) AS total_executions,
            COALESCE(e.success_execs, 0) AS success_count,
            COALESCE(e.failed_execs, 0) AS failure_count,
            e.last_executed_at
        FROM soar_playbooks p
        LEFT JOIN (
            SELECT 
                playbook_id,
                COUNT(*) AS total_execs,
                SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS success_execs,
                SUM(CASE WHEN status IN ('FAILED', 'VERIFICATION_FAILED') THEN 1 ELSE 0 END) AS failed_execs,
                MAX(started_at) AS last_executed_at
            FROM soar_executions
            GROUP BY playbook_id
        ) e ON p.playbook_id = e.playbook_id
        WHERE {where_sql}
        ORDER BY {sort_column} {sort_dir}
        LIMIT ? OFFSET ?
        """
        cursor.execute(data_query, params + [page_size, offset])
        rows = cursor.fetchall()

        items = []
        for r in rows:
            d = dict(r)
            try:
                d["trigger_config"] = json.loads(d.get("trigger_config_json") or "{}")
            except Exception:
                d["trigger_config"] = {}
            try:
                d["required_permissions"] = json.loads(d.get("required_permissions") or "[]")
            except Exception:
                d["required_permissions"] = ["soc:analyst"]
            items.append(d)

        return {
            "items": items,
            "total": total_items,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }


def get_playbook(playbook_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves single playbook metadata along with its active/latest version graph."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            p.*,
            COALESCE(e.total_execs, 0) AS total_executions,
            COALESCE(e.success_execs, 0) AS success_count,
            COALESCE(e.failed_execs, 0) AS failure_count,
            e.last_executed_at
        FROM soar_playbooks p
        LEFT JOIN (
            SELECT 
                playbook_id,
                COUNT(*) AS total_execs,
                SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS success_execs,
                SUM(CASE WHEN status IN ('FAILED', 'VERIFICATION_FAILED') THEN 1 ELSE 0 END) AS failed_execs,
                MAX(started_at) AS last_executed_at
            FROM soar_executions
            WHERE playbook_id = ?
        ) e ON p.playbook_id = e.playbook_id
        WHERE p.playbook_id = ?
        """, (playbook_id, playbook_id))
        row = cursor.fetchone()
        if not row:
            return None

        pb = dict(row)
        try:
            pb["trigger_config"] = json.loads(pb.get("trigger_config_json") or "{}")
        except Exception:
            pb["trigger_config"] = {}
        try:
            pb["required_permissions"] = json.loads(pb.get("required_permissions") or "[]")
        except Exception:
            pb["required_permissions"] = ["soc:analyst"]

        # Fetch current version graph
        cursor.execute("""
        SELECT * FROM soar_playbook_versions 
        WHERE playbook_id = ? AND version = ?
        """, (playbook_id, pb["current_version"]))
        ver_row = cursor.fetchone()

        if ver_row:
            pb["version_data"] = {
                "version": ver_row["version"],
                "nodes": json.loads(ver_row["nodes_json"] or "[]"),
                "edges": json.loads(ver_row["edges_json"] or "[]"),
                "viewport": json.loads(ver_row["viewport_json"] or '{"x":0,"y":0,"zoom":1}'),
                "is_published": bool(ver_row["is_published"]),
                "change_summary": ver_row["change_summary"],
                "created_at": ver_row["created_at"]
            }
        else:
            pb["version_data"] = {
                "version": pb["current_version"],
                "nodes": [],
                "edges": [],
                "viewport": {"x": 0, "y": 0, "zoom": 1},
                "is_published": False,
                "change_summary": "Initial draft",
                "created_at": pb["created_at"]
            }

        return pb


def create_playbook(
    name: str,
    description: str,
    category: str,
    trigger_type: str = "NEW_INCIDENT",
    trigger_config: Optional[Dict[str, Any]] = None,
    owner: str = "admin@sentinel.sec",
    required_permissions: Optional[List[str]] = None,
    initial_nodes: Optional[List[Dict[str, Any]]] = None,
    initial_edges: Optional[List[Dict[str, Any]]] = None,
    custom_playbook_id: Optional[str] = None
) -> Dict[str, Any]:
    """Creates a new SOAR playbook in DRAFT status with initial version 1 canvas."""
    if not name or not name.strip():
        raise ValueError("Playbook name is required.")

    cat_clean = (category or "INJECTION").strip().upper()
    pid = custom_playbook_id or f"PB-{cat_clean[:4]}-{secrets.token_hex(4).upper()}"

    t_cfg_json = json.dumps(trigger_config or {})
    perms_json = json.dumps(required_permissions or ["soc:analyst"])
    nodes_json = json.dumps(initial_nodes or [])
    edges_json = json.dumps(initial_edges or [])

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO soar_playbooks (
            playbook_id, name, description, category, status, current_version,
            trigger_type, trigger_config_json, owner, required_permissions
        ) VALUES (?, ?, ?, ?, 'DRAFT', 1, ?, ?, ?, ?)
        """, (
            pid, name.strip(), description.strip(), cat_clean,
            trigger_type, t_cfg_json, owner, perms_json
        ))

        cursor.execute("""
        INSERT INTO soar_playbook_versions (
            playbook_id, version, nodes_json, edges_json, is_published, change_summary, created_by
        ) VALUES (?, 1, ?, ?, 0, 'Initial playbook creation', ?)
        """, (pid, nodes_json, edges_json, owner))

        conn.commit()

    record_soar_audit(
        action_type="PLAYBOOK_CREATED",
        playbook_id=pid,
        actor=owner,
        details={"name": name, "category": cat_clean, "trigger_type": trigger_type}
    )

    return get_playbook(pid)


def update_playbook_metadata(
    playbook_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    trigger_type: Optional[str] = None,
    trigger_config: Optional[Dict[str, Any]] = None,
    status: Optional[str] = None,
    owner: Optional[str] = None,
    actor: str = "admin@sentinel.sec"
) -> Dict[str, Any]:
    """Updates high-level playbook metadata."""
    existing = get_playbook(playbook_id)
    if not existing:
        raise ValueError(f"Playbook {playbook_id} not found.")

    updates = []
    params = []

    if name is not None and name.strip():
        updates.append("name = ?")
        params.append(name.strip())
    if description is not None:
        updates.append("description = ?")
        params.append(description.strip())
    if category is not None:
        updates.append("category = ?")
        params.append(category.strip().upper())
    if trigger_type is not None:
        updates.append("trigger_type = ?")
        params.append(trigger_type.strip())
    if trigger_config is not None:
        updates.append("trigger_config_json = ?")
        params.append(json.dumps(trigger_config))
    if status is not None:
        updates.append("status = ?")
        params.append(status.strip().upper())
    if owner is not None:
        updates.append("owner = ?")
        params.append(owner.strip())

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(playbook_id)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE soar_playbooks SET {', '.join(updates)} WHERE playbook_id = ?", params)
        conn.commit()

    record_soar_audit(
        action_type="PLAYBOOK_UPDATED",
        playbook_id=playbook_id,
        actor=actor,
        details={"updates": updates}
    )

    return get_playbook(playbook_id)


def duplicate_playbook(source_playbook_id: str, new_name: Optional[str] = None, actor: str = "admin@sentinel.sec") -> Dict[str, Any]:
    """Duplicates an existing playbook with its current version graph into a new DRAFT playbook."""
    src = get_playbook(source_playbook_id)
    if not src:
        raise ValueError(f"Source playbook {source_playbook_id} not found.")

    dup_name = new_name or f"Copy of {src['name']}"
    dup_id = f"PB-{src['category'][:4]}-{secrets.token_hex(4).upper()}"

    v_data = src.get("version_data", {})
    return create_playbook(
        name=dup_name,
        description=f"Cloned from {src['name']} ({source_playbook_id}). {src['description']}",
        category=src["category"],
        trigger_type=src["trigger_type"],
        trigger_config=src.get("trigger_config"),
        owner=actor,
        required_permissions=src.get("required_permissions"),
        initial_nodes=v_data.get("nodes", []),
        initial_edges=v_data.get("edges", []),
        custom_playbook_id=dup_id
    )


def archive_playbook(playbook_id: str, actor: str = "admin@sentinel.sec") -> Dict[str, Any]:
    """Safely archives a playbook, disabling active execution."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE soar_playbooks SET status = 'ARCHIVED', updated_at = CURRENT_TIMESTAMP WHERE playbook_id = ?", (playbook_id,))
        conn.commit()

    record_soar_audit(
        action_type="PLAYBOOK_ARCHIVED",
        playbook_id=playbook_id,
        actor=actor,
        details={"action": "archived"}
    )
    return {"status": "success", "message": f"Playbook {playbook_id} archived."}


# =========================================================================
# WORKFLOW VERSIONING & DRAFT MANAGEMENT
# =========================================================================

def save_playbook_draft(
    playbook_id: str,
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    viewport: Optional[Dict[str, Any]] = None,
    change_summary: str = "",
    actor: str = "admin@sentinel.sec"
) -> Dict[str, Any]:
    """Saves workflow graph changes to the current active draft version."""
    pb = get_playbook(playbook_id)
    if not pb:
        raise ValueError(f"Playbook {playbook_id} not found.")

    curr_version = pb["current_version"]
    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)
    viewport_json = json.dumps(viewport or {"x": 0, "y": 0, "zoom": 1})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Check if current version is already published
        cursor.execute("SELECT is_published FROM soar_playbook_versions WHERE playbook_id = ? AND version = ?", (playbook_id, curr_version))
        ver_row = cursor.fetchone()

        if ver_row and ver_row["is_published"]:
            # If current version is published, fork a new draft version
            new_version = curr_version + 1
            cursor.execute("""
            INSERT INTO soar_playbook_versions (
                playbook_id, version, nodes_json, edges_json, viewport_json, is_published, change_summary, created_by
            ) VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            """, (playbook_id, new_version, nodes_json, edges_json, viewport_json, change_summary or "Draft update", actor))

            cursor.execute("""
            UPDATE soar_playbooks 
            SET current_version = ?, status = 'DRAFT', updated_at = CURRENT_TIMESTAMP 
            WHERE playbook_id = ?
            """, (new_version, playbook_id))
        else:
            # Overwrite active draft
            cursor.execute("""
            UPDATE soar_playbook_versions 
            SET nodes_json = ?, edges_json = ?, viewport_json = ?, change_summary = ?, created_at = CURRENT_TIMESTAMP
            WHERE playbook_id = ? AND version = ?
            """, (nodes_json, edges_json, viewport_json, change_summary, playbook_id, curr_version))

            cursor.execute("UPDATE soar_playbooks SET updated_at = CURRENT_TIMESTAMP WHERE playbook_id = ?", (playbook_id,))

        conn.commit()

    record_soar_audit(
        action_type="DRAFT_SAVED",
        playbook_id=playbook_id,
        actor=actor,
        details={"node_count": len(nodes), "edge_count": len(edges), "version": curr_version}
    )

    return get_playbook(playbook_id)


def publish_playbook_version(
    playbook_id: str,
    version: Optional[int] = None,
    validation_hash: Optional[str] = None,
    actor: str = "admin@sentinel.sec"
) -> Dict[str, Any]:
    """Marks a playbook version as PUBLISHED and transitions playbook to active status."""
    pb = get_playbook(playbook_id)
    if not pb:
        raise ValueError(f"Playbook {playbook_id} not found.")

    target_ver = version or pb["current_version"]

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE soar_playbook_versions 
        SET is_published = 1, validation_hash = ?
        WHERE playbook_id = ? AND version = ?
        """, (validation_hash or "sha256-verified", playbook_id, target_ver))

        cursor.execute("""
        UPDATE soar_playbooks 
        SET status = 'PUBLISHED', current_version = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE playbook_id = ?
        """, (target_ver, playbook_id))
        conn.commit()

    record_soar_audit(
        action_type="PLAYBOOK_PUBLISHED",
        playbook_id=playbook_id,
        actor=actor,
        details={"version": target_ver, "validation_hash": validation_hash}
    )

    return get_playbook(playbook_id)


def get_playbook_versions_list(playbook_id: str) -> List[Dict[str, Any]]:
    """Lists all historical versions for a playbook."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT version, is_published, change_summary, created_by, created_at,
               length(nodes_json) AS nodes_bytes, length(edges_json) AS edges_bytes
        FROM soar_playbook_versions
        WHERE playbook_id = ?
        ORDER BY version DESC
        """, (playbook_id,))
        return [dict(r) for r in cursor.fetchall()]


# =========================================================================
# WORKFLOW EXECUTION TELEMETRY
# =========================================================================

def create_soar_execution(
    playbook_id: str,
    playbook_version: int,
    playbook_name: str,
    trigger_source: str = "MANUAL",
    incident_id: Optional[str] = None,
    event_id: Optional[str] = None,
    simulation_id: Optional[str] = None,
    execution_mode: str = "LIVE",
    initial_context: Optional[Dict[str, Any]] = None,
    triggered_by: str = "admin@sentinel.sec"
) -> str:
    """Initializes an execution record in QUEUED status."""
    exec_id = f"EXEC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
    ctx_json = json.dumps(initial_context or {})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO soar_executions (
            execution_id, playbook_id, playbook_version, playbook_name,
            trigger_source, incident_id, event_id, simulation_id,
            execution_mode, status, context_json, triggered_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'QUEUED', ?, ?)
        """, (
            exec_id, playbook_id, playbook_version, playbook_name,
            trigger_source, incident_id, event_id, simulation_id,
            execution_mode.upper(), ctx_json, triggered_by
        ))
        conn.commit()

    record_soar_audit(
        action_type="EXECUTION_STARTED",
        playbook_id=playbook_id,
        execution_id=exec_id,
        actor=triggered_by,
        details={"mode": execution_mode, "incident_id": incident_id, "trigger_source": trigger_source}
    )

    return exec_id


def update_soar_execution(
    execution_id: str,
    status: Optional[str] = None,
    current_node_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    verification_status: Optional[str] = None,
    duration_ms: Optional[float] = None,
    error_message: Optional[str] = None
):
    """Updates state of an active execution."""
    updates = []
    params = []

    if status:
        updates.append("status = ?")
        params.append(status.upper())
        if status.upper() in ("COMPLETED", "FAILED", "CANCELLED", "VERIFICATION_FAILED"):
            updates.append("completed_at = CURRENT_TIMESTAMP")
    if current_node_id:
        updates.append("current_node_id = ?")
        params.append(current_node_id)
    if context:
        updates.append("context_json = ?")
        params.append(json.dumps(context))
    if verification_status:
        updates.append("verification_status = ?")
        params.append(verification_status)
    if duration_ms is not None:
        updates.append("duration_ms = ?")
        params.append(duration_ms)
    if error_message is not None:
        updates.append("error_message = ?")
        params.append(error_message)

    if not updates:
        return

    params.append(execution_id)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE soar_executions SET {', '.join(updates)} WHERE execution_id = ?", params)
        conn.commit()


def log_node_execution(
    execution_id: str,
    node_id: str,
    node_type: str,
    node_name: str,
    status: str,
    input_data: Optional[Dict[str, Any]] = None,
    output_data: Optional[Dict[str, Any]] = None,
    duration_ms: float = 0.0,
    error_message: Optional[str] = None,
    retry_count: int = 0
):
    """Logs node-level execution telemetry."""
    in_json = json.dumps(input_data or {})
    out_json = json.dumps(output_data or {})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO soar_node_executions (
            execution_id, node_id, node_type, node_name, status,
            input_json, output_json, duration_ms, error_message, retry_count, completed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            execution_id, node_id, node_type, node_name, status.upper(),
            in_json, out_json, duration_ms, error_message, retry_count
        ))
        conn.commit()


def get_soar_execution(execution_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves full execution details along with node-by-node execution records."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM soar_executions WHERE execution_id = ?", (execution_id,))
        exec_row = cursor.fetchone()
        if not exec_row:
            return None

        result = dict(exec_row)
        try:
            result["context"] = json.loads(result.get("context_json") or "{}")
        except Exception:
            result["context"] = {}

        cursor.execute("""
        SELECT * FROM soar_node_executions 
        WHERE execution_id = ? 
        ORDER BY id ASC
        """, (execution_id,))
        nodes_raw = cursor.fetchall()

        node_list = []
        for n in nodes_raw:
            nd = dict(n)
            try:
                nd["input"] = json.loads(nd.get("input_json") or "{}")
            except Exception:
                nd["input"] = {}
            try:
                nd["output"] = json.loads(nd.get("output_json") or "{}")
            except Exception:
                nd["output"] = {}
            node_list.append(nd)

        result["nodes"] = node_list
        return result


def list_soar_executions(
    playbook_id: Optional[str] = None,
    incident_id: Optional[str] = None,
    status: Optional[str] = None,
    execution_mode: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """Lists execution history with multi-field filtering and pagination."""
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size

    where_clauses = ["1=1"]
    params: List[Any] = []

    if playbook_id:
        where_clauses.append("playbook_id = ?")
        params.append(playbook_id)
    if incident_id:
        where_clauses.append("incident_id = ?")
        params.append(incident_id)
    if status and status.upper() != "ALL":
        where_clauses.append("status = ?")
        params.append(status.upper())
    if execution_mode and execution_mode.upper() != "ALL":
        where_clauses.append("execution_mode = ?")
        params.append(execution_mode.upper())

    where_sql = " AND ".join(where_clauses)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) AS total FROM soar_executions WHERE {where_sql}", params)
        total_items = cursor.fetchone()["total"]
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

        cursor.execute(f"""
        SELECT * FROM soar_executions 
        WHERE {where_sql}
        ORDER BY started_at DESC
        LIMIT ? OFFSET ?
        """, params + [page_size, offset])
        rows = cursor.fetchall()

        items = []
        for r in rows:
            d = dict(r)
            try:
                d["context"] = json.loads(d.get("context_json") or "{}")
            except Exception:
                d["context"] = {}
            items.append(d)

        return {
            "items": items,
            "total": total_items,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }


def cancel_soar_execution(execution_id: str, actor: str = "admin@sentinel.sec", reason: str = "") -> Dict[str, Any]:
    """Cancels a running or waiting execution."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, playbook_id FROM soar_executions WHERE execution_id = ?", (execution_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Execution {execution_id} not found.")

        current_status = row["status"]
        if current_status in ("COMPLETED", "FAILED", "CANCELLED"):
            raise ValueError(f"Cannot cancel execution in terminal state '{current_status}'.")

        cursor.execute("""
        UPDATE soar_executions 
        SET status = 'CANCELLED', completed_at = CURRENT_TIMESTAMP, error_message = ?
        WHERE execution_id = ?
        """, (f"Cancelled by {actor}. Reason: {reason or 'User intervention'}", execution_id))

        # Also cancel any pending approvals for this execution
        cursor.execute("""
        UPDATE soar_approvals 
        SET status = 'EXPIRED', decided_by = ?, reason = 'Execution cancelled', decided_at = CURRENT_TIMESTAMP
        WHERE execution_id = ? AND status = 'PENDING'
        """, (actor, execution_id))

        conn.commit()

    record_soar_audit(
        action_type="EXECUTION_CANCELLED",
        playbook_id=row["playbook_id"],
        execution_id=execution_id,
        actor=actor,
        details={"reason": reason}
    )

    return {"status": "CANCELLED", "execution_status": "CANCELLED", "message": f"Execution {execution_id} cancelled."}


# =========================================================================
# HUMAN-IN-THE-LOOP APPROVAL CENTER
# =========================================================================

def create_approval_request(
    execution_id: str,
    node_id: str,
    playbook_id: str,
    action_type: str,
    action_target: str,
    action_description: str,
    incident_id: Optional[str] = None,
    requested_by: str = "System"
) -> Dict[str, Any]:
    """Creates a pending approval request pausing workflow execution."""
    appr_id = f"APPR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
    token = f"tok_appr_{secrets.token_hex(16)}"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO soar_approvals (
            approval_id, execution_id, node_id, playbook_id,
            action_type, action_target, action_description,
            status, requested_by, decision_token, incident_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?, ?)
        """, (
            appr_id, execution_id, node_id, playbook_id,
            action_type, action_target, action_description,
            requested_by, token, incident_id
        ))
        conn.commit()

    record_soar_audit(
        action_type="APPROVAL_REQUESTED",
        playbook_id=playbook_id,
        execution_id=execution_id,
        actor=requested_by,
        details={"approval_id": appr_id, "action_type": action_type, "target": action_target}
    )

    return {
        "approval_id": appr_id,
        "token": token,
        "action_type": action_type,
        "action_target": action_target,
        "description": action_description
    }


def get_approval(approval_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single approval record by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM soar_approvals WHERE approval_id = ?", (approval_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def list_pending_approvals(execution_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists all pending approval gates."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM soar_approvals WHERE status = 'PENDING'"
        params = []
        if execution_id:
            query += " AND execution_id = ?"
            params.append(execution_id)
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]


def decide_approval(
    approval_id: str,
    decision: str,  # 'APPROVED' or 'REJECTED'
    decided_by: str = "admin@sentinel.sec",
    reason: str = ""
) -> Dict[str, Any]:
    """Resolves an approval gate. Enforces single-use token and records audit decision."""
    dec_clean = decision.strip().upper()
    if dec_clean not in ("APPROVED", "REJECTED"):
        raise ValueError("Decision must be 'APPROVED' or 'REJECTED'.")
    if dec_clean == "REJECTED" and not reason.strip():
        raise ValueError("A mandatory rejection reason must be provided.")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM soar_approvals WHERE approval_id = ?", (approval_id,))
        appr = cursor.fetchone()
        if not appr:
            raise ValueError(f"Approval request {approval_id} not found.")

        if appr["status"] != "PENDING":
            raise ValueError(f"Approval {approval_id} already decided as '{appr['status']}'. Replay rejected.")

        cursor.execute("""
        UPDATE soar_approvals 
        SET status = ?, decided_by = ?, reason = ?, decided_at = CURRENT_TIMESTAMP
        WHERE approval_id = ?
        """, (dec_clean, decided_by, reason.strip(), approval_id))
        conn.commit()

    record_soar_audit(
        action_type="APPROVAL_GRANTED" if dec_clean == "APPROVED" else "APPROVAL_REJECTED",
        playbook_id=appr["playbook_id"],
        execution_id=appr["execution_id"],
        actor=decided_by,
        details={"approval_id": approval_id, "decision": dec_clean, "reason": reason}
    )

    return {
        "status": "success",
        "approval_id": approval_id,
        "decision": dec_clean,
        "execution_id": appr["execution_id"],
        "node_id": appr["node_id"]
    }


# =========================================================================
# AUDIT LOGGING
# =========================================================================

def record_soar_audit(
    action_type: str,
    playbook_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    actor: str = "admin@sentinel.sec",
    details: Optional[Dict[str, Any]] = None,
    ip_address: str = "127.0.0.1"
):
    """Permanently records an audit trail entry for privileged SOAR operations."""
    log_id = f"AUD-SOAR-{secrets.token_hex(6).upper()}"
    det_json = json.dumps(details or {})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO soar_audit_logs (
            log_id, action_type, playbook_id, execution_id, actor, details_json, ip_address
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (log_id, action_type.upper(), playbook_id, execution_id, actor, det_json, ip_address))
        conn.commit()


def list_soar_audit_logs(
    playbook_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 25
) -> Dict[str, Any]:
    """Retrieves paginated audit log history."""
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size

    where_clauses = ["1=1"]
    params: List[Any] = []

    if playbook_id:
        where_clauses.append("playbook_id = ?")
        params.append(playbook_id)
    if execution_id:
        where_clauses.append("execution_id = ?")
        params.append(execution_id)

    where_sql = " AND ".join(where_clauses)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) AS total FROM soar_audit_logs WHERE {where_sql}", params)
        total_items = cursor.fetchone()["total"]
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

        cursor.execute(f"""
        SELECT * FROM soar_audit_logs 
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """, params + [page_size, offset])
        rows = cursor.fetchall()

        items = []
        for r in rows:
            d = dict(r)
            try:
                d["details"] = json.loads(d.get("details_json") or "{}")
            except Exception:
                d["details"] = {}
            items.append(d)

        return {
            "items": items,
            "total": total_items,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }


# =========================================================================
# BASELINE ENTERPRISE PLAYBOOKS SEEDING
# =========================================================================

def seed_default_playbooks_if_empty():
    """Seeds four realistic enterprise security playbooks if none exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM soar_playbooks")
        if cursor.fetchone()["total"] > 0:
            return  # already seeded

        # Playbook 1: SQL Injection Autonomous Quarantine & Verification
        pb1_nodes = [
            {"id": "node_trigger", "type": "trigger_incident", "name": "SQLi Incident Trigger", "position": {"x": 80, "y": 180}, "config": {"category": "INJECTION", "min_severity": "HIGH"}},
            {"id": "node_lookup_ip", "type": "lookup_ip_info", "name": "Attacker IP Lookup", "position": {"x": 320, "y": 180}, "config": {}},
            {"id": "node_cond_sev", "type": "condition_severity", "name": "Severity Check", "position": {"x": 560, "y": 180}, "config": {"operator": "IN_LIST", "values": ["HIGH", "CRITICAL"]}},
            {"id": "node_branch_sev", "type": "branch_if_else", "name": "Critical Branch", "position": {"x": 800, "y": 180}, "config": {}},
            {"id": "node_block_ip", "type": "action_block_ip", "name": "Quarantine Offender IP", "position": {"x": 1040, "y": 100}, "config": {"duration_seconds": 300, "reason": "SOAR Autonomous SQLi Block"}},
            {"id": "node_verify_quarantine", "type": "verify_ip_blocked", "name": "Perimeter 403 Probe", "position": {"x": 1280, "y": 100}, "config": {"expected_code": 403}},
            {"id": "node_verify_benign", "type": "verify_benign_traffic", "name": "Shopper 200 Probe", "position": {"x": 1520, "y": 100}, "config": {"target_path": "/api/shop/products", "expected_code": 200}},
            {"id": "node_add_note", "type": "action_add_note", "name": "Log Containment Note", "position": {"x": 1760, "y": 100}, "config": {"note_template": "Autonomous quarantine and dual-probe verification completed successfully."}},
            {"id": "node_notify_analyst", "type": "action_notify_analyst", "name": "Notify SOC Analyst", "position": {"x": 1040, "y": 280}, "config": {"channel": "SOC_ALERT", "priority": "MEDIUM"}}
        ]
        pb1_edges = [
            {"id": "e1", "source": "node_trigger", "target": "node_lookup_ip"},
            {"id": "e2", "source": "node_lookup_ip", "target": "node_cond_sev"},
            {"id": "e3", "source": "node_cond_sev", "target": "node_branch_sev"},
            {"id": "e4", "source": "node_branch_sev", "target": "node_block_ip", "source_handle": "true"},
            {"id": "e5", "source": "node_branch_sev", "target": "node_notify_analyst", "source_handle": "false"},
            {"id": "e6", "source": "node_block_ip", "target": "node_verify_quarantine"},
            {"id": "e7", "source": "node_verify_quarantine", "target": "node_verify_benign"},
            {"id": "e8", "source": "node_verify_benign", "target": "node_add_note"}
        ]

        cursor.execute("""
        INSERT INTO soar_playbooks (
            playbook_id, name, description, category, status, current_version,
            trigger_type, trigger_config_json, owner, required_permissions
        ) VALUES (?, ?, ?, ?, 'PUBLISHED', 1, 'NEW_INCIDENT', ?, 'admin@sentinel.sec', ?)
        """, (
            "PB-SQLI-CONTAINMENT",
            "SQL Injection Autonomous Containment & Dual-Probe Verification",
            "Automatic dynamic WAF quarantine and dual-probe perimeter verification for SQL injection attacks.",
            "INJECTION",
            json.dumps({"category": "INJECTION"}),
            json.dumps(["soc:analyst", "soc:admin"])
        ))
        cursor.execute("""
        INSERT INTO soar_playbook_versions (
            playbook_id, version, nodes_json, edges_json, is_published, change_summary, created_by
        ) VALUES (?, 1, ?, ?, 1, 'Production baseline SQLi containment playbook', 'admin@sentinel.sec')
        """, ("PB-SQLI-CONTAINMENT", json.dumps(pb1_nodes), json.dumps(pb1_edges)))

        # Playbook 2: Credential Stuffing & Session Revocation
        pb2_nodes = [
            {"id": "node_trigger", "type": "trigger_rule_matched", "name": "Brute Force Rule Match", "position": {"x": 80, "y": 180}, "config": {"rule_id": "AUTH-001"}},
            {"id": "node_lookup_incident", "type": "lookup_incident", "name": "Fetch Incident Dossier", "position": {"x": 320, "y": 180}, "config": {}},
            {"id": "node_block_ip", "type": "action_block_ip", "name": "Quarantine Attacker IP", "position": {"x": 560, "y": 180}, "config": {"duration_seconds": 180, "reason": "Credential Stuffing Quarantine"}},
            {"id": "node_approval_account", "type": "approval_high_impact", "name": "Account Lockout Approval", "position": {"x": 800, "y": 180}, "config": {"approver_role": "admin", "impact_desc": "Lock targeted account to prevent credential compromise."}},
            {"id": "node_branch_appr", "type": "branch_approval", "name": "Approval Branch", "position": {"x": 1040, "y": 180}, "config": {}},
            {"id": "node_disable_acc", "type": "action_disable_account", "name": "Disable Test Account", "position": {"x": 1280, "y": 100}, "config": {}},
            {"id": "node_revoke_session", "type": "action_revoke_session", "name": "Revoke Active Sessions", "position": {"x": 1520, "y": 100}, "config": {}},
            {"id": "node_verify_session", "type": "verify_session_revoked", "name": "Verify Token Invalidation", "position": {"x": 1760, "y": 100}, "config": {}},
            {"id": "node_alert_only", "type": "action_notify_analyst", "name": "Log Approval Rejection", "position": {"x": 1280, "y": 280}, "config": {"channel": "AUDIT_LOG", "priority": "LOW"}}
        ]
        pb2_edges = [
            {"id": "e1", "source": "node_trigger", "target": "node_lookup_incident"},
            {"id": "e2", "source": "node_lookup_incident", "target": "node_block_ip"},
            {"id": "e3", "source": "node_block_ip", "target": "node_approval_account"},
            {"id": "e4", "source": "node_approval_account", "target": "node_branch_appr"},
            {"id": "e5", "source": "node_branch_appr", "target": "node_disable_acc", "source_handle": "approved"},
            {"id": "e6", "source": "node_branch_appr", "target": "node_alert_only", "source_handle": "rejected"},
            {"id": "e7", "source": "node_disable_acc", "target": "node_revoke_session"},
            {"id": "e8", "source": "node_revoke_session", "target": "node_verify_session"}
        ]
        cursor.execute("""
        INSERT INTO soar_playbooks (
            playbook_id, name, description, category, status, current_version,
            trigger_type, trigger_config_json, owner, required_permissions
        ) VALUES (?, ?, ?, ?, 'PUBLISHED', 1, 'DETECTION_RULE_MATCHED', ?, 'admin@sentinel.sec', ?)
        """, (
            "PB-CRED-STUFFING-LOCKDOWN",
            "Credential Stuffing Quarantine & Targeted Session Revocation",
            "Quarantines high-velocity brute force attacks and invalidates compromised consumer session tokens.",
            "AUTHENTICATION",
            json.dumps({"rule_id": "AUTH-001"}),
            json.dumps(["soc:analyst", "soc:admin"])
        ))
        cursor.execute("""
        INSERT INTO soar_playbook_versions (
            playbook_id, version, nodes_json, edges_json, is_published, change_summary, created_by
        ) VALUES (?, 1, ?, ?, 1, 'Production credential stuffing lockdown playbook', 'admin@sentinel.sec')
        """, ("PB-CRED-STUFFING-LOCKDOWN", json.dumps(pb2_nodes), json.dumps(pb2_edges)))

        # Playbook 3: DoS Rate-Limit Adaptive Throttling
        pb3_nodes = [
            {"id": "node_trigger", "type": "trigger_security_event", "name": "HTTP Flood Event", "position": {"x": 80, "y": 180}, "config": {"event_type": "RATE_LIMIT"}},
            {"id": "node_rate_limit", "type": "action_apply_rate_limit", "name": "Apply Route Rate Limit", "position": {"x": 320, "y": 180}, "config": {"duration_seconds": 120, "threshold": 5}},
            {"id": "node_verify_benign", "type": "verify_benign_traffic", "name": "Verify Store Availability", "position": {"x": 560, "y": 180}, "config": {"target_path": "/api/shop/products", "expected_code": 200}},
            {"id": "node_report", "type": "action_generate_report", "name": "Compile DoS Telemetry", "position": {"x": 800, "y": 180}, "config": {"format": "json"}}
        ]
        pb3_edges = [
            {"id": "e1", "source": "node_trigger", "target": "node_rate_limit"},
            {"id": "e2", "source": "node_rate_limit", "target": "node_verify_benign"},
            {"id": "e3", "source": "node_verify_benign", "target": "node_report"}
        ]
        cursor.execute("""
        INSERT INTO soar_playbooks (
            playbook_id, name, description, category, status, current_version,
            trigger_type, trigger_config_json, owner, required_permissions
        ) VALUES (?, ?, ?, ?, 'PUBLISHED', 1, 'SECURITY_EVENT', ?, 'admin@sentinel.sec', ?)
        """, (
            "PB-DOS-RATE-SHAPER",
            "Denial of Service Adaptive Throttling & Storefront Preservation",
            "Enforces dynamic request rate-limiting on offending endpoints while validating customer browsing.",
            "RATE_LIMIT",
            json.dumps({"event_type": "RATE_LIMIT"}),
            json.dumps(["soc:analyst"])
        ))
        cursor.execute("""
        INSERT INTO soar_playbook_versions (
            playbook_id, version, nodes_json, edges_json, is_published, change_summary, created_by
        ) VALUES (?, 1, ?, ?, 1, 'Production baseline DoS rate-shaping playbook', 'admin@sentinel.sec')
        """, ("PB-DOS-RATE-SHAPER", json.dumps(pb3_nodes), json.dumps(pb3_edges)))

        # Playbook 4: BOLA / Unauthorized Access Containment
        pb4_nodes = [
            {"id": "node_trigger", "type": "trigger_incident", "name": "BOLA Incident Trigger", "position": {"x": 80, "y": 180}, "config": {"category": "AUTHORIZATION"}},
            {"id": "node_assign", "type": "action_assign_incident", "name": "Assign Tier-2 Lead", "position": {"x": 320, "y": 180}, "config": {"analyst": "alex.rivera@sentinel.sec", "reason": "BOLA authorization breach escalation"}},
            {"id": "node_revoke_session", "type": "action_revoke_session", "name": "Revoke Suspect Token", "position": {"x": 560, "y": 180}, "config": {}},
            {"id": "node_note", "type": "action_add_note", "name": "Append Incident Audit", "position": {"x": 800, "y": 180}, "config": {"note_template": "Session token invalidated. Assigned to tier-2 lead for authorization audit."}}
        ]
        pb4_edges = [
            {"id": "e1", "source": "node_trigger", "target": "node_assign"},
            {"id": "e2", "source": "node_assign", "target": "node_revoke_session"},
            {"id": "e3", "source": "node_revoke_session", "target": "node_note"}
        ]
        cursor.execute("""
        INSERT INTO soar_playbooks (
            playbook_id, name, description, category, status, current_version,
            trigger_type, trigger_config_json, owner, required_permissions
        ) VALUES (?, ?, ?, ?, 'DRAFT', 1, 'NEW_INCIDENT', ?, 'admin@sentinel.sec', ?)
        """, (
            "PB-BOLA-AUTH-RECOVERY",
            "BOLA Authorization Containment & Session Quarantine",
            "Rapid containment of broken object-level authorization attempts with session revocation and analyst handoff.",
            "AUTHENTICATION",
            json.dumps({"category": "AUTHORIZATION"}),
            json.dumps(["soc:analyst", "soc:admin"])
        ))
        cursor.execute("""
        INSERT INTO soar_playbook_versions (
            playbook_id, version, nodes_json, edges_json, is_published, change_summary, created_by
        ) VALUES (?, 1, ?, ?, 0, 'Initial draft BOLA containment playbook', 'admin@sentinel.sec')
        """, ("PB-BOLA-AUTH-RECOVERY", json.dumps(pb4_nodes), json.dumps(pb4_edges)))

        # Seed initial historical executions for realistic metrics
        cursor.execute("""
        INSERT INTO soar_executions (
            execution_id, playbook_id, playbook_version, playbook_name, trigger_source,
            execution_mode, status, verification_status, duration_ms, started_at, completed_at
        ) VALUES (?, ?, 1, ?, 'INCIDENT', 'LIVE', 'COMPLETED', 'VERIFIED_CONTAINED', 42.8, datetime('now', '-2 hours'), datetime('now', '-2 hours', '+42 seconds'))
        """, ("EXEC-20261101-HIST1", "PB-SQLI-CONTAINMENT", "SQL Injection Autonomous Containment & Dual-Probe Verification"))

        cursor.execute("""
        INSERT INTO soar_executions (
            execution_id, playbook_id, playbook_version, playbook_name, trigger_source,
            execution_mode, status, verification_status, duration_ms, started_at, completed_at
        ) VALUES (?, ?, 1, ?, 'INCIDENT', 'LIVE', 'COMPLETED', 'VERIFIED_CONTAINED', 31.4, datetime('now', '-1 day'), datetime('now', '-1 day', '+31 seconds'))
        """, ("EXEC-20261101-HIST2", "PB-CRED-STUFFING-LOCKDOWN", "Credential Stuffing Quarantine & Targeted Session Revocation"))

        cursor.execute("""
        INSERT INTO soar_executions (
            execution_id, playbook_id, playbook_version, playbook_name, trigger_source,
            execution_mode, status, verification_status, duration_ms, started_at, completed_at
        ) VALUES (?, ?, 1, ?, 'EVENT', 'LIVE', 'COMPLETED', 'VERIFIED_CONTAINED', 18.2, datetime('now', '-3 days'), datetime('now', '-3 days', '+18 seconds'))
        """, ("EXEC-20261101-HIST3", "PB-DOS-RATE-SHAPER", "Denial of Service Adaptive Throttling & Storefront Preservation"))

        conn.commit()
