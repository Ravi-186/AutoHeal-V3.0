import unittest
import os
from datetime import datetime
from src.correlation.engine import CorrelationEngine
from src.simulator.network import NetworkSimulator
from src.simulator.log_generator import LogGenerator
from src.simulator.scenarios import ScenarioRunner

class TestCorrelationEngine(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "data_test")
        os.makedirs(self.data_dir, exist_ok=True)
        # Clear old data
        for f in os.listdir(self.data_dir):
            if f.endswith(".csv"):
                os.remove(os.path.join(self.data_dir, f))
                
        self.network = NetworkSimulator()
        self.logger = LogGenerator(self.data_dir)
        self.runner = ScenarioRunner(self.network, self.logger)
        self.engine = CorrelationEngine(self.data_dir)

    def test_normal_traffic_no_alert(self):
        start = datetime.now()
        end = self.runner.generate_normal_traffic(start, duration_minutes=5)
        
        # Normal traffic should return None (no incident)
        incident = self.engine.analyze_window("DEV001", start, end)
        self.assertIsNone(incident)

    def test_attack_traffic_raises_alert(self):
        start = datetime.now()
        end = self.runner.run_attack_a(start, "DEV001")
        
        # Attack traffic should raise an Incident
        incident = self.engine.analyze_window("DEV001", start, end)
        self.assertIsNotNone(incident)
        self.assertEqual(incident.device_id, "DEV001")
        self.assertEqual(incident.severity, "HIGH")

if __name__ == '__main__':
    unittest.main()
