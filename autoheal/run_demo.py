import os
from datetime import datetime, timedelta
from src.simulator.network import NetworkSimulator
from src.simulator.log_generator import LogGenerator
from src.simulator.scenarios import ScenarioRunner
from src.agents.detection_agent import DetectionAgent
from src.agents.response_agent import ResponseAgent
from src.agents.verification_agent import VerificationAgent
from src.graph.workflow import AutoHealGraph

def main():
    print("=====================================================")
    print(">>> AutoHeal End-to-End Demo")
    print("=====================================================")
    
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            if f.endswith(".csv"):
                try:
                    os.remove(os.path.join(data_dir, f))
                except:
                    pass
                
    network = NetworkSimulator()
    logger = LogGenerator(data_dir)
    runner = ScenarioRunner(network, logger)
    
    detect_agent = DetectionAgent(data_dir)
    response_agent = ResponseAgent(network)
    verify_agent = VerificationAgent(data_dir, network)
    
    graph_manager = AutoHealGraph(detect_agent, response_agent, verify_agent, max_retries=2)
    app = graph_manager.graph
    
    current_time = datetime.now()
    device = "CORP-LAPTOP-142"
    
    print(f"\n[1] Normal Operations...")
    current_time = runner.generate_normal_traffic(current_time, duration_minutes=5)
    print("    - Users are logging in normally. Traffic is standard.")
    
    print(f"\n[2] Attacker initiates Brute Force & Data Exfiltration on {device}...")
    current_time = runner.run_attack_a(current_time, device)
    
    # We patch the verify node to simulate an attacker dynamically trying to bypass the isolation
    original_verify = graph_manager.node_verify
    def patched_verify(state):
        if network.devices[state['device_id']].state == "Isolated":
            print(f"\n    [!] [Simulator Hack] Attacker bypassed the isolation! Generating new attack logs...")
            network.devices[state['device_id']].state = "Normal"
            runner.run_attack_a(state['current_time'] + timedelta(minutes=4, seconds=5), state['device_id'])
            network.devices[state['device_id']].state = "Isolated"
        else:
            print(f"\n    [+] [Simulator Hack] Device is fully blocked. No attack traffic can pass.")
        return original_verify(state)
        
    graph_manager.node_verify = patched_verify
    app = graph_manager._build_graph()
    
    initial_state = {
        "device_id": device,
        "current_time": current_time,
        "incident": None,
        "action_taken": None,
        "is_verified": False,
        "retry_count": 0
    }
    
    print("\n[3] LangGraph AutoHeal Workflow Triggered")
    print("-----------------------------------------------------")
    for output in app.stream(initial_state):
        pass # All node outputs are printed directly by the agents
        
    print("\n-----------------------------------------------------")
    print("[SUCCESS] AutoHeal Demo Complete. Network is secure.")
    print("=====================================================")

if __name__ == "__main__":
    main()
