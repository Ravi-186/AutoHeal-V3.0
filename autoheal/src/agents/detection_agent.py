from src.correlation.engine import CorrelationEngine
from datetime import timedelta

class DetectionAgent:
    """Watches logs, runs AI and correlation engine, and raises confirmed incidents."""
    def __init__(self, data_dir):
        self.engine = CorrelationEngine(data_dir)
        
    def run(self, device_id, current_time, window_minutes=5):
        start_time = current_time - timedelta(minutes=window_minutes)
        print(f"[DetectionAgent] Scanning logs for {device_id} from {start_time.strftime('%H:%M:%S')} to {current_time.strftime('%H:%M:%S')}")
        
        incident = self.engine.analyze_window(device_id, start_time, current_time)
        
        if incident:
            print(f"[DetectionAgent] -> THREAT DETECTED! Raised Incident for {device_id}.")
        else:
            print("[DetectionAgent] -> System Normal. No threats detected.")
            
        return incident
