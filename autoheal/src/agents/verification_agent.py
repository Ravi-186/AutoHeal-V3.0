from src.correlation.engine import CorrelationEngine
from datetime import timedelta

class VerificationAgent:
    """Checks the network logs after a response to verify if the attack stopped."""
    def __init__(self, data_dir, network):
        self.engine = CorrelationEngine(data_dir)
        self.network = network
        
    def run(self, device_id, action_taken, check_time, window_minutes=5):
        start_time = check_time - timedelta(minutes=window_minutes)
        print(f"[VerificationAgent] Verifying '{action_taken}' action on {device_id} over the last {window_minutes} minutes...")
        
        # Run correlation engine on the time window AFTER the action
        incident = self.engine.analyze_window(device_id, start_time, check_time)
        
        if incident:
            print(f"[VerificationAgent] -> VERIFICATION FAILED. Suspicious activity continued despite the '{action_taken}' action.")
            return False # Failed
        else:
            print(f"[VerificationAgent] -> VERIFICATION SUCCESS. No suspicious activity found. The '{action_taken}' action worked.")
            return True # Success
