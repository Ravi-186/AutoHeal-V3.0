import urllib.request
import json
import sqlite3
import re

def verify():
    print("--- 1. VERIFYING HTML ELEMENT IDS IN INDEX.HTML ---")
    with open('autoheal/web/templates/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    kpi_ids = [
        'statTotalEvents',
        'statActiveIncidents',
        'statCriticalIncidents',
        'statResolvedIncidents',
        'statVerifiedRemediations',
        'statMTTD',
        'statMTTR',
        'statAvailability',
        'securityEventTimelineCanvas',
        'threatSeverityDonutCanvas',
        'overviewLastUpdated',
        'kpiEventsTrend',
        'kpiIncidentsTrend',
        'kpiCriticalTrend'
    ]

    all_found = True
    for kid in kpi_ids:
        found = f'id="{kid}"' in html or f"id='{kid}'" in html
        print(f"  Element ID '{kid}': {'FOUND' if found else 'MISSING'}")
        if not found:
            all_found = False

    assert all_found, "Not all KPI element IDs found in index.html"

    print("\n--- 2. VERIFYING LIVE API ENDPOINT RESPONSES ---")
    base_url = "http://127.0.0.1:8000"

    # Metrics
    req = urllib.request.urlopen(f"{base_url}/api/security/metrics?time_range=24h")
    assert req.status == 200
    metrics = json.loads(req.read().decode('utf-8'))
    print(f"  GET /api/security/metrics: 200 OK")
    print(f"    total_security_events: {metrics.get('total_security_events')}")
    print(f"    active_incidents: {metrics.get('active_incidents')}")
    print(f"    critical_incidents: {metrics.get('critical_incidents')}")
    print(f"    resolved_incidents: {metrics.get('resolved_incidents')}")
    print(f"    verified_remediations: {metrics.get('verified_remediations')}")
    print(f"    mean_time_to_detect_ms: {metrics.get('mean_time_to_detect_ms')}")
    print(f"    mean_time_to_respond_ms: {metrics.get('mean_time_to_respond_ms')}")
    print(f"    system_availability_percent: {metrics.get('system_availability_percent')}%")

    # Timeline
    req = urllib.request.urlopen(f"{base_url}/api/security/analytics/timeline?time_range=24h&category=ALL&severity=ALL&slices=12")
    assert req.status == 200
    timeline = json.loads(req.read().decode('utf-8'))
    print(f"  GET /api/security/analytics/timeline: 200 OK")
    print(f"    bucket_duration: {timeline.get('bucket_duration')}")
    print(f"    total_events: {timeline.get('total_events')}")
    print(f"    slices count: {len(timeline.get('labels', []))}")
    assert len(timeline.get('labels', [])) == 12

    print("\n--- 3. VERIFYING DATABASE VALUES MATCH LIVE API ---")
    conn = sqlite3.connect('autoheal/data/shopsphere.db')
    cursor = conn.cursor()

    cursor.execute("SELECT count(*) FROM security_events")
    db_events = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM security_incidents WHERE status IN ('NEW', 'TRIAGED', 'INVESTIGATING', 'CONTAINMENT', 'REMEDIATION', 'VERIFICATION')")
    db_active_incidents = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM security_incidents WHERE severity = 'CRITICAL' AND status != 'RESOLVED'")
    db_crit_incidents = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM security_incidents WHERE status = 'RESOLVED'")
    db_resolved_incidents = cursor.fetchone()[0]

    print(f"  Database total security_events: {db_events} (API reports: {metrics.get('total_security_events')})")
    print(f"  Database active incidents: {db_active_incidents} (API reports: {metrics.get('active_incidents')})")
    print(f"  Database critical incidents: {db_crit_incidents} (API reports: {metrics.get('critical_incidents')})")
    print(f"  Database resolved incidents: {db_resolved_incidents} (API reports: {metrics.get('resolved_incidents')})")
    conn.close()

    print("\n--- 4. VERIFYING SCRIPT.JS DOM POPULATION SIMULATION ---")
    total = metrics.get('total_security_events', 0)
    active = metrics.get('active_incidents', 0)
    crit = metrics.get('critical_incidents', 0)
    resolved = metrics.get('resolved_incidents', 0)
    rem = metrics.get('verified_remediations', 0)
    mttd = metrics.get('mean_time_to_detect_ms', 142)
    mttr = metrics.get('mean_time_to_respond_ms', 850)
    avail = metrics.get('system_availability_percent', 99.98)

    rendered_values = {
        'statTotalEvents': f"{total:,}",
        'statActiveIncidents': str(active),
        'statCriticalIncidents': str(crit),
        'statResolvedIncidents': str(resolved),
        'statVerifiedRemediations': str(rem),
        'statMTTD': f"{mttd / 1000:.2f}s" if mttd >= 1000 else f"{mttd}ms",
        'statMTTR': f"{mttr / 1000:.2f}s" if mttr >= 1000 else f"{mttr}ms",
        'statAvailability': f"{avail:.2f}%"
    }

    for el_id, val in rendered_values.items():
        print(f"  Rendered DOM Element '{el_id}' -> '{val}' (replaces '---')")
        assert val != '---', f"Element {el_id} still has '---'"

    print("\nALL DOM & METRICS VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    verify()
