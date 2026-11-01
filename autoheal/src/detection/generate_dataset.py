import os
from datetime import datetime, timedelta
from src.simulator.network import NetworkSimulator
from src.simulator.log_generator import LogGenerator
from src.simulator.scenarios import ScenarioRunner

def generate_data():
    """Generates a dataset with normal traffic and specific attacks."""
    network = NetworkSimulator()
    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    logger = LogGenerator(data_dir=data_dir)
    runner = ScenarioRunner(network, logger)
    
    # Generate traffic starting from a fixed time
    start_time = datetime(2023, 1, 1, 12, 0, 0)
    current_time = start_time
    
    # Store attack periods (device_id, start_time, end_time) to label them later
    attack_labels = [] 
    
    print("Generating 2 hours of normal background traffic...")
    current_time = runner.generate_normal_traffic(current_time, duration_minutes=120)
    
    print("Injecting multiple attack scenarios for training...")
    for i in range(10):
        # Attack A
        dev_id = f"DEV00{1 + i%5}"
        atk_a_start = current_time
        current_time = runner.run_attack_a(current_time, dev_id)
        attack_labels.append((dev_id, atk_a_start, current_time))
        current_time += timedelta(minutes=5)
        
        # Attack B
        dev_id = f"DEV00{1 + i%5}"
        atk_b_start = current_time
        current_time = runner.run_attack_b(current_time, dev_id)
        attack_labels.append((dev_id, atk_b_start, current_time))
        current_time += timedelta(minutes=5)
        
        # Attack C
        iot_id = f"IOT00{1 + i%3}"
        atk_c_start = current_time
        current_time = runner.run_attack_c(current_time, iot_id)
        attack_labels.append((iot_id, atk_c_start, current_time))
        current_time += timedelta(minutes=5)

    
    # Add a bit more normal traffic at the end
    current_time += timedelta(minutes=30)
    
    return attack_labels
