# AutoHeal: Autonomous Self-Healing Workflow & LangGraph Swarm

**Author:** SOAR Automation Engineer & AI Systems Lead  
**Document Ref:** `HEAL-WORKFLOW-001`  
**Date:** 2026-11-01  

---

## 1. LangGraph Multi-Agent Swarm Topology

AutoHeal uses an autonomous multi-agent state graph (`AutoHealGraph` in `src/graph/workflow.py`) with three specialized nodes:

```
          [ START ]
              │
              ▼
    +───────────────────+
    |   Detect Node     |  <-- Scans telemetry window for metric anomalies & IOCs
    +───────────────────+
              │
         Threat Found?
        /            \
      Yes             No
      /                \
     v                  v
+───────────────────+  [ END: Nominal State ]
|   Respond Node    |  <-- Selects & executes bounded defensive action (ISOLATE / BLOCK)
+───────────────────+
     │
     ▼
+───────────────────+
|   Verify Node     |  <-- Tests if action stopped attack & preserved availability
+───────────────────+
     │
Verified?
   /   \
 Yes    No (Retry < 3)
 /        \
v          v
[ END ]   [ Respond Node (Retry with Backoff) ]
```

---

## 2. Invariant Healing Execution (ShopSphere Application Level)

In addition to perimeter network defenses, AutoHeal implements application-level self-healing:
1. **Financial Invariant Enforcement:** Detects logical anomalies (e.g. negative cart totals or negative delivery fees) via `VulnerabilityManager`.
2. **Surgical Patch Application:** Applies minimal AST-based code patches to restore financial and security invariants.
3. **Regression Test Verification:** Automatically runs targeted unit tests (`test_cart_delivery_and_total_calculation`) against the patched module in an isolated environment before confirming the repair.
4. **Zero Downtime Rollback:** If the regression test fails, the patch is automatically rolled back to the previous baseline, preserving stability.
