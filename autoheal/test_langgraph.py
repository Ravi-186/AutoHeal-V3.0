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
    print("--- AutoHeal Module 5: LangGraph Workflow ---\n")
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            if f.endswith(".csv"):
                os.remove(os.path.join(data_dir, f))
                
    network = NetworkSimulator()
    logger = LogGenerator(data_dir)
    runner = ScenarioRunner(network, logger)
    
    detect_agent = DetectionAgent(data_dir)
    response_agent = ResponseAgent(network)
    verify_agent = VerificationAgent(data_dir, network)
    
    graph_manager = AutoHealGraph(detect_agent, response_agent, verify_agent, max_retries=2)
    app = graph_manager.graph
    
    print("--- GRAPH MERMAID DIAGRAM ---")
    print(app.get_graph().draw_mermaid())
    print("-----------------------------\n")
    
    current_time = datetime.now()
    device_id = "DEV001"
    
    print("\n--- Running Story: End-to-End Attack and Self-Healing ---")
    print("\n[Simulator] Generating normal traffic...")
    current_time = runner.generate_normal_traffic(current_time, duration_minutes=5)
    
    print(f"\n[Simulator] Launching Attack A on {device_id}...")
    current_time = runner.run_attack_a(current_time, device_id)
    
    # Hack the verify node for this test so the simulator generates 
    # logs *during* the graph execution without pausing for real time.
    original_verify = graph_manager.node_verify
    def patched_verify(state):
        if network.devices[state['device_id']].state == "Isolated":
            print(f"  [Simulator] Attacker bypassed isolation! Generating more attack logs...")
            network.devices[state['device_id']].state = "Normal"
            runner.run_attack_a(state['current_time'] + timedelta(minutes=4, seconds=5), state['device_id'])
            network.devices[state['device_id']].state = "Isolated"
        else:
            print(f"  [Simulator] Device is fully blocked. No attack traffic can pass.")
        return original_verify(state)
        
    graph_manager.node_verify = patched_verify
    # Recompile the graph so the patch takes effect!
    app = graph_manager._build_graph()
    
    initial_state = {
        "device_id": device_id,
        "current_time": current_time,
        "incident": None,
        "action_taken": None,
        "is_verified": False,
        "retry_count": 0
    }
    
    print("\n[Main] Starting LangGraph Workflow (Detect -> Respond -> Verify loop)...")
    for output in app.stream(initial_state):
        for node_name, state_update in output.items():
            print(f"--- Finished node: {node_name} ---")

if __name__ == "__main__":
    main()
