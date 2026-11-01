import unittest
import os
from datetime import datetime, timedelta
from src.simulator.network import NetworkSimulator
from src.simulator.log_generator import LogGenerator
from src.simulator.scenarios import ScenarioRunner
from src.agents.detection_agent import DetectionAgent
from src.agents.response_agent import ResponseAgent
from src.agents.verification_agent import VerificationAgent

class TestAgents(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "data_test_agents")
        os.makedirs(self.data_dir, exist_ok=True)
        for f in os.listdir(self.data_dir):
            if f.endswith(".csv"):
                try: os.remove(os.path.join(self.data_dir, f))
                except: pass
                
        self.network = NetworkSimulator()
        self.logger = LogGenerator(self.data_dir)
        self.runner = ScenarioRunner(self.network, self.logger)
        self.detect = DetectionAgent(self.data_dir)
        self.response = ResponseAgent(self.network)
        self.verify = VerificationAgent(self.data_dir, self.network)

    def test_detection_agent_nominal(self):
        start = datetime.now()
        end = self.runner.generate_normal_traffic(start, duration_minutes=5)
        incident = self.detect.run("DEV001", end, window_minutes=5)
        self.assertIsNone(incident)

    def test_detection_and_response_lifecycle(self):
        start = datetime.now()
        end = self.runner.run_attack_a(start, "DEV001")
        incident = self.detect.run("DEV001", end, window_minutes=5)
        self.assertIsNotNone(incident)
        self.assertEqual(incident.device_id, "DEV001")
        
        # Test initial response (ISOLATE)
        action = self.response.run(incident)
        self.assertEqual(action, "ISOLATE")
        self.assertEqual(self.network.devices["DEV001"].state, "Isolated")
        
        # Test escalation when isolated device continues attack
        action_escalated = self.response.run(incident)
        self.assertEqual(action_escalated, "BLOCK")
        self.assertEqual(self.network.devices["DEV001"].state, "Blocked")

    def test_verification_agent(self):
        start = datetime.now()
        # Normal traffic -> verification succeeds
        end = self.runner.generate_normal_traffic(start, duration_minutes=5)
        is_fixed = self.verify.run("DEV001", "ISOLATE", end, window_minutes=5)
        self.assertTrue(is_fixed)
        
        # Attack traffic -> verification fails
        end_atk = self.runner.run_attack_a(end, "DEV001")
        is_fixed_atk = self.verify.run("DEV001", "ISOLATE", end_atk, window_minutes=5)
        self.assertFalse(is_fixed_atk)

if __name__ == '__main__':
    unittest.main()
