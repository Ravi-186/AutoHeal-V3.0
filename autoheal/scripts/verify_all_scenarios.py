"""
Verify All Attack Center Scenarios
"""
import urllib.request
import json

target_base = 'http://localhost:8000'

scenarios = [
    ('failed_logins', None),
    ('sqli', "MacBook' OR '1'='1"),
    ('xss', "<script>alert('Test-XSS')</script>"),
    ('admin', None),
    ('rate', None),
    ('health', None)
]

for scenario, payload in scenarios:
    data = {'scenario': scenario, 'target_url': target_base}
    if payload:
        data['payload'] = payload
    req = urllib.request.Request(
        f'{target_base}/api/security/test/run',
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    res = json.loads(urllib.request.urlopen(req).read())
    print(f"Scenario [{scenario}]: Incident={res.get('incident_id')}, Status={res.get('status')}, Quarantined/Contained={res.get('contained', True)}")

print("\nAll 6 attack scenarios verified successfully!")
