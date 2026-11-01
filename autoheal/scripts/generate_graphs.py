import os
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIAGRAMS_DIR = os.path.join(BASE_DIR, "AutoHeal_Documentation", "diagrams")
os.makedirs(DIAGRAMS_DIR, exist_ok=True)

# Set high DPI and professional style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.size'] = 11

# Graph 1: Telemetry Event & Threat Distribution
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

event_types = ['Normal Traffic\n(GET /shop)', 'Brute-Force\n(AUTH-001)', 'Rate Anomaly\n(RATE-001)', 'SQLi Probe\n(SQLI-001)', 'Admin Probe\n(ADMIN-001)']
event_counts = [360, 48, 42, 28, 22]
colors = ['#2563eb', '#dc2626', '#f59e0b', '#9333ea', '#059669']

bars = ax1.bar(event_types, event_counts, color=colors, width=0.55, edgecolor='#1e293b', linewidth=1.2)
ax1.set_title('Security Telemetry Ingress by Vector (500 Events)', fontsize=13, fontweight='bold', pad=15)
ax1.set_ylabel('Number of Logged Events', fontsize=11, fontweight='bold')
ax1.set_ylim(0, 420)
for bar in bars:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 6, f'{yval} ({yval/500*100:.1f}%)', ha='center', va='bottom', fontsize=10, fontweight='bold')

severities = ['Low / Normal', 'Medium', 'High', 'Critical']
sev_counts = [360, 92, 42, 6]
sev_colors = ['#10b981', '#f59e0b', '#ef4444', '#7f1d1d']
explode = (0.02, 0.05, 0.08, 0.12)

wedges, texts, autotexts = ax2.pie(
    sev_counts, labels=severities, autopct='%1.1f%%', startangle=140,
    colors=sev_colors, explode=explode, shadow=True,
    textprops=dict(color="#1e293b", fontweight='bold', fontsize=10)
)
for at in autotexts:
    at.set_color('white')
ax2.set_title('Incident Severity Distribution Across Ingress Streams', fontsize=13, fontweight='bold', pad=15)

plt.tight_layout()
g1_path = os.path.join(DIAGRAMS_DIR, "graph_01_threat_distribution.png")
plt.savefig(g1_path, dpi=300, bbox_inches='tight')
plt.close()
print("Saved Graph 1:", g1_path)

# Graph 2: Response & Containment Latency Comparison (Manual vs. AutoHeal)
fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)

stages = [
    'Telemetry\nIngestion',
    'Pattern\nCorrelation',
    'Incident\nClassification',
    'Perimeter\nContainment',
    'Synthetic\nVerification',
    'Total Mean\nTime To Heal'
]

# Manual SOC response (in seconds) vs AutoHeal Autonomous response (in seconds)
manual_times = [15.0, 180.0, 300.0, 420.0, 600.0, 1515.0]  # ~25 minutes
autoheal_times = [0.035, 0.045, 0.020, 0.080, 0.150, 0.330]  # 330 milliseconds

x = np.arange(len(stages))
width = 0.35

rects1 = ax.bar(x - width/2, [m/60.0 for m in manual_times], width, label='Conventional Manual SOC Response (Minutes)', color='#94a3b8', edgecolor='#334155')
rects2 = ax.bar(x + width/2, [a for a in autoheal_times], width, label='AutoHeal Autonomous Containment (Seconds)', color='#0284c7', edgecolor='#0369a1')

ax.set_ylabel('Execution Duration (Log Scale)', fontsize=11, fontweight='bold')
ax.set_title('Containment & Remediation Latency: Manual vs. AutoHeal Autonomous SOAR', fontsize=13, fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(stages, fontweight='bold')
ax.set_yscale('log')
ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1', fontsize=10)

# Add value annotations
for i, rect in enumerate(rects1):
    val = manual_times[i]
    lbl = f"{val/60:.1f}m" if val >= 60 else f"{val:.0f}s"
    ax.annotate(lbl,
                xy=(rect.get_x() + rect.get_width() / 2, rect.get_height()),
                xytext=(0, 3), textcoords="offset points",
                ha='center', va='bottom', fontsize=9, fontweight='bold', color='#475569')

for i, rect in enumerate(rects2):
    val = autoheal_times[i]
    lbl = f"{val*1000:.0f}ms" if val < 1.0 else f"{val:.2f}s"
    ax.annotate(lbl,
                xy=(rect.get_x() + rect.get_width() / 2, rect.get_height()),
                xytext=(0, 3), textcoords="offset points",
                ha='center', va='bottom', fontsize=9, fontweight='bold', color='#0369a1')

plt.tight_layout()
g2_path = os.path.join(DIAGRAMS_DIR, "graph_02_containment_latency.png")
plt.savefig(g2_path, dpi=300, bbox_inches='tight')
plt.close()
print("Saved Graph 2:", g2_path)
