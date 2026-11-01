class ResponseAgent:
    """Automatically isolates or blocks devices based on the incident."""
    def __init__(self, network):
        self.network = network
        self.action_log = []
        
    def run(self, incident):
        device_id = incident.device_id
        current_state = self.network.devices[device_id].state
        print(f"[ResponseAgent] Received Incident for {device_id}. Current network state: {current_state}.")
        
        action = None
        if current_state == "Normal":
            print(f"[ResponseAgent] Action chosen: ISOLATE {device_id}.")
            self.network.isolate_device(device_id)
            action = "ISOLATE"
        elif current_state == "Isolated":
            print(f"[ResponseAgent] Device {device_id} is already isolated but attack continues. Escalating action to: BLOCK.")
            self.network.block_device(device_id)
            action = "BLOCK"
            
        # Record the action taken
        self.action_log.append({
            'device_id': device_id,
            'incident_reason': incident.reason,
            'action_taken': action,
            'timestamp': incident.timestamp
        })
        
        return action
