import os
from datetime import datetime
from src.simulator.network import NetworkSimulator
from src.simulator.log_generator import LogGenerator
from src.simulator.scenarios import ScenarioRunner
from src.correlation.engine import CorrelationEngine

def main():
    print("--- AutoHeal Module 3: Log Correlation Engine Test ---")
    
    # 1. Clear old data and initialize
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            if f.endswith(".csv"):
                os.remove(os.path.join(data_dir, f))
                
    network = NetworkSimulator()
    logger = LogGenerator(data_dir=data_dir)
    runner = ScenarioRunner(network, logger)
    engine = CorrelationEngine(data_dir)
    
    # 2. Simulate Normal Traffic
    start_time = datetime.now()
    print("\n[Simulating] 5 minutes of normal traffic for DEV001...")
    normal_end_time = runner.generate_normal_traffic(start_time, duration_minutes=5)
    
    # 3. Test Normal Correlation
    print("\n[Testing] Correlating logs for normal traffic window...")
    normal_incident = engine.analyze_window("DEV001", start_time, normal_end_time)
    if normal_incident:
        print(f"ALERT RAISED (Unexpected!):\n{normal_incident}")
    else:
        print("Result: No alert raised (As expected for normal traffic).")
        
    # 4. Simulate Attack A
    print("\n[Simulating] Attack A (Failed logins + Exfiltration) on DEV001...")
    attack_start = normal_end_time
    attack_end = runner.run_attack_a(attack_start, "DEV001")
    
    # 5. Test Attack Correlation
    print("\n[Testing] Correlating logs for attack window...")
    attack_incident = engine.analyze_window("DEV001", attack_start, attack_end)
    
    if attack_incident:
        print("\n=== COMBINED ALERT PRODUCED ===")
        print(f"Severity: {attack_incident.severity}")
        print(f"Device: {attack_incident.device_id}")
        print(f"Time: {attack_incident.timestamp}")
        print(f"Reason: {attack_incident.reason}")
        print(f"Total Related Events: {len(attack_incident.events)}")
        print("\nSample of Related Events:")
        for event in attack_incident.events[:4]:
            evt_type = "Firewall" if "bytes_sent" in event else "Login" if "status" in event else "DNS" if "domain" in event else "Device"
            print(f"  - [{evt_type}] {event}")
        print("  ... (more events combined into this single alert) ...")
    else:
        print("ERROR: No alert was raised for the attack!")

if __name__ == "__main__":
    main()
