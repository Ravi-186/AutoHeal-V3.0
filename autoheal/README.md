# 🛡️ AutoHeal: Enterprise Autonomous Cyber Defense Platform

AutoHeal is an enterprise-grade autonomous Security Orchestration, Automation, and Response (SOAR) platform powered by **LangGraph multi-agent loops** and **Machine Learning threat intelligence**. It continuously monitors enterprise zero-trust enclaves, detects adversary behaviors mapped to the **MITRE ATT&CK framework**, enforces automated microsegmentation containment, and verifies remediation efficacy with self-healing escalation.

---

## 🌟 Enterprise Architecture & Core Capabilities

- **Zero-Trust Network Microsegmentation**:
  - **Identity Enclave (Tier 0)**: Domain Controllers (`ENT-CORE-DC-01`, `ENT-CORE-DC-02`).
  - **Data Enclave (PCI/PII)**: Databases (`ENT-PAYMENT-DB`, `ENT-HR-DB-01`).
  - **Application Tier**: Microservice App Servers (`ENT-APP-SRV-01`, `ENT-APP-SRV-02`).
  - **Perimeter DMZ**: Stateful Edge Firewalls (`ENT-DMZ-FW-01`, `ENT-DMZ-FW-02`).
  - **Corporate LAN & Industrial IoT**: Endpoints and SCADA sensors (`CORP-LAPTOP-142`, `SCADA-SENSOR-01`).

- **Multi-Vector Threat Defense (MITRE ATT&CK)**:
  - **Attack A**: Credential Stuffing & Exfiltration (`T1110 - Brute Force` / `T1048 - Exfiltration`).
  - **Attack B**: Lateral Movement & Subnet Port Scan (`T1046 - Network Discovery`).
  - **Attack C**: Cryptolocker Ransomware Encryption (`T1486 - Data Encrypted`).
  - **Attack D**: Stealthy C2 Tunneling & DNS Exfiltration (`T1568 - Dynamic Resolution`).

- **LangGraph Multi-Agent Orchestration**:
  - **Detection Agent**: Extracts multi-dimensional sliding window features and evaluates ensemble model confidence with defense-in-depth security guardrails.
  - **Response Agent**: Dynamically enforces mitigation policy (Microsegmentation VLAN Quarantine or 802.1X Port Shutdown).
  - **Verification Agent**: Analyzes post-mitigation log delta to confirm threat neutralization.
  - **Escalation Engine**: Automatically re-engages and escalates containment severity if evasion or bypass is detected.

- **SOC Command Center & 3D Telemetry**:
  - **Executive KPI Dashboard**: Real-time MTTR, MTTD, Zero-Trust Posture Grade, and Asset Matrix.
  - **Explainable AI (XAI)**: Step-by-step audit trail of agent reasoning and state transitions.
  - **3D Topology & Lateral Movement Replay**: Interactive Force-Directed 3D graph with chronology scrubber and blast-radius inspector.
  - **Forensic Dossier & One-Click Export**: Export full incident dossiers as structured JSON or Markdown executive summaries.

---

## 🚀 Setup & Installation

1. **Clone & Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Running the Platform

### 1. Interactive Enterprise SOC Dashboard (Streamlit)
Launch the primary Command Center with live 3D topology, MITRE ATT&CK navigator, and forensic triage:
```bash
streamlit run dashboard/app.py
```

### 2. Autonomous End-to-End Simulation Demo (CLI)
Run the automated adversary story showing detection, dynamic containment, simulated bypass, escalation, and verification:
```bash
python run_demo.py
```

### 3. FastAPI AutoHeal Sentinel REST API & Web Portal
Run the dual FastAPI backend and cyber portal:
```bash
python server.py
```

---

## 🧪 Automated Test Verification

Run all unit and regression test suites:
```bash
python -m unittest discover tests
python test_agents.py
python test_correlation.py
python test_langgraph.py
```
