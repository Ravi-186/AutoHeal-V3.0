import os
import pandas as pd
from src.detection.model import DetectionModel

class Incident:
    """Represents a confirmed security incident with enterprise telemetry and IOC correlation."""
    def __init__(self, device_id, timestamp, events, severity, reason):
        self.device_id = device_id
        self.timestamp = timestamp
        self.events = events  # List of raw log dictionaries
        self.severity = severity
        self.reason = reason
        self.mitre_tactic = self._determine_mitre(reason)
        # Enterprise metadata
        ts_str = str(timestamp)
        self.incident_id = f"INC-{abs(hash(device_id + ts_str)) % 90000 + 10000}"
        self.status = "NEW"  # 'NEW', 'CONTAINED', 'VERIFIED', 'CLOSED'
        self.risk_score = 95 if severity == "HIGH" else (75 if severity == "MEDIUM" else 50)
        self.iocs = self._extract_iocs()
        self.blast_radius = self._calculate_blast_radius()
        
    def _determine_mitre(self, reason):
        r = reason.lower()
        if 'failed login' in r: return 'T1110 - Brute Force'
        if 'connection' in r: return 'T1046 - Network Discovery'
        if 'c2' in r or 'dns' in r: return 'T1568 - Dynamic Resolution'
        if 'ransomware' in r or 'encryption' in r or 'cpu' in r: return 'T1486 - Data Encrypted'
        return 'T1078 - Valid Accounts'

    def _extract_iocs(self):
        """Extracts Indicators of Compromise (IPs, domains, users) from correlated events."""
        iocs = {"dest_ips": set(), "domains": set(), "users": set()}
        for e in self.events:
            if 'dst_ip' in e and e['dst_ip'] not in ['127.0.0.1', '0.0.0.0']:
                iocs["dest_ips"].add(e['dst_ip'])
            if 'domain' in e:
                iocs["domains"].add(e['domain'])
            if 'user' in e:
                iocs["users"].add(e['user'])
        return {
            "dest_ips": list(iocs["dest_ips"]),
            "domains": list(iocs["domains"]),
            "users": list(iocs["users"])
        }

    def _calculate_blast_radius(self):
        """Identifies unique devices or subnets targeted during the attack."""
        targets = set()
        for e in self.events:
            if 'dst_ip' in e:
                targets.add(e['dst_ip'])
        return list(targets)

    def to_dict(self):
        return {
            "incident_id": self.incident_id,
            "device_id": self.device_id,
            "timestamp": str(self.timestamp),
            "severity": self.severity,
            "mitre_tactic": self.mitre_tactic,
            "reason": self.reason,
            "status": self.status,
            "risk_score": self.risk_score,
            "event_count": len(self.events),
            "blast_radius": self.blast_radius,
            "iocs": self.iocs
        }
        
    def __str__(self):
        return f"[{self.incident_id}] Severity: {self.severity} | {self.device_id} at {self.timestamp}\nReason: {self.reason}\nMITRE: {self.mitre_tactic}\nRelated Events: {len(self.events)}"

