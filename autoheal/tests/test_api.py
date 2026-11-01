import unittest
from fastapi.testclient import TestClient
from server import app

class TestFastAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "HEALTHY")
        self.assertTrue(data["model_loaded"])
        self.assertGreater(data["devices_monitored"], 0)

    def test_get_state(self):
        res = self.client.get("/api/state")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("devices", data)
        self.assertIn("active_threats", data)
        self.assertIn("logs", data)

    def test_attack_triggers(self):
        for atk in ["A", "B", "C", "D"]:
            res = self.client.post(f"/api/attack/{atk}")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["status"], "success")

    def test_invalid_attack_trigger(self):
        res = self.client.post("/api/attack/INVALID")
        self.assertEqual(res.status_code, 400)

    def test_detection_cycle(self):
        # Trigger attack A, then detect
        self.client.post("/api/attack/A")
        res = self.client.post("/api/detect")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("threat_found", data)
        self.assertTrue(data["threat_found"])

    def test_device_overrides(self):
        target = "CORP-LAPTOP-142"
        # Isolate
        res_iso = self.client.post(f"/api/device/{target}/isolate")
        self.assertEqual(res_iso.status_code, 200)
        self.assertEqual(res_iso.json()["current_state"], "Isolated")
        
        # Block
        res_blk = self.client.post(f"/api/device/{target}/block")
        self.assertEqual(res_blk.status_code, 200)
        self.assertEqual(res_blk.json()["current_state"], "Blocked")
        
        # Restore
        res_rst = self.client.post(f"/api/device/{target}/restore")
        self.assertEqual(res_rst.status_code, 200)
        self.assertEqual(res_rst.json()["current_state"], "Normal")

    def test_reset_sandbox(self):
        res = self.client.post("/api/reset")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "success")

if __name__ == '__main__':
    unittest.main()
