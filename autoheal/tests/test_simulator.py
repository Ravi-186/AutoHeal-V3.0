import unittest
import os
from datetime import datetime
from src.simulator.network import NetworkSimulator
from src.simulator.log_generator import LogGenerator
from src.simulator.scenarios import ScenarioRunner

class TestSimulator(unittest.TestCase):
    def setUp(self):
        self.network = NetworkSimulator()
        self.data_dir = os.path.join(os.path.dirname(__file__), "data_test")
        os.makedirs(self.data_dir, exist_ok=True)
        self.logger = LogGenerator(self.data_dir)
        self.runner = ScenarioRunner(self.network, self.logger)

    def test_isolate_device(self):
        self.assertEqual(self.network.devices["DEV001"].state, "Normal")
        self.network.isolate_device("DEV001")
        self.assertEqual(self.network.devices["DEV001"].state, "Isolated")
        self.assertGreater(self.network.devices["DEV001"].risk_score, 0)

    def test_block_device(self):
        self.network.block_device("DEV002")
        self.assertEqual(self.network.devices["DEV002"].state, "Blocked")
        self.assertEqual(self.network.devices["DEV002"].risk_score, 100)

    def test_restore_device(self):
        self.network.isolate_device("DEV001")
        self.network.restore_device("DEV001")
        self.assertEqual(self.network.devices["DEV001"].state, "Normal")
        self.assertEqual(self.network.devices["DEV001"].risk_score, 0)

    def test_zero_trust_zones(self):
        dc = self.network.devices["ENT-CORE-DC-01"]
        self.assertEqual(dc.zone, "Identity Enclave (Tier 0)")
        db = self.network.devices["ENT-HR-DB-01"]
        self.assertEqual(db.zone, "Data Enclave (PCI/PII)")

    def test_scenarios_a_b_c_d(self):
        t0 = datetime.now()
        t1 = self.runner.run_attack_a(t0, "CORP-LAPTOP-142")
        self.assertGreater(t1, t0)
        t2 = self.runner.run_attack_b(t1, "ENT-APP-SRV-01")
        self.assertGreater(t2, t1)
        t3 = self.runner.run_attack_c(t2, "ENT-HR-DB-01")
        self.assertGreater(t3, t2)
        t4 = self.runner.run_attack_d(t3, "ENT-PAYMENT-DB")
        self.assertGreater(t4, t3)

if __name__ == '__main__':
    unittest.main()
