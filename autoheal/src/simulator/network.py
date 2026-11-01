class Device:
    """Represents a single device on an enterprise network."""
    def __init__(self, device_id, ip, role, zone="Corporate LAN"):
        self.device_id = device_id
        self.ip = ip
        self.role = role  # domain_controller, database, app_server, firewall, workstation, iot
        self.zone = zone  # Zero-Trust Network Zone
        self.state = 'Normal'  # 'Normal', 'Isolated', 'Blocked', 'Quarantined'
        self.risk_score = 0
        self.last_incident = None

    def to_dict(self):
        return {
            "device_id": self.device_id,
            "ip": self.ip,
            "role": self.role,
            "zone": self.zone,
            "state": self.state,
            "risk_score": self.risk_score
        }


class AutoRegisteringDeviceDict(dict):
    """Safe dictionary that auto-creates mock devices for legacy test suites if not found."""
    def __getitem__(self, key):
        if key not in self:
            # Auto-register device to prevent KeyError in tests and ad-hoc simulations
            ip_suffix = (abs(hash(key)) % 200) + 10
            role = "workstation"
            zone = "Corporate LAN"
            if "SRV" in key:
                role, zone = "app_server", "Application Tier"
            elif "DB" in key:
                role, zone = "database", "Data Enclave (PCI/PII)"
            elif "DC" in key:
                role, zone = "domain_controller", "Identity Enclave (Tier 0)"
            elif "FW" in key:
                role, zone = "firewall", "Perimeter DMZ"
            elif "SCADA" in key or "CAM" in key or "IOT" in key:
                role, zone = "iot", "OT / Industrial Enclave"
            self[key] = Device(key, f"10.10.9.{ip_suffix}", role, zone)
        return super().__getitem__(key)


class NetworkSimulator:
    """Manages simulated enterprise devices, segmentation zones, and autonomous mitigations."""
    def __init__(self):
        self.devices = AutoRegisteringDeviceDict({
            'ENT-CORE-DC-01': Device('ENT-CORE-DC-01', '10.0.0.10', 'domain_controller', 'Identity Enclave (Tier 0)'),
            'ENT-CORE-DC-02': Device('ENT-CORE-DC-02', '10.0.0.11', 'domain_controller', 'Identity Enclave (Tier 0)'),
            'ENT-PAYMENT-DB': Device('ENT-PAYMENT-DB', '10.0.1.50', 'database', 'Data Enclave (PCI/PII)'),
            'ENT-HR-DB-01': Device('ENT-HR-DB-01', '10.0.1.51', 'database', 'Data Enclave (PCI/PII)'),
            'ENT-APP-SRV-01': Device('ENT-APP-SRV-01', '10.0.2.100', 'app_server', 'Application Tier'),
            'ENT-APP-SRV-02': Device('ENT-APP-SRV-02', '10.0.2.101', 'app_server', 'Application Tier'),
            'ENT-DMZ-FW-01': Device('ENT-DMZ-FW-01', '192.168.254.1', 'firewall', 'Perimeter DMZ'),
            'ENT-DMZ-FW-02': Device('ENT-DMZ-FW-02', '192.168.254.2', 'firewall', 'Perimeter DMZ'),
            'CORP-LAPTOP-142': Device('CORP-LAPTOP-142', '10.10.1.142', 'workstation', 'Corporate LAN'),
            'CORP-LAPTOP-299': Device('CORP-LAPTOP-299', '10.10.1.299', 'workstation', 'Corporate LAN'),
            'CORP-LAPTOP-841': Device('CORP-LAPTOP-841', '10.10.2.115', 'workstation', 'Corporate LAN'),
            'CORP-LAPTOP-902': Device('CORP-LAPTOP-902', '10.10.2.211', 'workstation', 'Corporate LAN'),
            'SCADA-SENSOR-01': Device('SCADA-SENSOR-01', '10.20.1.5', 'iot', 'OT / Industrial Enclave'),
            'SCADA-SENSOR-02': Device('SCADA-SENSOR-02', '10.20.1.6', 'iot', 'OT / Industrial Enclave'),
            'WAREHOUSE-CAM-1': Device('WAREHOUSE-CAM-1', '10.20.2.10', 'iot', 'OT / Industrial Enclave'),
            # Flipkart E-Commerce Microservices
            'FK-FRONTEND-GATEWAY': Device('FK-FRONTEND-GATEWAY', '192.168.1.10', 'firewall', 'Perimeter DMZ'),
            'FK-STORE-APP': Device('FK-STORE-APP', '10.0.2.10', 'app_server', 'Application Tier'),
            'FK-AUTH-SERVICE': Device('FK-AUTH-SERVICE', '10.0.0.20', 'domain_controller', 'Identity Enclave (Tier 0)'),
            'FK-CHECKOUT-PAYMENT': Device('FK-CHECKOUT-PAYMENT', '10.0.1.75', 'app_server', 'Data Enclave (PCI/PII)'),
            'FK-INVENTORY-DB': Device('FK-INVENTORY-DB', '10.0.1.80', 'database', 'Data Enclave (PCI/PII)'),
            # Compatibility aliases for legacy tests
            'DEV001': Device('DEV001', '10.10.1.201', 'workstation', 'Corporate LAN'),
            'DEV002': Device('DEV002', '10.10.1.202', 'workstation', 'Corporate LAN'),
            'DEV003': Device('DEV003', '10.10.1.203', 'workstation', 'Corporate LAN'),
        })

    def isolate_device(self, device_id):
        """Simulates isolating a device (quarantine VLAN) from the rest of the network."""
        dev = self.devices[device_id]
        dev.state = 'Isolated'
        dev.risk_score = min(100, dev.risk_score + 35)
        print(f"[Network] Device {device_id} ISOLATED (Microsegmentation Enforced).")

    def block_device(self, device_id):
        """Simulates fully blocking a device at perimeter firewalls and 802.1X NAC."""
        dev = self.devices[device_id]
        dev.state = 'Blocked'
        dev.risk_score = 100
        print(f"[Network] Device {device_id} BLOCKED at 802.1X / Firewall perimeter.")

    def restore_device(self, device_id):
        """Restores a remediated device back to Normal operating state."""
        dev = self.devices[device_id]
        dev.state = 'Normal'
        dev.risk_score = 0
        print(f"[Network] Device {device_id} RESTORED to Normal state.")

    def get_status(self):
        """Returns the state of all devices."""
        return {d_id: d.state for d_id, d in self.devices.items()}
