"""
Executive SOC Command Center & Live Security Analytics Test Suite (Phase 2)
Tests all real backend metrics, timeline bucketing, activity feeds, subsystem health,
and HTML DOM elements.
"""

import unittest
from fastapi.testclient import TestClient
from server import app
from shopsphere.database import get_db_connection

class TestExecutiveSOCCommandCenter(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_executive_dashboard_dom_elements(self):
        """Verify that GET / returns the complete Executive SOC Command Center UI structure."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.text

        # 1. Executive Header Ribbon & Controls
        self.assertIn("Executive SOC Command Center", html)
        self.assertIn("overviewSystemStatusBadge", html)
        self.assertIn("overviewLastUpdated", html)
        self.assertIn("rangeBtn1h", html)
        self.assertIn("rangeBtn24h", html)
        self.assertIn("rangeBtn7d", html)
        self.assertIn("rangeBtn30d", html)
        self.assertIn("rangeBtnAll", html)
        self.assertIn("btnDashboardAutoRefresh", html)
        self.assertIn("btnRefreshDashboard", html)

        # 2. 8 KPI Cards
        self.assertIn("kpiCardTotalEvents", html)
        self.assertIn("statTotalEvents", html)
        self.assertIn("kpiCardActiveIncidents", html)
        self.assertIn("statActiveIncidents", html)
        self.assertIn("kpiCardCriticalIncidents", html)
        self.assertIn("statCriticalIncidents", html)
        self.assertIn("kpiCardResolvedIncidents", html)
        self.assertIn("statResolvedIncidents", html)
        self.assertIn("kpiCardVerifiedRemediations", html)
        self.assertIn("statVerifiedRemediations", html)
        self.assertIn("kpiCardMTTD", html)
        self.assertIn("statMTTD", html)
        self.assertIn("kpiCardMTTR", html)
        self.assertIn("statMTTR", html)
        self.assertIn("kpiCardAvailability", html)
        self.assertIn("statAvailability", html)

        # 3. Security Analytics Charts
        self.assertIn("securityEventTimelineCanvas", html)
        self.assertIn("timelineCategorySelect", html)
        self.assertIn("timelineSeveritySelect", html)
        self.assertIn("threatSeverityDonutCanvas", html)
        self.assertIn("sevModeEventsBtn", html)
        self.assertIn("sevModeIncidentsBtn", html)

        # 4. Lifecycle Pipeline & Detection Rules
        self.assertIn("lifecycleStagesContainer", html)
        self.assertIn("stageStepNew", html)
        self.assertIn("stageStepTriaged", html)
        self.assertIn("stageStepInvestigating", html)
        self.assertIn("stageStepContainment", html)
        self.assertIn("stageStepRemediation", html)
        self.assertIn("stageStepVerification", html)
        self.assertIn("stageStepResolved", html)
        self.assertIn("detectionRulesTableBody", html)

        # 5. Remediation & Self-Healing
        self.assertIn("remediationSuccessRateVal", html)
        self.assertIn("healingAttackerProbeStatus", html)
        self.assertIn("healingBenignProbeStatus", html)

        # 6. Live Activity Feed & Active Incidents Queue
        self.assertIn("executiveActivityFeedContainer", html)
        self.assertIn("overviewIncidentsTableBody", html)

        # 7. 8-Subsystem System Health Panel
        self.assertIn("healthSubsystemsContainer", html)
        self.assertIn("overallSystemHealthBadge", html)

    def test_metrics_time_ranges(self):
        """Test /api/security/metrics across all supported time ranges."""
        ranges = ["1h", "24h", "7d", "30d", "all"]
        for tr in ranges:
            res = self.client.get(f"/api/security/metrics?time_range={tr}")
            self.assertEqual(res.status_code, 200, f"Failed for time range {tr}")
            data = res.json()

            # Backwards compatible keys
            self.assertIn("total_events_recorded", data)
            self.assertIn("total_incidents", data)
            self.assertIn("active_threats", data)
            self.assertIn("active_blocked_ips", data)
            self.assertIn("incidents_by_severity", data)

            # Executive analytics keys
            self.assertIn("total_security_events", data)
            self.assertIn("active_incidents", data)
            self.assertIn("critical_incidents", data)
            self.assertIn("resolved_incidents", data)
            self.assertIn("verified_remediations", data)
            self.assertIn("mean_time_to_detect_ms", data)
            self.assertIn("mean_time_to_respond_ms", data)
            self.assertIn("system_availability_percent", data)
            self.assertIn("threat_severity_distribution", data)
            self.assertIn("incident_lifecycle", data)
            self.assertIn("detection_rules", data)
            self.assertIn("remediation_analytics", data)
            self.assertIn("self_healing_status", data)

    def test_metrics_against_sqlite_database(self):
        """Verify that metrics originate from actual persisted SQLite rows, zero fabrication."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM security_events")
            db_events_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM security_incidents")
            db_incidents_count = cursor.fetchone()[0]

        res = self.client.get("/api/security/metrics?time_range=all")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["total_security_events"], db_events_count)
        self.assertEqual(data["total_incidents"], db_incidents_count)
        self.assertGreater(data["total_security_events"], 0)
        self.assertGreater(data["total_incidents"], 0)

    def test_analytics_timeline_endpoint(self):
        """Verify timeline aggregation with uniform slices and filters."""
        # Test default uniform 12 slices
        res = self.client.get("/api/security/analytics/timeline?time_range=all&slices=12")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["labels"]), 12)
        self.assertEqual(len(data["counts"]), 12)
        self.assertEqual(sum(data["counts"]), data["total_events"])
        self.assertGreater(data["total_events"], 0)

        # Test severity filtering
        res_crit = self.client.get("/api/security/analytics/timeline?time_range=all&severity=CRITICAL&slices=12")
        self.assertEqual(res_crit.status_code, 200)
        data_crit = res_crit.json()
        self.assertLessEqual(data_crit["total_events"], data["total_events"])

        # Test category filtering
        res_inj = self.client.get("/api/security/analytics/timeline?time_range=all&category=INJ&slices=12")
        self.assertEqual(res_inj.status_code, 200)
        data_inj = res_inj.json()
        self.assertLessEqual(data_inj["total_events"], data["total_events"])

    def test_live_activity_feed_endpoint(self):
        """Verify real-time activity feed contains events and incidents with required fields."""
        res = self.client.get("/api/security/activity/feed?limit=15")
        self.assertEqual(res.status_code, 200)
        feed = res.json()
        self.assertIsInstance(feed, list)
        self.assertGreater(len(feed), 0)
        self.assertLessEqual(len(feed), 15)

        first = feed[0]
        self.assertIn("id", first)
        self.assertIn("timestamp", first)
        self.assertIn("type", first)
        self.assertIn("title", first)
        self.assertIn("severity", first)
        self.assertIn("source_ip", first)

    def test_detailed_system_health_endpoint(self):
        """Verify all 8 subsystems report live operational health and latencies."""
        res = self.client.get("/api/security/health/detailed")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["total_subsystems"], 8)
        self.assertIn("subsystems", data)
        subsystems = {s["name"]: s for s in data["subsystems"]}

        expected_names = [
            "FastAPI Core Daemon",
            "SQLite WAL Telemetry Store",
            "AppSec Telemetry Ingestion",
            "Autonomous Correlation Worker",
            "Perimeter Quarantine Queue",
            "Rule-Based Detection Engine",
            "Dual-Probe Verification Agent",
            "AI Threat Classifier / Ollama"
        ]

        for name in expected_names:
            self.assertIn(name, subsystems, f"Missing subsystem: {name}")
            sub = subsystems[name]
            self.assertIn(sub["status"], ["healthy", "degraded", "unavailable", "unknown"])
            self.assertIsInstance(sub["latency_ms"], (int, float))
            self.assertIn("details", sub)

    def test_incident_lifecycle_stages(self):
        """Verify all 7 incident lifecycle stages are reported."""
        res = self.client.get("/api/security/metrics?time_range=all")
        self.assertEqual(res.status_code, 200)
        lifecycle = res.json()["incident_lifecycle"]

        stages = ["new", "triaged", "investigating", "containment", "remediation", "verification", "resolved"]
        for st in stages:
            self.assertIn(st, lifecycle)
            self.assertIsInstance(lifecycle[st], int)
            self.assertGreaterEqual(lifecycle[st], 0)

    def test_dual_probe_verification(self):
        """Verify self-healing status includes attacker and benign user verification."""
        res = self.client.get("/api/security/metrics?time_range=all")
        self.assertEqual(res.status_code, 200)
        sh = res.json()["self_healing_status"]

        self.assertIn("attacker_verification", sh)
        self.assertIn("benign_user_verification", sh)
        self.assertIn("dual_probe_confirmed", sh)
        self.assertTrue(sh["attacker_verification"])
        self.assertTrue(sh["benign_user_verification"])
        self.assertTrue(sh["dual_probe_confirmed"])

if __name__ == "__main__":
    unittest.main()
