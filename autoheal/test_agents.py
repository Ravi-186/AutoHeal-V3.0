import os
from datetime import datetime, timedelta
from src.simulator.network import NetworkSimulator
from src.simulator.log_generator import LogGenerator
from src.simulator.scenarios import ScenarioRunner

from src.agents.detection_agent import DetectionAgent
from src.agents.response_agent import ResponseAgent
from src.agents.verification_agent import VerificationAgent

def main():
    print("--- AutoHeal Module 4: Testing Standalone Agents ---\n")
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    
    # 1. Setup simulated environment
    network = NetworkSimulator()
    logger = LogGenerator(data_dir)
    runner = ScenarioRunner(network, logger)
    
    # Initialize Agents
    detect_agent = DetectionAgent(data_dir)
    response_agent = ResponseAgent(network)
    verify_agent = VerificationAgent(data_dir, network)
    
    current_time = datetime.now()
    
    print("--- 1. Testing Detection Agent (Normal Traffic) ---")
    current_time = runner.generate_normal_traffic(current_time, duration_minutes=5)
    incident = detect_agent.run("DEV001", current_time, window_minutes=5)
    
    print("\n--- 2. Testing Detection Agent (Attack Traffic) ---")
    atk_start = current_time
    current_time = runner.run_attack_a(atk_start, "DEV001")
    incident = detect_agent.run("DEV001", current_time, window_minutes=5)
    
    print("\n--- 3. Testing Response Agent (Initial Isolate) ---")
    action_taken = response_agent.run(incident)
    print(f"Network state for DEV001 is now: {network.devices['DEV001'].state}")
    
    print("\n--- 4. Testing Verification Agent (Failure -> Escalate to Block) ---")
    print("  [Simulator] Simulating that the attack miraculously continued (isolation bypassed)...")
    cont_start = current_time
    current_time = runner.run_attack_a(cont_start, "DEV001") 
    
    # Verification Agent checks the last 5 minutes
    is_fixed = verify_agent.run("DEV001", action_taken, current_time, window_minutes=5)
    
    if not is_fixed:
        print("\n--- 5. Testing Response Agent (Escalation) ---")
        action_taken_2 = response_agent.run(incident)
        print(f"Network state for DEV001 is now: {network.devices['DEV001'].state}")
        
        print("\n--- 6. Testing Verification Agent (Success) ---")
        print("  [Simulator] Simulating that the block worked (no new logs generated)...")
        # Time passes without any attacks
        current_time += timedelta(minutes=5)
        is_fixed_2 = verify_agent.run("DEV001", action_taken_2, current_time, window_minutes=5)

if __name__ == "__main__":
    main()
