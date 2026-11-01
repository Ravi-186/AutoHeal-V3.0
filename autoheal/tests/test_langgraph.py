import unittest
import os
from datetime import datetime, timedelta
from src.simulator.network import NetworkSimulator
from src.simulator.log_generator import LogGenerator
from src.simulator.scenarios import ScenarioRunner
from src.agents.detection_agent import DetectionAgent
from src.agents.response_agent import ResponseAgent
from src.agents.verification_agent import VerificationAgent
from src.graph.workflow import AutoHealGraph

class TestLangGraphWorkflow(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "data_test_graph")
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
        self.graph_manager = AutoHealGraph(self.detect, self.response, self.verify, max_retries=2)

    def test_workflow_nominal_terminates_immediately(self):
        t0 = datetime.now()
        t1 = self.runner.generate_normal_traffic(t0, duration_minutes=5)
        
        initial_state = {
            "device_id": "DEV001",
            "current_time": t1,
            "incident": None,
            "action_taken": None,
            "is_verified": False,
            "retry_count": 0,
            "audit_trail": []
        }
        
        final_state = dict(initial_state)
        for output in self.graph_manager.graph.stream(initial_state):
            for node, state_update in output.items():
                if isinstance(state_update, dict):
                    final_state.update(state_update)
                    
        # No incident should be raised, action_taken should be None
        self.assertIsNone(final_state["incident"])
        self.assertIsNone(final_state["action_taken"])

    def test_workflow_attack_neutralization(self):
        t0 = datetime.now()
        t1 = self.runner.run_attack_a(t0, "CORP-LAPTOP-142")
        
        initial_state = {
            "device_id": "CORP-LAPTOP-142",
            "current_time": t1,
            "incident": None,
            "action_taken": None,
            "is_verified": False,
            "retry_count": 0,
            "audit_trail": []
        }
        
        final_state = dict(initial_state)
        for output in self.graph_manager.graph.stream(initial_state):
            for node, state_update in output.items():
                if isinstance(state_update, dict):
                    final_state.update(state_update)
                    
        self.assertIsNotNone(final_state["incident"])
        self.assertIn(final_state["action_taken"], ["ISOLATE", "BLOCK"])
        self.assertGreater(len(final_state["audit_trail"]), 0)

if __name__ == '__main__':
    unittest.main()
