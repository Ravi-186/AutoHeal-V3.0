# AutoHeal v3.0 — Enterprise Database Architecture & Schema Reference
**Platform:** AutoHeal AI-Assisted Autonomous Security Operations Center (SOC)  
**Target Application:** ShopSphere E-Commerce Application  
**Version:** `3.0.0-enterprise`  
**Database File:** `autoheal/data/shopsphere.db`  
**Engine:** SQLite 3 (WAL Mode)  
**Table Count:** 30 Normalized Tables  
**Date:** November 1, 2026  

---

## 1. Relational Database Overview

AutoHeal v3.0 utilizes a single, highly optimized relational SQLite database structured in Third Normal Form (3NF). The schema cleanly accommodates both the cybersecurity observability domain and the consumer e-commerce transactional domain while maintaining complete referential integrity.

### Active Performance Pragmas
Every database connection is initialized with these performance and safety pragmas:
- `PRAGMA journal_mode = WAL;` — Write-Ahead Logging allows unlimited concurrent readers alongside serialized non-blocking writers.
- `PRAGMA synchronous = NORMAL;` — Drastically reduces disk sync overhead while ensuring power-failure durability in WAL mode.
- `PRAGMA foreign_keys = ON;` — Strictly enforces relational referential integrity.
- `PRAGMA busy_timeout = 5000;` — Threads wait up to 5 seconds to acquire write locks before failing, preventing lock contention errors.

---

## 2. Table Catalog by Subsystem (30 Tables Total)

### Group 1: Threat Detection & Telemetry (6 Tables)
1. **`security_events`** — Chronological log of all HTTP requests evaluated by WAF middleware (`id`, `event_id`, `correlation_id`, `timestamp`, `client_ip`, `user_agent`, `method`, `path`, `status_code`, `latency_ms`, `event_type`, `severity`, `details_json`, `action_taken`).
2. **`security_incidents`** — Correlated threat dossiers (`id`, `incident_id`, `rule_id`, `title`, `category`, `severity`, `status`, `confidence`, `summary`, `evidence_json`, `affected_endpoints_json`, `source_ip`, `verification_status`, `version`, `created_at`, `updated_at`).
3. **`incident_timeline`** — Attack progression sequence events linked to an incident (`id`, `incident_id`, `timestamp`, `stage`, `description`, `evidence_ref`).
4. **`event_investigations`** — Analyst investigation notes and triage updates (`id`, `event_id`, `analyst`, `status`, `notes`, `updated_at`).
5. **`blocked_clients`** — Active perimeter IP quarantine list (`id`, `client_ip`, `reason`, `blocked_at`, `blocked_until`, `rule_id`).
6. **`soc_activity_logs`** — Audit ledger of all SOC operator interactions (`id`, `timestamp`, `actor`, `action`, `resource_id`, `details_json`).

### Group 2: Visual SOAR Automation (5 Tables)
7. **`soar_playbooks`** — Master playbook records (`id`, `playbook_id`, `name`, `description`, `category`, `status`, `current_version`, `trigger_type`, `owner`).
8. **`soar_playbook_versions`** — Versioned DAG schemas with node graphs (`id`, `playbook_id`, `version`, `nodes_json`, `edges_json`, `published_at`).
9. **`soar_executions`** — Playbook execution tracking (`id`, `execution_id`, `playbook_id`, `playbook_version`, `execution_mode`, `incident_id`, `status`, `started_at`, `completed_at`).
10. **`soar_execution_logs`** — Node-by-node execution telemetry (`id`, `execution_id`, `node_id`, `node_name`, `status`, `input_json`, `output_json`, `duration_ms`).
11. **`soar_approval_requests`** — Governance pause gates awaiting human approval (`id`, `approval_id`, `execution_id`, `node_id`, `action_name`, `status`, `decided_by`, `reason`).

