import os
from datetime import datetime
from src.simulator.network import NetworkSimulator
from src.simulator.log_generator import LogGenerator
from src.simulator.scenarios import ScenarioRunner

def count_and_sample(filepath, n_samples=2):
    if not os.path.exists(filepath):
        return 0, []
    with open(filepath, 'r') as f:
        lines = f.readlines()
    if len(lines) <= 1:
        return 0, []
    samples = lines[1:n_samples+1]
    return len(lines) - 1, samples

def main():
    print("--- AutoHeal Module 1: Network and Log Simulator ---")
    
    network = NetworkSimulator()
    print(f"Initialized {len(network.devices)} devices.")
    
    # Initialize logger
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    logger = LogGenerator(data_dir=data_dir)
    print(f"Log files initialized in {data_dir}")
    
    runner = ScenarioRunner(network, logger)
    
    start_time = datetime.now()
    
    print("\nGenerating 10 minutes of normal traffic...")
    current_time = runner.generate_normal_traffic(start_time, duration_minutes=10)
    
    print("\nRunning Attack A on DEV001...")
    current_time = runner.run_attack_a(current_time, "DEV001")
    
    print("\nRunning Attack B on DEV002...")
    current_time = runner.run_attack_b(current_time, "DEV002")
    
    print("\nRunning Attack C on IOT001...")
    current_time = runner.run_attack_c(current_time, "IOT001")
    
    print("\nSimulating device isolation for DEV001 (Response Agent mock)...")
    network.isolate_device("DEV001")
    
    print(f"\nFinal Network Status:\n{network.get_status()}")
    
    print("\n--- Summary & Samples of Generated Logs ---")
    files = [
        ("Firewall Logs", logger.firewall_path),
        ("Login Logs", logger.login_path),
        ("DNS Logs", logger.dns_path),
        ("Device Logs", logger.device_path)
    ]
    for name, path in files:
        count, samples = count_and_sample(path, n_samples=2)
        print(f"{name}: {count} rows")
        for s in samples:
            print(f"  {s.strip()}")

if __name__ == "__main__":
    main()