class CorrelationEngine:
    """Groups logs by device and time window, runs AI model, and produces combined alerts."""
    def __init__(self, data_dir, model=None):
        self.data_dir = data_dir
        self.model = model or DetectionModel()

    def analyze_window(self, device_id, start_time, end_time):
        """
        Gathers logs for a device in the time window, groups them into features,
        runs the AI model, and creates ONE combined Incident if a threat is detected.
        """
        fw = self._read_logs("firewall_logs.csv", device_id, start_time, end_time)
        logins = self._read_logs("login_logs.csv", device_id, start_time, end_time)
        dns = self._read_logs("dns_logs.csv", device_id, start_time, end_time)
        dev = self._read_logs("device_logs.csv", device_id, start_time, end_time)
        
        all_events = fw + logins + dns + dev
        
        if not all_events:
            return None
            
        # Group and calculate features for this window
        bytes_sent = sum([int(e.get('bytes_sent', 0)) for e in fw])
        bytes_received = sum([int(e.get('bytes_received', 0)) for e in fw])
        connections = len(fw)
        failed_logins = sum([1 for e in logins if e.get('status') == 'FAILED'])
        dns_requests = len(dns)
        
        cpu_usage = sum([float(e.get('cpu_usage', 0)) for e in dev]) / len(dev) if dev else 0.0
        mem_usage = sum([float(e.get('mem_usage', 0)) for e in dev]) / len(dev) if dev else 0.0
        
        features = {
            'bytes_sent': bytes_sent,
            'bytes_received': bytes_received,
            'connections': connections,
            'failed_logins': failed_logins,
            'dns_requests': dns_requests,
            'cpu_usage': cpu_usage,
            'mem_usage': mem_usage
        }
        
        print(f"  [DEBUG] Features: {features}")
        is_threat, score = self.model.predict(features)
        
        if is_threat:
            reason = self._generate_reason(features)
            # Enterprise severity classification based on score and attack indicators
            if score >= 0.75 or features['failed_logins'] >= 5 or (features['cpu_usage'] > 80 and features['mem_usage'] > 80) or features['bytes_sent'] > 100000:
                severity = "HIGH"
            elif score >= 0.5:
                severity = "MEDIUM"
            else:
                severity = "LOW"
            return Incident(device_id, end_time, all_events, severity, reason)
            
        return None
        
    def _read_logs(self, filename, device_id, start_time, end_time):
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            return []
            
        df = pd.read_csv(path)
        if df.empty:
            return []
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        mask = (df['device_id'] == device_id) & (df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)
        filtered = df[mask]
        
        # Convert timestamp to string for serialization later
        filtered = filtered.copy()
        filtered['timestamp'] = filtered['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return filtered.to_dict('records')
        
    def _generate_reason(self, features):
        """Generates a plain-English explanation based on the dominant features."""
        reasons = []
        if features['failed_logins'] >= 5 and features['bytes_sent'] > 10000:
            reasons.append(f"Detected {features['failed_logins']} failed logins followed by unusual outbound traffic ({features['bytes_sent']} bytes sent).")
        elif features['failed_logins'] >= 5:
            reasons.append(f"High number of failed logins ({features['failed_logins']}).")
            
        if features['connections'] > 20:
            reasons.append(f"Unusually high number of internal network connections ({features['connections']}).")
            
        if features['dns_requests'] > 10:
            reasons.append(f"Rapid, suspicious DNS requests detected ({features['dns_requests']} requests).")
            
        if features['cpu_usage'] > 80 and features['mem_usage'] > 80:
            reasons.append(f"Critical resource exhaustion (CPU: {features['cpu_usage']:.1f}%, MEM: {features['mem_usage']:.1f}%) indicating possible Ransomware encryption.")
            
        if not reasons:
            reasons.append("AI model detected anomalous network and device behavior.")
            
        return " ".join(reasons)

def extract_attack_path(incident, network=None):
    """
    Converts an incident into a list of chronological path steps:
    [{'from_device': str, 'to_device': str, 'timestamp': str, 'reason': str, 'step': int}]
    """
    if not incident or not incident.events:
        return []
        
    steps = []
    step_num = 1
    
    # Sort events chronologically
    sorted_events = sorted(incident.events, key=lambda x: str(x.get('timestamp', '')))
    
    # Map IPs to Device IDs
    if network is not None:
        ip_to_dev = {d.ip: d_id for d_id, d in network.devices.items()}
    else:
        from src.simulator.network import NetworkSimulator
        net = NetworkSimulator()
        ip_to_dev = {d.ip: d_id for d_id, d in net.devices.items()}
    
    has_failed_login = False
    has_outbound = False
    has_dns = False
    has_cpu_spike = False
    spread_targets = set()
    
    for e in sorted_events:
        ts = str(e.get('timestamp', ''))
        from_dev = e.get('device_id', incident.device_id)
        
        # Login event
        if 'status' in e and e['status'] == 'FAILED' and not has_failed_login:
            steps.append({'from_device': from_dev, 'to_device': from_dev, 'timestamp': ts, 'reason': 'Brute force credential attack burst', 'step': step_num})
            step_num += 1
            has_failed_login = True
            
        # Firewall event
        elif 'dst_ip' in e:
            dst_ip = e['dst_ip']
            to_dev = ip_to_dev.get(dst_ip, "Internet")
            
            # Internal spread
            if to_dev != "Internet" and to_dev != from_dev and to_dev not in spread_targets:
                steps.append({'from_device': from_dev, 'to_device': to_dev, 'timestamp': ts, 'reason': 'Lateral movement & subnet recon', 'step': step_num})
                step_num += 1
                spread_targets.add(to_dev)
                
            # Outbound exfiltration
            elif to_dev == "Internet" and int(e.get('bytes_sent', 0)) > 10000 and not has_outbound:
                steps.append({'from_device': from_dev, 'to_device': "Internet", 'timestamp': ts, 'reason': 'Massive data exfiltration outbound', 'step': step_num})
                step_num += 1
                has_outbound = True
                
        # DNS event
        elif 'domain' in e and not has_dns:
            dom = e['domain'].lower()
            if any(bad in dom for bad in ["malicious", "evil", "crypto", "keyserver", "darknet"]):
                steps.append({'from_device': from_dev, 'to_device': "Internet", 'timestamp': ts, 'reason': f'C2 Beacon / Key Exchange ({e["domain"]})', 'step': step_num})
                step_num += 1
                has_dns = True
                
        # Device telemetry spike
        elif 'cpu_usage' in e and float(e.get('cpu_usage', 0)) > 80 and not has_cpu_spike:
            steps.append({'from_device': from_dev, 'to_device': from_dev, 'timestamp': ts, 'reason': f'Cryptolocker payload execution (CPU {e["cpu_usage"]}%)', 'step': step_num})
            step_num += 1
            has_cpu_spike = True
                
    if not steps and sorted_events:
        steps.append({'from_device': incident.device_id, 'to_device': incident.device_id, 'timestamp': str(incident.timestamp), 'reason': 'Anomalous telemetry spike detected', 'step': step_num})
        
    return steps