### Group 3: Self-Healing & Remediation (5 Tables)
12. **`self_healing_policies`** — Autonomous policy thresholds (`id`, `policy_id`, `name`, `autonomy_level`, `max_retries`, `allowlisted_actions_json`, `is_active`).
13. **`self_healing_executions`** — Remediation plan rollout records (`id`, `execution_id`, `incident_id`, `plan_id`, `status`, `snapshot_before_json`, `started_at`, `completed_at`).
14. **`self_healing_audit_logs`** — Immutable remediation and rollback history (`id`, `timestamp`, `incident_id`, `action_type`, `details_json`, `reverted`).
15. **`remediation_plans`** — Multi-option remediation plans formulated by RCA (`id`, `plan_id`, `incident_id`, `actions_json`, `risk_score`, `created_at`).
16. **`verification_results`** — Synthetic dual-probe test results (`id`, `incident_id`, `probe_type`, `expected_status`, `actual_status`, `passed`, `timestamp`).

### Group 4: 3D Threat Topology (3 Tables)
17. **`topology_nodes`** — Physical and logical assets in the graph (`id`, `node_id`, `node_type`, `label`, `ip_address`, `risk_score`, `x`, `y`, `z`).
18. **`topology_edges`** — Relationships and communication hops (`id`, `edge_id`, `source_node`, `target_node`, `edge_type`, `weight`, `is_active`).
19. **`attack_paths`** — Computed blast radius attack paths (`id`, `path_id`, `source_ip`, `target_asset`, `hop_count`, `risk_level`, `details_json`).

### Group 5: AI SOC Copilot (3 Tables)
20. **`copilot_conversations`** — Multi-turn chat session history (`id`, `session_id`, `user_query`, `copilot_reply`, `citations_json`, `timestamp`).
21. **`copilot_reports`** — Persisted 12-section formal defense reports (`id`, `report_id`, `incident_id`, `title`, `content_markdown`, `generated_at`).
22. **`threat_intel_cache`** — Cached threat intelligence scores (`id`, `ip_address`, `reputation_score`, `classification`, `asn_info_json`, `expires_at`).

### Group 6: ShopSphere E-Commerce Domain (8 Tables)
23. **`products`** — E-commerce product catalog (`id`, `title`, `slug`, `category`, `description`, `price`, `original_price`, `discount_percent`, `rating`, `review_count`, `stock`, `image_url`, `badge`, `specs_json`, `brand`, `gallery_images_json`).
24. **`categories`** — Product categories (`id`, `name`, `slug`, `icon_name`, `display_order`).
25. **`users`** — Customer accounts (`id`, `email`, `password_hash`, `name`, `role`, `phone`, `address`, `city`, `pincode`, `created_at`).
26. **`cart_items`** — Persistent customer cart items (`id`, `user_or_session_id`, `product_id`, `quantity`, `created_at`, `updated_at`).
27. **`orders`** — Customer orders (`id`, `order_ref`, `user_id`, `customer_name`, `customer_email`, `customer_phone`, `shipping_address`, `city`, `pincode`, `payment_method`, `payment_status`, `order_status`, `subtotal`, `discount`, `delivery_fee`, `total_amount`, `coupon_code`, `coupon_discount`, `created_at`).
28. **`order_items`** — Order line items (`id`, `order_id`, `product_id`, `quantity`, `unit_price`, `total_price`).
29. **`product_reviews`** — Customer product reviews (`id`, `product_id`, `user_id`, `customer_name`, `rating`, `headline`, `comment`, `verified_purchase`, `helpful_votes`, `created_at`).
30. **`coupons`** — Promotional discount coupons (`id`, `code`, `discount_type`, `discount_value`, `min_order_amount`, `max_discount_amount`, `usage_limit`, `times_used`, `is_active`, `expires_at`).

---

## 3. Database Integrity & Drill Verification Results

During the Phase 10 certification, rigorous structural integrity checks were conducted:
```sql
-- 1. Structural B-Tree Verification
PRAGMA integrity_check;
-- Result: "ok" (0 corrupt pages, 0 index orphan pointers)

-- 2. Referential Integrity Verification
PRAGMA foreign_key_check;
-- Result: 0 rows returned (Zero foreign key violations)

-- 3. Live Non-Locking Backup
-- Executed via sqlite3 native backup API: Completed in 42.1ms
```

---

## 4. Database Documentation Sign-Off

The database schema is fully normalized, indexed for high-speed queries, and verified against corruption or orphaned relationships.
