import random
from datetime import timedelta

class ScenarioRunner:
    """Generates normal traffic and specific attack scenarios."""
    def __init__(self, network, logger):
        self.network = network
        self.logger = logger
        self.domains = ["google.com", "github.com", "microsoft.com", "amazon.com", "internal.corp"]

    def generate_normal_traffic(self, start_time, duration_minutes=60):
        """Generates normal background traffic for all normal devices."""
        current_time = start_time
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        while current_time < end_time:
            for device_id, device in self.network.devices.items():
                if device.state != 'Normal':
                    continue
                
                # Randomly generate logs for normal behavior
                if random.random() < 0.2:
                    self.logger.log_firewall(
                        current_time, device_id, device.ip, f"104.21.{random.randint(1,255)}.{random.randint(1,255)}", 
                        random.randint(100, 2000), random.randint(1000, 10000)
                    )
                if random.random() < 0.05:
                    self.logger.log_login(current_time, device_id, "user", "SUCCESS")
                if random.random() < 0.1:
                    domain = random.choice(self.domains)
                    self.logger.log_dns(current_time, device_id, domain, f"8.8.8.{random.randint(1,8)}")
                if random.random() < 0.1:
                    self.logger.log_device(current_time, device_id, random.randint(5, 40), random.randint(20, 60), random.randint(50, 150))
                    
            current_time += timedelta(seconds=15)
        return current_time

    def run_attack_a(self, start_time, attacker_id="CORP-LAPTOP-142"):
        """Attack A: Failed-login burst + unusual outbound traffic."""
        current_time = start_time
        device = self.network.devices[attacker_id]
        
        if device.state != 'Normal':
            return current_time
            
        print(f"[Scenario] Launching Attack A on {attacker_id} at {current_time}")
        
        # 1. Burst of failed logins and high resource usage
        self.logger.log_device(current_time, attacker_id, random.randint(85, 99), random.randint(75, 95), random.randint(500, 1000))
        for _ in range(20):
            self.logger.log_login(current_time, attacker_id, "admin", "FAILED")
            current_time += timedelta(seconds=1)
            
        # 2. Unusual outbound traffic (data exfiltration)
        current_time += timedelta(seconds=5)
        for _ in range(10):
            self.logger.log_firewall(
                current_time, attacker_id, device.ip, "198.51.100.42", 
                random.randint(50000, 100000), random.randint(100, 500)
            )
            current_time += timedelta(seconds=2)
            
        return current_time

    def run_attack_b(self, start_time, attacker_id="ENT-APP-SRV-01"):
        """Attack B: Compromised device spreading to others."""
        current_time = start_time
        device = self.network.devices[attacker_id]
        
        if device.state != 'Normal':
            return current_time
            
        print(f"[Scenario] Launching Attack B on {attacker_id} at {current_time}")
        
        # Internal network scanning and connection attempts
        for target_id, target_device in self.network.devices.items():
            if target_id != attacker_id:
                self.logger.log_firewall(
                    current_time, attacker_id, device.ip, target_device.ip,
                    50, 50, action="DENY" if random.random() < 0.5 else "ALLOW"
                )
                current_time += timedelta(seconds=1)
                
        return current_time

    def run_attack_c(self, start_time, attacker_id="ENT-HR-DB-01"):
        """Attack C: Ransomware Encryption Simulation."""
        current_time = start_time
        device = self.network.devices.get(attacker_id)
        
        if not device or device.state != 'Normal':
            return current_time
            
        print(f"[Scenario] Launching Attack C (Ransomware) on {attacker_id} at {current_time}")
        
        # Ransomware pattern: High CPU, high memory, rapid file modifications, unusual DNS
        self.logger.log_dns(current_time, attacker_id, "keyserver-darknet.ru", "198.51.100.1")
        current_time += timedelta(seconds=2)
        
        for _ in range(5):
            self.logger.log_device(current_time, attacker_id, random.randint(95, 100), random.randint(90, 100), random.randint(300, 400))
            current_time += timedelta(seconds=5)
            
        return current_time

    def run_attack_d(self, start_time, attacker_id="ENT-PAYMENT-DB"):
        """Attack D: C2 Beaconing & DNS Tunneling Exfiltration."""
        current_time = start_time
        device = self.network.devices.get(attacker_id)
        
        if not device or device.state != 'Normal':
            return current_time
            
        print(f"[Scenario] Launching Attack D (C2 Beaconing / DNS Tunnel) on {attacker_id} at {current_time}")
        
        # High volume DNS requests to known malicious domains
        c2_domains = ["malicious-c2.net", "evil-tracker.io", "crypto-miner.xyz"]
        for _ in range(16):
            domain = random.choice(c2_domains)
            self.logger.log_dns(current_time, attacker_id, domain, "185.220.101.5")
            current_time += timedelta(seconds=1)
            
        # Outbound socket connections
        for _ in range(8):
            self.logger.log_firewall(
                current_time, attacker_id, device.ip, "185.220.101.5",
                random.randint(12000, 45000), random.randint(500, 2000)
            )
            current_time += timedelta(seconds=2)
            
        return current_time

    def run_flipkart_credential_stuffing(self, start_time, attacker_id="FK-AUTH-SERVICE"):
        """Flipkart Scenario 1: Flash sale botnet credential stuffing on customer accounts (T1110)."""
        current_time = start_time
        device = self.network.devices.get(attacker_id)
        if not device or device.state != 'Normal':
            return current_time

        print(f"[Flipkart Scenario] Flash sale botnet credential stuffing on {attacker_id} at {current_time}")
        self.logger.log_device(current_time, attacker_id, random.randint(88, 98), random.randint(80, 92), random.randint(600, 1200))
        for _ in range(25):
            user = random.choice(["flipkart_shopper", "supercoin_vip", "admin_store", "plus_member"])
            self.logger.log_login(current_time, attacker_id, user, "FAILED")
            current_time += timedelta(seconds=1)

        for _ in range(8):
            self.logger.log_firewall(
                current_time, attacker_id, device.ip, "198.51.100.24",
                random.randint(40000, 85000), random.randint(100, 400)
            )
            current_time += timedelta(seconds=1)
        return current_time

    def run_flipkart_payment_exfiltration(self, start_time, attacker_id="FK-CHECKOUT-PAYMENT"):
        """Flipkart Scenario 2: Payment gateway breach attempting cardholder PII exfiltration (T1048)."""
        current_time = start_time
        device = self.network.devices.get(attacker_id)
        if not device or device.state != 'Normal':
            return current_time

        print(f"[Flipkart Scenario] Malicious card token exfiltration on {attacker_id} at {current_time}")
        self.logger.log_device(current_time, attacker_id, random.randint(75, 90), random.randint(70, 85), random.randint(400, 800))
        for _ in range(12):
            self.logger.log_firewall(
                current_time, attacker_id, device.ip, "203.0.113.88",
                random.randint(65000, 120000), random.randint(200, 600)
            )
            current_time += timedelta(seconds=1)
        return current_time

    def run_flipkart_inventory_ransomware(self, start_time, attacker_id="FK-INVENTORY-DB"):
        """Flipkart Scenario 3: Inventory and Order database encryption ransomware (T1486)."""
        current_time = start_time
        device = self.network.devices.get(attacker_id)
        if not device or device.state != 'Normal':
            return current_time

        print(f"[Flipkart Scenario] Ransomware lock on Flipkart Inventory DB {attacker_id} at {current_time}")
        self.logger.log_dns(current_time, attacker_id, "keyserver-darknet.ru", "198.51.100.1")
        current_time += timedelta(seconds=1)
        for _ in range(6):
            self.logger.log_device(current_time, attacker_id, random.randint(96, 100), random.randint(94, 99), random.randint(350, 500))
            current_time += timedelta(seconds=2)
        return current_time

    def run_flipkart_catalog_ddos(self, start_time, attacker_id="FK-FRONTEND-GATEWAY"):
        """Flipkart Scenario 4: Automated competitor price-scraping probe and catalog flood (T1046)."""
        current_time = start_time
        device = self.network.devices.get(attacker_id)
        if not device or device.state != 'Normal':
            return current_time

        print(f"[Flipkart Scenario] High-rate price scraping and reconnaissance on {attacker_id} at {current_time}")
        self.logger.log_device(current_time, attacker_id, random.randint(85, 95), random.randint(80, 90), random.randint(800, 1500))
        for target_id, target_device in self.network.devices.items():
            if target_id.startswith("FK-") and target_id != attacker_id:
                self.logger.log_firewall(
                    current_time, attacker_id, device.ip, target_device.ip,
                    random.randint(35000, 60000), 50, action="DENY" if random.random() < 0.4 else "ALLOW"
                )
                current_time += timedelta(seconds=1)
        return current_time


