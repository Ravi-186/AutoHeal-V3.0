import csv
import os

class LogGenerator:
    """Generates and writes logs to CSV files."""
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.firewall_path = os.path.join(self.data_dir, "firewall_logs.csv")
        self.login_path = os.path.join(self.data_dir, "login_logs.csv")
        self.dns_path = os.path.join(self.data_dir, "dns_logs.csv")
        self.device_path = os.path.join(self.data_dir, "device_logs.csv")
        
        self._init_files()
        
    def _init_files(self):
        """Initialize the CSV files with headers."""
        self._write_csv(self.firewall_path, ["timestamp", "device_id", "src_ip", "dst_ip", "bytes_sent", "bytes_received", "action"], mode='w')
        self._write_csv(self.login_path, ["timestamp", "device_id", "user", "status", "message"], mode='w')
        self._write_csv(self.dns_path, ["timestamp", "device_id", "domain", "resolved_ip"], mode='w')
        self._write_csv(self.device_path, ["timestamp", "device_id", "cpu_usage", "mem_usage", "process_count"], mode='w')

    def _write_csv(self, path, row, mode='a'):
        with open(path, mode, newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
            
    def log_firewall(self, ts, device_id, src, dst, bs, br, action="ALLOW"):
        self._write_csv(self.firewall_path, [ts.strftime('%Y-%m-%d %H:%M:%S'), device_id, src, dst, bs, br, action])
        
    def log_login(self, ts, device_id, user, status):
        self._write_csv(self.login_path, [ts.strftime('%Y-%m-%d %H:%M:%S'), device_id, user, status, f"Login {status}"])
        
    def log_dns(self, ts, device_id, domain, resolved_ip):
        self._write_csv(self.dns_path, [ts.strftime('%Y-%m-%d %H:%M:%S'), device_id, domain, resolved_ip])
        
    def log_device(self, ts, device_id, cpu, mem, procs):
        self._write_csv(self.device_path, [ts.strftime('%Y-%m-%d %H:%M:%S'), device_id, cpu, mem, procs])
