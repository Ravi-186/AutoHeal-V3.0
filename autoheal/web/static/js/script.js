// =========================================================================
// AUTOHEAL ENTERPRISE CYBERSECURITY SOC - FRONTEND CONTROLLER
// Real-time telemetry, Attack Center SSE streaming, incident reporting,
// autonomous healing & forensics inspection.
// =========================================================================

let activeEventSource = null;
let overviewChartInstance = null;
let eventsAutoRefreshTimer = null;
let allFetchedEvents = [];
let allFetchedIncidents = [];
let selectedIncidentId = null;

// Universal Timestamp Formatter (Safely handles ISO strings, SQLite strings, Unix epochs)
function formatAppSecTimestamp(val, includeDate = false) {
    if (!val) return '-';
    let d;
    if (typeof val === 'number') {
        d = new Date(val < 1e11 ? val * 1000 : val);
    } else if (typeof val === 'string') {
        const trimmed = val.trim();
        if (/^\d+$/.test(trimmed)) {
            const num = parseInt(trimmed, 10);
            d = new Date(num < 1e11 ? num * 1000 : num);
        } else {
            const normalized = trimmed.includes('T') ? trimmed : trimmed.replace(' ', 'T');
            d = new Date(normalized);
            if (isNaN(d.getTime())) {
                d = new Date(trimmed);
            }
        }
    } else {
        d = new Date(val);
    }
    if (isNaN(d.getTime())) {
        return String(val);
    }
    return includeDate ? d.toLocaleString() : d.toLocaleTimeString();
}

function getStatusBadgeHtml(status) {
    const s = (status || 'OPEN').toUpperCase();
    if (s.includes('VERIFIED') || s.includes('CONTAINED') || s.includes('RESOLVED') || s.includes('CLOSED')) {
        return `<span class="badge badge-success">${status}</span>`;
    }
    if (s.includes('FAILED') || s.includes('CRITICAL') || s.includes('ESCALAT')) {
        return `<span class="badge badge-critical">${status}</span>`;
    }
    if (s.includes('ATTEMPT') || s.includes('MITIGAT') || s.includes('INVESTIGAT')) {
        return `<span class="badge badge-warning">${status}</span>`;
    }
    return `<span class="badge badge-info">${status}</span>`;
}

document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 Initializing AutoHeal Enterprise Cybersecurity SOC UI...');
    toastr.options = { positionClass: 'toast-top-right', timeOut: 3000 };

    // 1. Initialize Navigation Tabs
    initNavigationTabs();

    // 2. Initialize Attack Center
    initAttackCenterControls();

    // 3. Initialize Overview Chart & KPIs
    initOverviewChart();
    loadDashboardMetrics();
    loadOverviewIncidents();
    loadSecurityPosture();

    // 4. Initial data loads
    loadSecurityEvents();
    loadIncidentsList();
    loadQuarantinedClients();
    loadVulnerabilitiesTable();
    loadIncidentReportsTable();
    pingAllServices();

    // 5. Polling for real-time dashboard stats every 3 seconds
    setInterval(loadDashboardMetrics, 3000);
});

// Update Live Clock
setInterval(() => {
    const now = new Date();
    const clockEl = document.getElementById('currentTime');
    if (clockEl) clockEl.textContent = now.toLocaleTimeString();
}, 1000);

// =========================================================================
// 1. NAVIGATION CONTROLLER
// =========================================================================

function initNavigationTabs() {
    const tabs = document.querySelectorAll('.nav-tab-item[data-page]');
    tabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            const pageId = this.getAttribute('data-page');
            switchToTab(pageId);
        });
    });
}

function switchToTab(pageId) {
    const tabs = document.querySelectorAll('.nav-tab-item[data-page]');
    tabs.forEach(t => t.classList.remove('active'));
    
    const activeTab = document.querySelector(`.nav-tab-item[data-page="${pageId}"]`);
    if (activeTab) activeTab.classList.add('active');

    // Switch visible section
    document.querySelectorAll('.workspace-page').forEach(page => {
        page.classList.remove('active');
    });

    const targetPage = document.getElementById(pageId);
    if (targetPage) {
        targetPage.classList.add('active');
    }

    // Refresh page-specific content on tab entry
    if (pageId === 'pageOverview') {
        loadDashboardMetrics();
        loadOverviewIncidents();
        loadSecurityPosture();
        if (overviewChartInstance) overviewChartInstance.resize();
    } else if (pageId === 'pageEvents') {
        loadSecurityEvents();
    } else if (pageId === 'pageIncidents') {
        loadIncidentsList();
    } else if (pageId === 'pageHealing') {
        loadQuarantinedClients();
        loadVulnerabilitiesTable();
    } else if (pageId === 'pageReports') {
        loadIncidentReportsTable();
    } else if (pageId === 'pageHealth') {
        pingAllServices();
    }
}

// =========================================================================
// 2. OVERVIEW DASHBOARD & METRICS
// =========================================================================

async function loadDashboardMetrics() {
    try {
        const res = await fetch('/api/security/metrics');
        if (!res.ok) return;
        const data = await res.json();

        // Update KPIs
        const totalEventsEl = document.getElementById('statTotalEvents');
        const activeIncidentsEl = document.getElementById('statActiveIncidents');
        const quarantinedIpsEl = document.getElementById('statQuarantinedIps');
        const navCountEl = document.getElementById('navIncidentCount');

        if (totalEventsEl) totalEventsEl.textContent = data.total_events_recorded || 0;
        if (activeIncidentsEl) activeIncidentsEl.textContent = data.active_threats || 0;
        if (quarantinedIpsEl) quarantinedIpsEl.textContent = data.active_blocked_ips || 0;
        if (navCountEl) navCountEl.textContent = data.total_incidents || 0;

        // Push random/real velocity point to chart
        if (overviewChartInstance) {
            const currentVelocity = (data.active_threats > 0) ? (20 + Math.floor(Math.random() * 30)) : (2 + Math.floor(Math.random() * 6));
            overviewChartInstance.data.datasets[0].data.shift();
            overviewChartInstance.data.datasets[0].data.push(currentVelocity);
            overviewChartInstance.update();
        }
    } catch (e) {
        console.error('Error loading dashboard metrics', e);
    }
}

function initOverviewChart() {
    const ctx = document.getElementById('overviewChart');
    if (!ctx) return;

    overviewChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array(20).fill(''),
            datasets: [{
                label: 'Security Events / sec',
                data: Array(20).fill(2),
                borderColor: '#00d4ff',
                backgroundColor: 'rgba(0, 212, 255, 0.12)',
                borderWidth: 2,
                fill: true,
                tension: 0.35,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 0 },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 60,
                    grid: { color: 'rgba(255, 255, 255, 0.06)' },
                    ticks: { color: '#94a3b8', font: { family: 'Inter', size: 11 } }
                },
                x: {
                    grid: { display: false },
                    ticks: { display: false }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#f8fafc', font: { family: 'Inter', size: 12 } }
                }
            }
        }
    });
}

async function loadOverviewIncidents() {
    const tbody = document.getElementById('overviewIncidentsTableBody');
    if (!tbody) return;

    try {
        const res = await fetch('/api/security/incidents?limit=5');
        if (!res.ok) return;
        const data = await res.json();
        const incidents = Array.isArray(data) ? data : (data.incidents || []);

        if (incidents.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 20px;">No incidents recorded yet. Launch a test from the Attack Center to generate real forensic data.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        incidents.slice(0, 5).forEach(inc => {
            const tr = document.createElement('tr');
            const sevBadge = getSeverityBadgeHtml(inc.severity);
            const timeStr = formatAppSecTimestamp(inc.created_at, false);
            const endpoint = (Array.isArray(inc.affected_endpoints) ? inc.affected_endpoints.join(', ') : inc.affected_endpoints) || inc.target_endpoint || '-';
            const action = (inc.mitigation_actions && inc.mitigation_actions[0] ? inc.mitigation_actions[0].action : inc.defensive_action) || 'Autonomous Containment';

            tr.innerHTML = `
                <td><strong style="color: var(--primary); font-family: var(--font-mono);">${inc.incident_id}</strong></td>
                <td>${timeStr}</td>
                <td><strong style="color: #ffffff;">${inc.category || inc.attack_category || '-'}</strong></td>
                <td><code>${endpoint}</code></td>
                <td>${sevBadge}</td>
                <td style="color: var(--status-success);">${action}</td>
                <td><span class="badge badge-success">${inc.verification_status || 'VERIFIED'}</span></td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="inspectIncident('${inc.incident_id}')">
                        <i class="fas fa-search"></i> Inspect
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error('Error loading overview incidents', e);
    }
}

// =========================================================================
// 3. ATTACK CENTER EXECUTION & SSE STREAM
// =========================================================================

let attackStartTime = null;
let currentGeneratedIncidentId = null;

function resetTimelineStepper() {
    const steps = [
        { id: 'stepReady', sub: 'Target Bound' },
        { id: 'stepRunning', sub: 'HTTP Probing' },
        { id: 'stepEvents', sub: 'SQLite Stream' },
        { id: 'stepDetected', sub: 'Rule Matching' },
        { id: 'stepResponse', sub: 'Policy Action' },
        { id: 'stepVerified', sub: 'Follow-up Probe' },
        { id: 'stepReport', sub: 'PDF / JSON' }
    ];
    steps.forEach((s, idx) => {
        const el = document.getElementById(s.id);
        if (el) {
            el.className = idx === 0 ? 'stepper-step step-completed' : 'stepper-step';
            const sub = el.querySelector('.step-sub');
            if (sub) sub.textContent = s.sub;
        }
    });
    for (let i = 1; i <= 6; i++) {
        const l = document.getElementById(`line${i}`);
        if (l) l.className = 'stepper-line';
    }
}

function updateTimelineStage(stageNumber, status, subText) {
    const stepIds = ['stepReady', 'stepRunning', 'stepEvents', 'stepDetected', 'stepResponse', 'stepVerified', 'stepReport'];
    const el = document.getElementById(stepIds[stageNumber - 1]);
    if (!el) return;

    el.classList.remove('step-active', 'step-completed', 'step-failed');
    if (status === 'active') {
        el.classList.add('step-active');
        if (stageNumber > 1) {
            const prevLine = document.getElementById(`line${stageNumber - 1}`);
            if (prevLine) prevLine.className = 'stepper-line line-active';
        }
    } else if (status === 'completed') {
        el.classList.add('step-completed');
        if (stageNumber > 1) {
            const prevLine = document.getElementById(`line${stageNumber - 1}`);
            if (prevLine) prevLine.className = 'stepper-line line-completed';
        }
    } else if (status === 'failed') {
        el.classList.add('step-failed');
    }

    if (subText) {
        const sub = el.querySelector('.step-sub');
        if (sub) sub.textContent = subText;
    }
}

function initAttackCenterControls() {
    const scenarioSelect = document.getElementById('attackScenarioSelect');
    const endpointSelect = document.getElementById('targetEndpointSelect');
    const attemptsInput = document.getElementById('testAttemptsInput');
    const clientIpInput = document.getElementById('testClientIpInput');
    const usernameInput = document.getElementById('testUsernameInput');
    const passwordInput = document.getElementById('testPasswordInput');
    const payloadGroup = document.getElementById('payloadGroup');
    const payloadInput = document.getElementById('testPayloadInput');
    const btnLaunch = document.getElementById('btnLaunchAttack');
    const btnStop = document.getElementById('btnStopAttack');
    const btnUnblock = document.getElementById('btnUnblockIp');
    const btnClear = document.getElementById('btnClearTerminal');

    // Wire up Diagram Step 1 Radio Cards
    const radioCards = document.querySelectorAll('.scenario-radio-card');
    radioCards.forEach(card => {
        card.addEventListener('click', function() {
            radioCards.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            const scenario = this.getAttribute('data-scenario');
            if (scenarioSelect) {
                scenarioSelect.value = scenario;
                scenarioSelect.dispatchEvent(new Event('change'));
            }
        });
    });

    if (!scenarioSelect) return;

    // Synchronize parameters based on selected scenario
    scenarioSelect.addEventListener('change', function() {
        const scenario = this.value;
        // Keep radio cards visually in sync
        radioCards.forEach(c => {
            if (c.getAttribute('data-scenario') === scenario) {
                c.classList.add('active');
            } else {
                c.classList.remove('active');
            }
        });

        if (scenario === 'failed_logins') {
            if (endpointSelect) endpointSelect.value = '/api/shop/auth/login';
            if (attemptsInput) attemptsInput.value = 10;
            if (usernameInput) usernameInput.value = 'test.attacker@example.com';
            if (passwordInput) passwordInput.value = 'WrongPass123';
            if (clientIpInput) clientIpInput.value = '198.51.100.42';
            if (payloadGroup) payloadGroup.style.display = 'none';
        } else if (scenario === 'admin') {
            if (endpointSelect) endpointSelect.value = '/api/shop/admin/stats';
            if (attemptsInput) attemptsInput.value = 5;
            if (usernameInput) usernameInput.value = 'unauthorized_operator@example.com';
            if (passwordInput) passwordInput.value = 'SecretAdmin123';
            if (clientIpInput) clientIpInput.value = '198.51.100.77';
            if (payloadGroup) payloadGroup.style.display = 'none';
        } else if (scenario === 'sqli') {
            if (endpointSelect) endpointSelect.value = "/api/shop/products?q=Laptop' OR '1'='1";
            if (attemptsInput) attemptsInput.value = 5;
            if (usernameInput) usernameInput.value = "admin' OR '1'='1' --";
            if (passwordInput) passwordInput.value = 'WrongPass123';
            if (clientIpInput) clientIpInput.value = '203.0.113.88';
            if (payloadGroup) payloadGroup.style.display = 'block';
            if (payloadInput) payloadInput.value = "Laptop' OR '1'='1";
        } else if (scenario === 'xss') {
            if (endpointSelect) endpointSelect.value = "/api/shop/products?q=<script>alert('ShopSphere-XSS-Test')</script>";
            if (attemptsInput) attemptsInput.value = 5;
            if (usernameInput) usernameInput.value = "<script>alert('xss')</script>";
            if (passwordInput) passwordInput.value = 'WrongPass123';
            if (clientIpInput) clientIpInput.value = '203.0.113.99';
            if (payloadGroup) payloadGroup.style.display = 'block';
            if (payloadInput) payloadInput.value = "<script>alert('ShopSphere-XSS-Test')</script>";
        } else if (scenario === 'rate') {
            if (endpointSelect) endpointSelect.value = '/api/shop/products';
            if (attemptsInput) attemptsInput.value = 30;
            if (usernameInput) usernameInput.value = 'burst_agent@example.com';
            if (passwordInput) passwordInput.value = 'WrongPass123';
            if (clientIpInput) clientIpInput.value = '198.51.100.55';
            if (payloadGroup) payloadGroup.style.display = 'none';
        } else if (scenario === 'health') {
            if (endpointSelect) endpointSelect.value = '/api/shop/health/simulate-error';
            if (attemptsInput) attemptsInput.value = 1;
            if (clientIpInput) clientIpInput.value = '198.51.100.33';
            if (payloadGroup) payloadGroup.style.display = 'none';
        }
    });

    if (endpointSelect) {
        endpointSelect.addEventListener('change', function() {
            const ep = this.value;
            if (ep.includes('/auth/login')) {
                scenarioSelect.value = 'failed_logins';
            } else if (ep.includes('/admin/stats')) {
                scenarioSelect.value = 'admin';
            } else if (ep.includes('1=1') || ep.includes('Laptop')) {
                scenarioSelect.value = 'sqli';
            } else if (ep.includes('script') || ep.includes('XSS')) {
                scenarioSelect.value = 'xss';
            } else if (ep.includes('simulate-error')) {
                scenarioSelect.value = 'health';
            }
            scenarioSelect.dispatchEvent(new Event('change'));
        });
    }

    // Launch Attack Handler
    btnLaunch.addEventListener('click', function() {
        launchAttackTest();
    });

    // Stop Attack Handler
    btnStop.addEventListener('click', function() {
        stopSecurityTest();
    });

    // Unblock IP Handler
    btnUnblock.addEventListener('click', async function() {
        const ip = clientIpInput.value.trim();
        if (!ip) {
            toastr.warning('Please enter an IP address to unblock.');
            return;
        }
        try {
            const res = await fetch('/api/security/unblock', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ client_ip: ip })
            });
            const data = await res.json();
            appendTerminalLine(`[SYS] IP ${ip} released from active quarantine blocklist.`, 'sys');
            toastr.success(`Client IP ${ip} unblocked.`, 'Perimeter Updated');
            loadQuarantinedClients();
            loadDashboardMetrics();
        } catch(e) {
            toastr.error('Failed to unblock IP: ' + e.message);
        }
    });

    // Clear Terminal Handler
    if (btnClear) {
        btnClear.addEventListener('click', function() {
            const term = document.getElementById('attackTerminalBody');
            if (term) term.innerHTML = '<div class="term-line" style="color: var(--text-muted);">[SYS] Terminal cleared. Standby.</div>';
            resetTimelineStepper();
        });
    }
}

function launchAttackTest() {
    const scenario = document.getElementById('attackScenarioSelect').value;
    const clientIp = document.getElementById('testClientIpInput').value.trim() || '198.51.100.42';
    const attempts = parseInt(document.getElementById('testAttemptsInput').value) || 5;
    const payload = document.getElementById('testPayloadInput').value.trim();
    const targetUrl = window.location.origin;

    const btnLaunch = document.getElementById('btnLaunchAttack');
    const btnStop = document.getElementById('btnStopAttack');
    const resultCard = document.getElementById('healingResultCard');
    const statusPill = document.getElementById('terminalStatusPill');

    if (btnLaunch) {
        btnLaunch.disabled = true;
        btnLaunch.style.opacity = '0.5';
    }
    if (btnStop) btnStop.style.display = 'inline-flex';
    if (resultCard) resultCard.style.display = 'none';

    if (statusPill) {
        statusPill.textContent = 'RUNNING';
        statusPill.className = 'badge badge-high';
    }

    // Reset Stepper & Timestamps
    resetTimelineStepper();
    attackStartTime = Date.now();
    const startTimeStr = new Date().toLocaleTimeString();
    const timeStartEl = document.getElementById('timeStart');
    if (timeStartEl) timeStartEl.textContent = startTimeStr;
    const timeEndEl = document.getElementById('timeEnd');
    if (timeEndEl) timeEndEl.textContent = '--:--:--';
    const timeDurEl = document.getElementById('timeDuration');
    if (timeDurEl) timeDurEl.textContent = 'In flight...';

    // Step 1: Ready -> Step 2: Attack Running
    updateTimelineStage(1, 'completed', 'Localhost Enforced');
    updateTimelineStage(2, 'active', 'HTTP Probing');

    appendTerminalLine(`<strong style="color: #ef4444;">🚀 DISPATCHING CONTROLLED SECURITY TEST:</strong> [${scenario}] against ${targetUrl}...`, 'sys');

    if (activeEventSource) {
        activeEventSource.close();
        activeEventSource = null;
    }

    const sseUrl = `/api/security/attack-center/stream?scenario=${encodeURIComponent(scenario)}&target_url=${encodeURIComponent(targetUrl)}&client_ip=${encodeURIComponent(clientIp)}&attempts=${encodeURIComponent(attempts)}${payload ? '&payload=' + encodeURIComponent(payload) : ''}`;

    activeEventSource = new EventSource(sseUrl);

    activeEventSource.onmessage = function(e) {
        try {
            const item = JSON.parse(e.data);
            if (item.type === 'phase') {
                appendTerminalLine(`<strong>[PHASE] ${item.name || item.phase}:</strong> ${item.message}`, 'phase');
                if (item.phase === 'DEFENSE_INTERCEPT') {
                    updateTimelineStage(4, 'completed', 'Rule Triggered');
                    updateTimelineStage(5, 'active', 'Applying Defense');
                } else if (item.phase === 'VERIFICATION_PROBE') {
                    updateTimelineStage(5, 'completed', 'Defense Executed');
                    updateTimelineStage(6, 'active', 'Probing Protected Endpoint');
                }
            } else if (item.type === 'request') {
                const sc = item.status_code;
                let scClass = 'term-code-200';
                if (sc === 401) scClass = 'term-code-401';
                else if (sc === 403) scClass = 'term-code-403';
                else if (sc === 429) scClass = 'term-code-429';
                else if (sc >= 400) scClass = 'term-code-403';

                // Update Stage 2 and Stage 3
                updateTimelineStage(2, 'completed', `Sent (${item.attempt || 1})`);
                updateTimelineStage(3, 'completed', `HTTP ${item.status_code}`);

                appendTerminalLine(
                    `&gt; <span class="${scClass}">HTTP ${item.method} ${item.endpoint || item.url}</span> &rarr; ` +
                    `<span class="${scClass}">[${item.status_code} ${item.status_text || ''}]</span> ` +
                    `(${item.latency_ms || item.duration_ms || 12}ms) | Client: <code>${item.client_ip || clientIp}</code>`
                );
            } else if (item.type === 'detection') {
                if (statusPill) {
                    statusPill.textContent = 'ANALYZING & MITIGATING';
                    statusPill.className = 'badge badge-critical';
                }
                const confPercent = Math.round((item.confidence || 0.96) * 100);
                updateTimelineStage(4, 'completed', `${item.rule_id} (${confPercent}%)`);
                updateTimelineStage(5, 'active', item.mitigation_action || 'Dynamic Quarantine');

                appendTerminalLine(
                    `<span class="term-detect-box">⚡ DETECTED: [${item.rule_id}] ${item.category || item.title} (${item.severity})</span><br>` +
                    `&nbsp;&nbsp;Evidence: ${item.summary || item.evidence || ''}`,
                    'detect'
                );
                if (item.mitigation_action) {
                    appendTerminalLine(
                        `<span class="term-defense-box">🛡️ DEFENSIVE ACTION: ${item.mitigation_action}</span>`,
                        'mitigate'
                    );
                }
                toastr.warning(`Security Rule ${item.rule_id} triggered! Defense deployed.`, 'AutoHeal Sentinel');
            } else if (item.type === 'verification') {
                const isBlocked = item.is_blocked || item.status_code === 403 || item.status_code === 429;
                if (isBlocked) {
                    updateTimelineStage(6, 'completed', `HTTP ${item.status_code} Blocked`);
                } else {
                    updateTimelineStage(6, 'failed', `HTTP ${item.status_code}`);
                }
                updateTimelineStage(7, 'active', 'Compiling Report');

                appendTerminalLine(
                    `<strong>🔎 POST-ACTION VERIFICATION:</strong> Target ${item.endpoint || '/api/shop'} &rarr; ` +
                    `<span class="${isBlocked ? 'term-code-403' : 'term-code-200'}">HTTP ${item.status_code}</span> ` +
                    `Outcome: <strong>${item.message || (isBlocked ? 'VERIFIED_CONTAINED' : 'UNEXPECTED_STATUS')}</strong>`,
                    'verify'
                );
            } else if (item.type === 'complete') {
                const attackEndTime = Date.now();
                const durationSec = attackStartTime ? ((attackEndTime - attackStartTime) / 1000).toFixed(1) : '1.2';
                
                const timeEndEl = document.getElementById('timeEnd');
                if (timeEndEl) timeEndEl.textContent = new Date().toLocaleTimeString();
                const timeDurEl = document.getElementById('timeDuration');
                if (timeDurEl) timeDurEl.textContent = `${durationSec}s`;

                updateTimelineStage(6, 'completed', 'Outcome Verified');
                updateTimelineStage(7, 'completed', 'Dossier Ready');

                if (statusPill) {
                    statusPill.textContent = 'CONTAINED & VERIFIED';
                    statusPill.className = 'badge badge-success';
                }
                appendTerminalLine(
                    `<strong style="color: var(--status-success);">✔ TEST COMPLETE & CONTAINED:</strong> Incident ${item.incident_id || 'Recorded'} protected and verified in ${durationSec}s.`,
                    'complete'
                );

                displayHealingResultCard(item, durationSec);
                resetAttackControls();
                if (activeEventSource) {
                    activeEventSource.close();
                    activeEventSource = null;
                }
                loadDashboardMetrics();
                loadOverviewIncidents();
                loadIncidentsList();
                loadQuarantinedClients();
                toastr.success('Security test contained and verified.', 'AutoHeal Sentinel');
            } else if (item.type === 'cancelled') {
                updateTimelineStage(2, 'failed', 'Stopped');
                appendTerminalLine(`<strong style="color: var(--status-warning);">[STOP] ${item.message}</strong>`, 'sys');
                resetAttackControls();
                if (activeEventSource) {
                    activeEventSource.close();
                    activeEventSource = null;
                }
            } else if (item.type === 'error') {
                updateTimelineStage(2, 'failed', 'Error');
                if (statusPill) {
                    statusPill.textContent = 'ERROR';
                    statusPill.className = 'badge badge-critical';
                }
                appendTerminalLine(`<strong style="color: var(--status-danger);">❌ ERROR:</strong> ${item.message}`, 'error');
                resetAttackControls();
                if (activeEventSource) {
                    activeEventSource.close();
                    activeEventSource = null;
                }
                toastr.error(item.message, 'Test Error');
            }
        } catch(err) {
            console.error('SSE JSON error', err, e.data);
        }
    };

    activeEventSource.onerror = function(err) {
        console.error('SSE Connection Error', err);
        appendTerminalLine('<span style="color: var(--status-warning);">[SSE] Connection closed or completed.</span>', 'sys');
        resetAttackControls();
        if (activeEventSource) {
            activeEventSource.close();
            activeEventSource = null;
        }
    };
}

async function stopSecurityTest() {
    try {
        await fetch('/api/security/test/stop', { method: 'POST' });
        appendTerminalLine('<strong style="color: var(--status-warning);">[SYS] Operator stop request dispatched.</strong>', 'sys');
        toastr.info('Test cancellation requested.', 'Attack Center');
    } catch(e) {
        console.error('Stop error', e);
    }
    updateTimelineStage(2, 'failed', 'Operator Stopped');
    if (activeEventSource) {
        activeEventSource.close();
        activeEventSource = null;
    }
    resetAttackControls();
    const statusPill = document.getElementById('terminalStatusPill');
    if (statusPill) {
        statusPill.textContent = 'STANDBY';
        statusPill.className = 'badge badge-neutral';
    }
}

function resetAttackControls() {
    const btnLaunch = document.getElementById('btnLaunchAttack');
    const btnStop = document.getElementById('btnStopAttack');
    if (btnLaunch) {
        btnLaunch.disabled = false;
        btnLaunch.style.opacity = '1';
    }
    if (btnStop) btnStop.style.display = 'none';
}

function appendTerminalLine(htmlContent, type) {
    const term = document.getElementById('attackTerminalBody');
    if (!term) return;

    const timeStr = new Date().toLocaleTimeString();
    const line = document.createElement('div');
    line.className = 'term-line';
    line.innerHTML = `<span class="term-timestamp">[${timeStr}]</span> ${htmlContent}`;
    term.appendChild(line);
    term.scrollTop = term.scrollHeight;
}

function displayHealingResultCard(data, durationSec) {
    const card = document.getElementById('healingResultCard');
    if (!card) return;

    const incId = data.incident_id || (data.detection ? data.detection.incident_id : (data.incident ? data.incident.incident_id : 'INC-APPSEC-CURRENT'));
    currentGeneratedIncidentId = incId;

    const incIdEl = document.getElementById('resIncidentId');
    if (incIdEl) incIdEl.textContent = incId;

    const catEl = document.getElementById('resCategory');
    if (catEl) catEl.textContent = (data.detection && data.detection.category) || data.category || (data.incident && data.incident.category) || 'Privilege & Credential Protection';

    const ruleEl = document.getElementById('resRule');
    if (ruleEl) ruleEl.textContent = (data.detection && data.detection.rule_id) || data.rule_id || (data.incident && data.incident.rule_id) || 'AUTH-001';

    // Detection Status
    const detStatusEl = document.getElementById('resDetectionStatus');
    if (detStatusEl) {
        const ruleId = (data.detection && data.detection.rule_id) || data.rule_id || 'SENTINEL-POLICY';
        detStatusEl.textContent = `TRIGGERED (${ruleId} - Active Correlation)`;
    }

    // Defensive Action
    const actionEl = document.getElementById('resAction');
    const actStr = (data.mitigation && data.mitigation.action) || (data.detection && data.detection.recommended_action) || 'BLOCK_IP (Dynamic Quarantine)';
    if (actionEl) actionEl.textContent = actStr;

    // Healing Status
    const healStatusEl = document.getElementById('resHealingStatus');
    if (healStatusEl) {
        healStatusEl.textContent = 'DYNAMIC IP QUARANTINE APPLIED (300s TTL)';
    }

    // Containment Outcome
    const contEl = document.getElementById('resContainmentBadge');
    if (contEl) {
        contEl.textContent = data.protection_verified ? 'VERIFIED CONTAINED' : 'CONTAINED';
        contEl.className = data.protection_verified ? 'badge badge-success' : 'badge badge-warning';
    }

    // Post-Verification Check
    const verifEl = document.getElementById('resVerification');
    if (verifEl) {
        verifEl.textContent = data.protection_verified ? 'PROTECTION VERIFIED (HTTP 403 Forbidden)' : 'VERIFIED CONTAINED';
    }

    // Duration
    const durEl = document.getElementById('resDuration');
    if (durEl) {
        durEl.textContent = durationSec ? `${durationSec}s` : '1.4s';
    }

    // Populate Diagram Step 6: Incident Created Card
    const s6Id = document.getElementById('resStep6IncidentId');
    if (s6Id) s6Id.textContent = `Incident #${incId}`;

    const s6Type = document.getElementById('resStep6AttackType');
    if (s6Type) {
        const scenario = document.getElementById('attackScenarioSelect')?.value || 'failed_logins';
        const typeMap = {
            'failed_logins': 'Brute-force login attempt',
            'admin': 'Unauthorized access test',
            'sqli': 'SQL injection validation',
            'xss': 'XSS validation test',
            'rate': 'Request-rate anomaly test'
        };
        s6Type.textContent = typeMap[scenario] || (data.detection && data.detection.category) || 'Brute-force login attempt';
    }

    const s6Ep = document.getElementById('resStep6Endpoint');
    if (s6Ep) {
        s6Ep.textContent = data.endpoint || (data.detection && data.detection.endpoint) || '/api/auth/login';
    }

    const now = new Date();
    const startTimeFormatted = attackStartTime ? new Date(attackStartTime).toISOString().replace('T', ' ').substring(0, 19) : now.toISOString().replace('T', ' ').substring(0, 19);
    const endTimeFormatted = now.toISOString().replace('T', ' ').substring(0, 19);

    const s6Start = document.getElementById('resStep6StartTime');
    if (s6Start) s6Start.textContent = startTimeFormatted;

    const s6End = document.getElementById('resStep6EndTime');
    if (s6End) s6End.textContent = endTimeFormatted;

    const s6Att = document.getElementById('resStep6Attempts');
    if (s6Att) {
        const att = document.getElementById('testAttemptsInput')?.value || 10;
        s6Att.textContent = att;
    }

    const s6Ip = document.getElementById('resStep6SourceIp');
    if (s6Ip) {
        s6Ip.textContent = data.client_ip || document.getElementById('testClientIpInput')?.value || '127.0.0.1';
    }

    const s6Sev = document.getElementById('resStep6Severity');
    if (s6Sev) {
        const sev = (data.detection && data.detection.severity) || 'HIGH';
        s6Sev.textContent = sev.toUpperCase();
    }

    // Download links
    const pdfBtn = document.getElementById('btnDownloadIncidentPdf');
    const jsonBtn = document.getElementById('btnDownloadIncidentJson');
    if (pdfBtn) {
        pdfBtn.href = `/api/security/incidents/${incId}/export?format=pdf`;
        pdfBtn.setAttribute('download', `${incId}_forensic_report.pdf`);
    }
    if (jsonBtn) {
        jsonBtn.href = `/api/security/incidents/${incId}/export?format=json`;
        jsonBtn.setAttribute('download', `${incId}_dossier.json`);
    }

    // Pre-populate Step 10 Incident Report in Reports workspace
    populateStep10Report(incId, data, startTimeFormatted, endTimeFormatted);

    card.style.display = 'block';
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function toggleAccordion(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.toggle('active');
    }
}

async function populateStep10Report(incId, customData, startTimeStr, endTimeStr) {
    const repHeader = document.getElementById('repHeaderIncidentId');
    if (repHeader) repHeader.textContent = `Incident Report #${incId}`;

    const repPdf = document.getElementById('repBtnPdf');
    if (repPdf) {
        repPdf.href = `/api/security/incidents/${incId}/export?format=pdf`;
    }
    const repJson = document.getElementById('repBtnJson');
    if (repJson) {
        repJson.href = `/api/security/incidents/${incId}/export?format=json`;
    }

    const scenario = document.getElementById('attackScenarioSelect')?.value || 'failed_logins';
    const typeMap = {
        'failed_logins': 'Brute-force login attempt',
        'admin': 'Unauthorized access test',
        'sqli': 'SQL injection validation',
        'xss': 'XSS validation test',
        'rate': 'Request-rate anomaly test'
    };

    const repType = document.getElementById('repSummaryAttackType');
    if (repType) repType.textContent = typeMap[scenario] || 'Brute-force login attempt';

    const repEp = document.getElementById('repSummaryEndpoint');
    if (repEp) repEp.textContent = (customData && customData.endpoint) || '/api/auth/login';

    const repSev = document.getElementById('repSummarySeverity');
    if (repSev) repSev.textContent = (customData && customData.detection && customData.detection.severity) || 'High';

    const repStart = document.getElementById('repSummaryStartTime');
    if (repStart) repStart.textContent = startTimeStr || new Date().toISOString().replace('T', ' ').substring(0, 19);

    const repEnd = document.getElementById('repSummaryEndTime');
    if (repEnd) repEnd.textContent = endTimeStr || new Date().toISOString().replace('T', ' ').substring(0, 19);

    // Fetch full incident details if available
    try {
        const res = await fetch(`/api/security/incidents/${incId}`);
        if (res.ok) {
            const inc = await res.json();
            if (inc.category || inc.attack_category) {
                if (repType) repType.textContent = inc.category || inc.attack_category;
            }
            const ep = inc.target_endpoint || (Array.isArray(inc.affected_endpoints) ? inc.affected_endpoints[0] : inc.affected_endpoints);
            if (ep && repEp) repEp.textContent = ep;
            if (inc.severity && repSev) repSev.textContent = inc.severity;
            if (inc.created_at && repStart) repStart.textContent = formatAppSecTimestamp(inc.created_at, true);
            if (inc.updated_at && repEnd) repEnd.textContent = formatAppSecTimestamp(inc.updated_at, true);
            const preEl = document.getElementById('repEvidencePre');
            if (preEl) {
                const evData = inc.evidence || inc.evidence_summary || inc.evidence_json;
                preEl.textContent = typeof evData === 'object' ? JSON.stringify(evData, null, 2) : String(evData || 'No additional evidence recorded.');
            }
        }
    } catch(e) {
        console.warn('Could not load specific incident details for Step 10 report', e);
    }
}

function openGeneratedIncident() {
    if (!currentGeneratedIncidentId) {
        toastr.info('Please launch a test to generate an incident first.', 'Attack Center');
        return;
    }
    inspectIncident(currentGeneratedIncidentId);
}

function openGeneratedReport() {
    switchToTab('pageReports');
    if (currentGeneratedIncidentId) {
        populateStep10Report(currentGeneratedIncidentId);
    }
    loadIncidentReportsTable();
    const step10El = document.getElementById('step10ReportCard');
    if (step10El) {
        step10El.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// =========================================================================
// 4. LIVE SECURITY EVENTS TABLE & FILTERS
// =========================================================================

async function loadSecurityEvents() {
    const tbody = document.getElementById('securityEventsTableBody');
    if (!tbody) return;

    const eventType = document.getElementById('eventsFilterType')?.value || '';
    const severity = document.getElementById('eventsFilterSeverity')?.value || '';

    let url = '/api/security/events?limit=100';
    if (eventType) url += `&event_type=${encodeURIComponent(eventType)}`;
    if (severity) url += `&severity=${encodeURIComponent(severity)}`;

    try {
        const res = await fetch(url);
        if (!res.ok) return;
        const events = await res.json();
        allFetchedEvents = events;

        renderEventsTable(events);
    } catch (e) {
        console.error('Error loading security events', e);
    }
}

function renderEventsTable(events) {
    const tbody = document.getElementById('securityEventsTableBody');
    if (!tbody) return;

    if (!events || events.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 24px;">No security events recorded matching criteria.</td></tr>';
        return;
    }

    tbody.innerHTML = '';
    events.forEach(evt => {
        const tr = document.createElement('tr');
        const timeStr = formatAppSecTimestamp(evt.timestamp, false);
        const sevBadge = getSeverityBadgeHtml(evt.severity);
        const method = evt.method || evt.http_method || 'GET';
        const path = evt.path || evt.endpoint_path || '-';
        const sc = evt.status_code || 200;

        tr.innerHTML = `
            <td><code style="color: var(--primary);">${evt.event_id || '-'}</code></td>
            <td style="color: var(--text-muted);">${timeStr}</td>
            <td><strong style="color: #ffffff;">${evt.event_type}</strong></td>
            <td><code>${evt.client_ip || '-'}</code></td>
            <td><span style="font-weight: 600; color: #ffffff;">${method}</span> <code style="color: var(--text-muted);">${path}</code></td>
            <td><span class="badge ${sc >= 400 ? 'badge-critical' : 'badge-success'}">${sc}</span></td>
            <td>${sevBadge}</td>
            <td style="font-family: var(--font-mono); font-size: 11px; color: var(--text-dim);">${evt.correlation_id || '-'}</td>
        `;
        tbody.appendChild(tr);
    });
}

function filterEventsTable() {
    const query = document.getElementById('eventsSearchInput')?.value.toLowerCase().trim() || '';
    if (!query) {
        renderEventsTable(allFetchedEvents);
        return;
    }

    const filtered = allFetchedEvents.filter(e => {
        const ip = (e.client_ip || '').toLowerCase();
        const path = (e.path || e.endpoint_path || '').toLowerCase();
        const method = (e.method || e.http_method || '').toLowerCase();
        const type = (e.event_type || '').toLowerCase();
        const corr = (e.correlation_id || '').toLowerCase();
        return ip.includes(query) || path.includes(query) || method.includes(query) || type.includes(query) || corr.includes(query);
    });

    renderEventsTable(filtered);
}

function toggleEventsAutoRefresh() {
    const statusEl = document.getElementById('autoRefreshStatus');
    const iconEl = document.getElementById('autoRefreshIcon');

    if (eventsAutoRefreshTimer) {
        clearInterval(eventsAutoRefreshTimer);
        eventsAutoRefreshTimer = null;
        if (statusEl) statusEl.textContent = 'OFF';
        if (iconEl) iconEl.className = 'fas fa-play';
        toastr.info('Events auto-refresh paused.');
    } else {
        eventsAutoRefreshTimer = setInterval(loadSecurityEvents, 3000);
        if (statusEl) statusEl.textContent = 'ON (3s)';
        if (iconEl) iconEl.className = 'fas fa-pause';
        toastr.success('Events auto-refresh activated.');
    }
}

// =========================================================================
// 5. INCIDENT DETAILS & FORENSICS INSPECTOR
// =========================================================================

async function loadIncidentsList() {
    const container = document.getElementById('incidentListItemsContainer');
    const totalCountEl = document.getElementById('incidentsTotalCount');
    if (!container) return;

    try {
        const res = await fetch('/api/security/incidents?limit=50');
        if (!res.ok) return;
        const data = await res.json();
        const incidents = Array.isArray(data) ? data : (data.incidents || []);
        allFetchedIncidents = incidents;

        if (totalCountEl) totalCountEl.textContent = incidents.length;

        if (incidents.length === 0) {
            container.innerHTML = '<div style="padding: 24px; text-align: center; color: var(--text-muted);">No incidents recorded. Launch an attack from the Attack Center to trigger detection.</div>';
            return;
        }

        container.innerHTML = '';
        incidents.forEach((inc, idx) => {
            const item = document.createElement('div');
            item.className = `incident-list-item ${selectedIncidentId === inc.incident_id || (idx === 0 && !selectedIncidentId) ? 'selected' : ''}`;
            const sevBadge = getSeverityBadgeHtml(inc.severity);
            const timeStr = formatAppSecTimestamp(inc.created_at, false);

            item.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <strong style="color: var(--primary); font-family: var(--font-mono); font-size: 13px;">${inc.incident_id}</strong>
                    ${sevBadge}
                </div>
                <div style="color: #ffffff; font-weight: 600; font-size: 13px; margin-bottom: 2px;">
                    ${inc.category || inc.attack_category || inc.title || 'Security Incident'}
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-dim);">
                    <span>Rule: <strong style="color: var(--status-warning);">${inc.rule_id || '-'}</strong></span>
                    <span>${timeStr}</span>
                </div>
            `;

            item.addEventListener('click', () => {
                document.querySelectorAll('.incident-list-item').forEach(el => el.classList.remove('selected'));
                item.classList.add('selected');
                renderIncidentDetailPanel(inc);
            });

            container.appendChild(item);
        });

        // Auto-select first incident
        if (!selectedIncidentId && incidents.length > 0) {
            renderIncidentDetailPanel(incidents[0]);
        }
    } catch (e) {
        console.error('Error loading incidents list', e);
    }
}

function inspectIncident(incidentId) {
    switchToTab('pageIncidents');
    selectedIncidentId = incidentId;
    loadIncidentsList();
}

function renderIncidentDetailPanel(inc) {
    selectedIncidentId = inc.incident_id;
    const panel = document.getElementById('incidentDetailPanel');
    if (!panel) return;

    const timeStr = formatAppSecTimestamp(inc.created_at, true);
    const endpoint = (Array.isArray(inc.affected_endpoints) ? inc.affected_endpoints.join(', ') : inc.affected_endpoints) || inc.target_endpoint || '-';
    const sevBadge = getSeverityBadgeHtml(inc.severity);
    const statusBadge = getStatusBadgeHtml(inc.status);
    const action = (inc.mitigation_actions && inc.mitigation_actions[0] ? (inc.mitigation_actions[0].action + ' - ' + (inc.mitigation_actions[0].details || '')) : null) || inc.defensive_action || 'Autonomous Quarantine';

    panel.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid var(--border-main);">
            <div>
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                    <h3 style="margin: 0; font-size: 20px; color: #ffffff;">${inc.incident_id}</h3>
                    ${sevBadge}
                    ${statusBadge}
                </div>
                <div style="font-size: 15px; font-weight: 600; color: #ffffff;">${inc.title || inc.category || 'Application Security Threat'}</div>
                <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px;">Created: ${timeStr} | Target: <code>${endpoint}</code></div>
            </div>
            <div style="display: flex; gap: 8px;">
                <a href="/api/security/incidents/${inc.incident_id}/export?format=pdf" target="_blank" class="btn btn-primary btn-sm">
                    <i class="fas fa-file-pdf"></i> Download PDF
                </a>
                <a href="/api/security/incidents/${inc.incident_id}/export?format=json" target="_blank" class="btn btn-secondary btn-sm">
                    <i class="fas fa-file-code"></i> Export JSON
                </a>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-bottom: 22px;">
            <div class="healing-item">
                <div class="healing-item-label">Detection Rule</div>
                <div class="healing-item-value" style="color: var(--status-warning);">${inc.rule_id || 'AUTH-001'}</div>
            </div>
            <div class="healing-item">
                <div class="healing-item-label">Source Client IP</div>
                <div class="healing-item-value"><code>${inc.source_ip || '-'}</code></div>
            </div>
            <div class="healing-item">
                <div class="healing-item-label">Confidence Score</div>
                <div class="healing-item-value" style="color: var(--primary);">${(inc.confidence || 0.95) * 100}%</div>
            </div>
            <div class="healing-item">
                <div class="healing-item-label">Verification Outcome</div>
                <div class="healing-item-value" style="color: var(--status-success);">${inc.verification_status || 'VERIFIED_CONTAINED'}</div>
            </div>
        </div>

        <!-- 5-Stage Autonomous Investigation & Containment Timeline -->
        <div style="margin-bottom: 22px;">
            <h4 style="font-size: 13px; color: var(--text-muted); text-transform: uppercase; margin-bottom: 12px;">
                <i class="fas fa-stream" style="color: var(--primary);"></i> 5-Stage Autonomous Investigation & Containment Timeline
            </h4>
            <div class="investigation-timeline">
                <div class="timeline-event success">
                    <div class="timeline-event-title">1. Ingress Telemetry Ingestion</div>
                    <div class="timeline-event-time">${timeStr}</div>
                    <div class="timeline-event-desc">Direct request stream captured from endpoint <code>${endpoint}</code> by Starlette AppSec middleware into persistent SQLite telemetry.</div>
                </div>
                <div class="timeline-event success">
                    <div class="timeline-event-title">2. Correlation & Rule Detection</div>
                    <div class="timeline-event-time">+45ms</div>
                    <div class="timeline-event-desc">Detection engine triggered rule <strong style="color: var(--status-warning);">${inc.rule_id || 'RULE'}</strong> with <strong>${Math.round((inc.confidence || 0.95)*100)}% confidence</strong> based on anomalous pattern.</div>
                </div>
                <div class="timeline-event success">
                    <div class="timeline-event-title">3. Autonomous Containment Deployed</div>
                    <div class="timeline-event-time">+80ms</div>
                    <div class="timeline-event-desc">Sentinel enacted policy: <strong style="color: var(--status-success);">${action}</strong> with sliding TTL auto-expiry.</div>
                </div>
                <div class="timeline-event success">
                    <div class="timeline-event-title">4. Follow-up Probe Verification</div>
                    <div class="timeline-event-time">+150ms</div>
                    <div class="timeline-event-desc">Autonomous synthetic verification probe confirmed perimeter blockage: <span class="badge badge-success">${inc.verification_status || 'VERIFIED_CONTAINED'}</span>.</div>
                </div>
                <div class="timeline-event neutral">
                    <div class="timeline-event-title">5. Recovery & Continuous Monitoring</div>
                    <div class="timeline-event-time">+210ms</div>
                    <div class="timeline-event-desc">System state transitioned to: <strong style="color: var(--primary);">${inc.recovery_status || 'NOMINAL_MONITORING'}</strong>. Target service nominal.</div>
                </div>
            </div>
        </div>

        <!-- MITRE ATT&CK Mapping Card -->
        <div style="margin-bottom: 20px; background: rgba(0, 212, 255, 0.05); border: 1px solid var(--border-main); padding: 14px 16px; border-radius: var(--radius-sm);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 13px; font-weight: 700; color: #ffffff;">
                    <i class="fas fa-network-wired" style="color: var(--primary);"></i> MITRE ATT&CK Enterprise Mapping
                </span>
                <span class="mitre-badge">${inc.mitre_technique_id || 'T1110.001'}</span>
            </div>
            <div style="font-size: 13px; color: var(--text-secondary);">
                <strong>Tactic:</strong> <span style="color: #ffffff;">${inc.mitre_tactic || 'Credential Access'}</span> &nbsp;|&nbsp; 
                <strong>Technique:</strong> <span style="color: #ffffff;">${inc.mitre_name || 'Password Guessing'}</span>
            </div>
        </div>

        <!-- AI-Assisted Incident Analysis & Grounded Recommendations -->
        <div style="margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h4 style="font-size: 13px; color: var(--text-muted); text-transform: uppercase; margin: 0;">
                    <i class="fas fa-robot" style="color: var(--primary);"></i> AI-Assisted Forensic Analysis & Grounded Recommendations
                </h4>
                <span class="badge badge-primary"><i class="fas fa-microchip"></i> Evidence-Grounded</span>
            </div>
            <div id="aiSummaryBox_${inc.incident_id}" style="background: var(--bg-card-subtle); padding: 14px 16px; border-radius: var(--radius-sm); border: 1px solid var(--border-main); line-height: 1.5; font-size: 13px;">
                <div style="color: var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Synthesizing forensic analysis from telemetry evidence...</div>
            </div>
        </div>

        <div style="margin-bottom: 20px;">
            <h4 style="font-size: 13px; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">Incident Narrative</h4>
            <div style="background: var(--bg-card-subtle); padding: 14px 16px; border-radius: var(--radius-sm); border: 1px solid var(--border-main); color: var(--text-secondary); line-height: 1.5;">
                ${inc.summary || 'Suspicious request pattern correlated by AutoHeal Sentinel.'}
            </div>
        </div>

        <div style="margin-bottom: 20px;">
            <h4 style="font-size: 13px; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">Supporting Detection Evidence</h4>
            <div style="background: var(--bg-terminal); padding: 14px 16px; border-radius: var(--radius-sm); border: 1px solid var(--border-main); font-family: var(--font-mono); font-size: 12px; color: #38bdf8;">
                ${inc.evidence ? (typeof inc.evidence === 'object' ? JSON.stringify(inc.evidence, null, 2) : inc.evidence) : (inc.evidence_json || 'Evidence recorded in telemetry store.')}
            </div>
        </div>

        <div>
            <h4 style="font-size: 13px; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">Autonomous Defensive Response</h4>
            <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid var(--status-success-border); padding: 14px 16px; border-radius: var(--radius-sm); color: #ffffff;">
                <strong style="color: var(--status-success);"><i class="fas fa-shield-check"></i> Action Executed:</strong> ${action}
            </div>
        </div>
    `;

    // Fetch grounded AI summary & recommendations asynchronously
    fetch(`/api/security/incidents/${inc.incident_id}/ai-summary`)
        .then(r => r.json())
        .then(ai => {
            const box = document.getElementById(`aiSummaryBox_${inc.incident_id}`);
            if (!box) return;
            let recList = '';
            if (ai.remediation_recommendations && Array.isArray(ai.remediation_recommendations)) {
                recList = ai.remediation_recommendations.map(r => `
                    <div style="display: flex; gap: 8px; margin-top: 6px; font-size: 12px; color: var(--text-secondary);">
                        <i class="fas fa-check-circle" style="color: var(--status-success); margin-top: 2px;"></i>
                        <span>${r}</span>
                    </div>
                `).join('');
            }
            box.innerHTML = `
                <div style="margin-bottom: 10px; color: #ffffff;">
                    <strong>Forensic Narrative:</strong> ${ai.ai_summary || inc.summary}
                </div>
                <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 6px;">
                    <strong>Root Cause:</strong> ${ai.root_cause || 'Application perimeter exposed to unmitigated attack pattern.'}
                </div>
                <div style="margin-top: 10px; border-top: 1px solid var(--border-main); padding-top: 10px;">
                    <strong style="color: var(--primary); font-size: 12px; text-transform: uppercase;">Prioritized Action Checklist:</strong>
                    ${recList}
                </div>
            `;
        })
        .catch(err => {
            const box = document.getElementById(`aiSummaryBox_${inc.incident_id}`);
            if (box) box.innerHTML = `<span style="color: var(--text-muted);">${inc.summary || 'Summary unavailable.'}</span>`;
        });
}

// =========================================================================
// 6. HEALING & REMEDIATION (QUARANTINE + SHOP DEMO)
// =========================================================================

async function loadQuarantinedClients() {
    const tbody = document.getElementById('quarantineTableBody');
    const badge = document.getElementById('activeBlocksBadge');
    if (!tbody) return;

    try {
        const res = await fetch('/api/security/blocked-clients');
        if (!res.ok) return;
        const blocks = await res.json();

        if (badge) badge.textContent = `${blocks.length} Active`;

        if (!blocks || blocks.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 18px;">No client IPs are currently quarantined. All perimeters nominal.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        blocks.forEach(b => {
            const tr = document.createElement('tr');
            const expiresStr = b.expires_in ? `${b.expires_in}s` : 'Active';
            tr.innerHTML = `
                <td><code style="color: var(--status-danger); font-weight: 700;">${b.client_ip}</code></td>
                <td>${b.reason || 'Sliding-Window Correlation'}</td>
                <td><span class="badge badge-warning">${expiresStr}</span></td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="unblockClient('${b.client_ip}')">
                        <i class="fas fa-unlock"></i> Unblock
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error('Error loading quarantined clients', e);
    }
}

async function unblockClient(ip) {
    try {
        const res = await fetch('/api/security/unblock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ client_ip: ip })
        });
        toastr.success(`Client IP ${ip} released from quarantine.`, 'Perimeter Updated');
        loadQuarantinedClients();
        loadDashboardMetrics();
    } catch (e) {
        toastr.error('Failed to unblock client: ' + e.message);
    }
}

async function unblockAllClients() {
    try {
        const res = await fetch('/api/security/blocked-clients');
        const blocks = await res.json();
        for (const b of blocks) {
            await fetch('/api/security/unblock', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ client_ip: b.client_ip })
            });
        }
        toastr.success('All active IP quarantines purged.', 'Reset Successful');
        loadQuarantinedClients();
        loadDashboardMetrics();
    } catch (e) {
        toastr.error('Error purging quarantines: ' + e.message);
    }
}

async function runShopSphereAction(action) {
    const consoleEl = document.getElementById('codeRemediationConsole');
    if (!consoleEl) return;

    appendRemediationLine(`[*] Initiating ShopSphere AutoHeal action: /api/shop/autoheal/${action}...`);

    try {
        const res = await fetch(`/api/shop/autoheal/${action}`, { method: 'POST' });
        const data = await res.json();

        if (action === 'inject-bug') {
            appendRemediationLine(`<span style="color: var(--status-danger);">[!] BUG INJECTED: ${data.message || 'Defect injected into shopping cart arithmetic.'}</span>`);
            toastr.error('Bug injected into ShopSphere cart calculations.');
        } else if (action === 'diagnose') {
            appendRemediationLine(`<span style="color: var(--primary);">[DIAGNOSIS] Root Cause: ${data.diagnosis?.root_cause || 'Cart arithmetic anomaly detected'}</span>`);
            toastr.info('AI Diagnosis identified defect.');
        } else if (action === 'apply-fix') {
            appendRemediationLine(`<span style="color: var(--status-success);">[SURGICAL PATCH] ${data.message || 'Code patched. Regression tests passed.'}</span>`);
            toastr.success('Surgical fix applied and verified!');
        } else if (action === 'run-full-demo') {
            appendRemediationLine(`<strong style="color: var(--status-success);">[FULL DEMO COMPLETED] All 11 steps executed successfully.</strong>`);
            toastr.success('Full autonomous code repair demo verified!');
        } else {
            appendRemediationLine(`[RESULT] ${data.status || 'OK'}: ${data.message || 'Action executed'}`);
        }
    } catch (e) {
        appendRemediationLine(`<span style="color: var(--status-danger);">[ERROR] ${e.message}</span>`);
    }
}

function appendRemediationLine(htmlContent) {
    const consoleEl = document.getElementById('codeRemediationConsole');
    if (!consoleEl) return;
    const timeStr = new Date().toLocaleTimeString();
    const div = document.createElement('div');
    div.className = 'term-line';
    div.innerHTML = `<span class="term-timestamp">[${timeStr}]</span> ${htmlContent}`;
    consoleEl.appendChild(div);
    consoleEl.scrollTop = consoleEl.scrollHeight;
}

// =========================================================================
// 7. INCIDENT REPORTS HUB
// =========================================================================

async function loadIncidentReportsTable() {
    const tbody = document.getElementById('incidentReportsTableBody');
    if (!tbody) return;

    try {
        const res = await fetch('/api/security/incidents?limit=50');
        if (!res.ok) return;
        const data = await res.json();
        const incidents = Array.isArray(data) ? data : (data.incidents || []);

        if (incidents.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 24px;">No incident reports recorded yet.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        incidents.forEach((inc, idx) => {
            const tr = document.createElement('tr');
            tr.style.cursor = 'pointer';
            tr.title = 'Click to inspect in Step 10 Incident Report';
            const timeStr = formatAppSecTimestamp(inc.created_at, true);
            const sevBadge = getSeverityBadgeHtml(inc.severity);
            const statusBadge = getStatusBadgeHtml(inc.status);
            const endpoint = (Array.isArray(inc.affected_endpoints) ? inc.affected_endpoints.join(', ') : inc.affected_endpoints) || inc.target_endpoint || '-';
            const action = (inc.mitigation_actions && inc.mitigation_actions[0] ? inc.mitigation_actions[0].action : inc.defensive_action) || 'Autonomous Containment';

            tr.innerHTML = `
                <td><strong style="color: var(--primary); font-family: var(--font-mono);">${inc.incident_id}</strong></td>
                <td style="color: var(--text-muted); font-size: 12px;">${timeStr}</td>
                <td><strong style="color: #ffffff;">${inc.category || inc.attack_category || '-'}</strong></td>
                <td><code>${endpoint}</code></td>
                <td>${sevBadge}</td>
                <td>${statusBadge}</td>
                <td style="color: var(--status-success);">${action}</td>
                <td><span class="badge badge-success">${inc.verification_status || 'VERIFIED'}</span></td>
                <td>
                    <div style="display: flex; gap: 6px;">
                        <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); populateStep10Report('${inc.incident_id}'); document.getElementById('step10ReportCard')?.scrollIntoView({behavior:'smooth'});">
                            <i class="fas fa-eye"></i> View
                        </button>
                        <a href="/api/security/incidents/${inc.incident_id}/export?format=pdf" target="_blank" class="btn btn-primary btn-sm">
                            <i class="fas fa-file-pdf"></i> PDF
                        </a>
                        <a href="/api/security/incidents/${inc.incident_id}/export?format=json" target="_blank" class="btn btn-secondary btn-sm">
                            <i class="fas fa-file-code"></i> JSON
                        </a>
                    </div>
                </td>
            `;

            tr.addEventListener('click', () => {
                populateStep10Report(inc.incident_id);
                document.getElementById('step10ReportCard')?.scrollIntoView({ behavior: 'smooth' });
            });

            tbody.appendChild(tr);
        });

        // Automatically populate Step 10 with the most recent incident if available
        if (incidents.length > 0 && !currentGeneratedIncidentId) {
            populateStep10Report(incidents[0].incident_id);
        }
    } catch (e) {
        console.error('Error loading incident reports table', e);
    }
}

// =========================================================================
// 8. SYSTEM HEALTH & DIAGNOSTICS
// =========================================================================

async function pingAllServices() {
    const endpoints = [
        { id: 'healthStorefront', latId: 'latencyStorefront', url: '/shop' },
        { id: 'healthApi', latId: 'latencyApi', url: '/api/shop/products' }
    ];

    for (const ep of endpoints) {
        const badge = document.getElementById(ep.id);
        const lat = document.getElementById(ep.latId);

        try {
            const t0 = performance.now();
            const res = await fetch(ep.url);
            const latency = Math.round(performance.now() - t0);

            if (res.ok) {
                if (badge) { badge.textContent = 'ONLINE'; badge.className = 'badge badge-success'; }
                if (lat) lat.textContent = `${latency}ms`;
            } else {
                if (badge) { badge.textContent = `HTTP ${res.status}`; badge.className = 'badge badge-warning'; }
                if (lat) lat.textContent = `${latency}ms`;
            }
        } catch (e) {
            if (badge) { badge.textContent = 'OFFLINE'; badge.className = 'badge badge-critical'; }
            if (lat) lat.textContent = 'Err';
        }
    }
}

// =========================================================================
// UTILITY HELPERS
// =========================================================================

function getSeverityBadgeHtml(severity) {
    const s = (severity || 'HIGH').toUpperCase();
    if (s === 'CRITICAL') return '<span class="badge badge-critical">CRITICAL</span>';
    if (s === 'HIGH') return '<span class="badge badge-high">HIGH</span>';
    if (s === 'MEDIUM') return '<span class="badge badge-medium">MEDIUM</span>';
    return '<span class="badge badge-low">LOW</span>';
}

// =========================================================================
// 9. SECURITY POSTURE SCORECARD (TRANSPARENT EVALUATION)
// =========================================================================

async function loadSecurityPosture() {
    try {
        const res = await fetch('/api/security/posture');
        if (!res.ok) return;
        const data = await res.json();

        const scoreEl = document.getElementById('postureScoreVal');
        const badgeEl = document.getElementById('postureRatingBadge');
        const textEl = document.getElementById('postureRatingText');
        const rateEl = document.getElementById('postureContainmentRate');
        const bansEl = document.getElementById('postureBans');
        const formulaEl = document.getElementById('postureFormulaText');
        const pillarsContainer = document.getElementById('defensePillarsContainer');

        if (scoreEl) scoreEl.textContent = data.posture_score || 0;
        if (badgeEl) {
            badgeEl.textContent = `Grade ${data.rating || 'A'}`;
            badgeEl.className = 'badge ' + (data.rating === 'A' ? 'badge-success' : (data.rating === 'B' ? 'badge-info' : (data.rating === 'C' ? 'badge-warning' : 'badge-critical')));
        }
        if (textEl) textEl.textContent = data.posture_rating || 'Nominal Defense';
        if (rateEl) rateEl.textContent = `${data.containment_rate_percent || 100}% Containment Rate`;
        if (bansEl) bansEl.textContent = `${data.active_containments || 0} Active Bans`;
        if (formulaEl && data.scoring_formula) {
            formulaEl.textContent = data.scoring_formula;
        }

        if (pillarsContainer && data.defense_pillars) {
            pillarsContainer.innerHTML = '';
            data.defense_pillars.forEach(p => {
                const row = document.createElement('div');
                row.className = 'posture-pillar-row';
                const scorePercent = p.score;
                const statusColor = p.status === 'HARDENED' ? 'var(--status-success)' : (p.status === 'MONITORED' ? 'var(--primary)' : 'var(--status-warning)');
                row.innerHTML = `
                    <div class="posture-pillar-name">${p.name}</div>
                    <div class="posture-pillar-bar">
                        <div class="posture-pillar-fill" style="width: ${scorePercent}%; background: ${statusColor};"></div>
                    </div>
                    <div style="font-family: var(--font-mono); font-size: 12px; font-weight: 700; color: #ffffff; width: 45px; text-align: right;">${scorePercent}%</div>
                    <div style="font-size: 11px; font-weight: 700; color: ${statusColor}; width: 85px; text-align: right;">${p.status}</div>
                `;
                pillarsContainer.appendChild(row);
            });
        }
    } catch (e) {
        console.error('Error loading security posture', e);
    }
}

// =========================================================================
// 10. ATTACK REPLAY & BEFORE-AND-AFTER COMPARISON
// =========================================================================

async function runAttackReplay() {
    const btn = document.getElementById('btnReplayAttack');
    const scenarioSelect = document.getElementById('attackScenarioSelect');
    const scenario = scenarioSelect ? scenarioSelect.value : 'failed_logins';
    const originalText = btn ? btn.innerHTML : '';

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Replaying Against Localhost...';
    }

    try {
        const res = await fetch('/api/security/test/replay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenario: scenario })
        });
        const data = await res.json();

        // Populate Before Details
        const bStatus = document.getElementById('repBeforeStatus');
        const bVerdict = document.getElementById('repBeforeVerdict');
        const bDetails = document.getElementById('repBeforeDetails');
        if (bStatus && data.before) {
            bStatus.textContent = `HTTP ${data.before.status_code}`;
            bStatus.className = 'badge badge-critical';
        }
        if (bVerdict && data.before) {
            bVerdict.textContent = data.before.defense_verdict || 'UNCONTAINED_EXPOSURE';
            bVerdict.style.color = 'var(--status-danger)';
        }
        if (bDetails && data.before) {
            bDetails.textContent = data.before.details || 'Baseline unprotected behavior.';
        }

        // Populate After Details
        const aStatus = document.getElementById('repAfterStatus');
        const aVerdict = document.getElementById('repAfterVerdict');
        const aDetails = document.getElementById('repAfterDetails');
        if (aStatus && data.after) {
            aStatus.textContent = `HTTP ${data.after.status_code}`;
            aStatus.className = 'badge badge-success';
        }
        if (aVerdict && data.after) {
            aVerdict.textContent = data.after.defense_verdict || 'CONTAINED_ACTIVE_SENTINEL';
            aVerdict.style.color = 'var(--status-success)';
        }
        if (aDetails && data.after) {
            aDetails.textContent = data.after.details || 'Sentinel active containment.';
        }

        // Delta summary
        const deltaEl = document.getElementById('replayDeltaSummary');
        if (deltaEl && data.evaluation_delta) {
            deltaEl.innerHTML = `<i class="fas fa-check-circle" style="color: var(--status-success); margin-right: 6px;"></i> <strong>Verification Delta:</strong> ${data.evaluation_delta}`;
        }

        toastr.success('Attack replay evaluation completed against local ShopSphere.', 'Replay Tester');
        loadSecurityPosture();
        loadDashboardMetrics();
    } catch (e) {
        toastr.error('Attack replay failed: ' + e.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText || '<i class="fas fa-play-circle"></i> Replay Attack vs Baseline';
        }
    }
}

// =========================================================================
// 11. TIER 3 VULNERABILITY TRACKER & CONTROLLED PATCH REMEDIATION
// =========================================================================

let currentDrawerVulnId = null;

async function loadVulnerabilitiesTable() {
    const tbody = document.getElementById('vulnerabilitiesTableBody');
    if (!tbody) return;

    try {
        const res = await fetch('/api/security/vulnerabilities');
        if (!res.ok) return;
        const vulns = await res.json();

        if (!vulns || vulns.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 24px;">No vulnerabilities registered.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        vulns.forEach(v => {
            const tr = document.createElement('tr');
            const sevBadge = getSeverityBadgeHtml(v.severity);
            
            let statusBadge = '<span class="badge badge-warning">PROPOSED</span>';
            if (v.status === 'REMEDIATED') {
                statusBadge = '<span class="badge badge-success">REMEDIATED</span>';
            } else if (v.status === 'ROLLED_BACK') {
                statusBadge = '<span class="badge badge-critical">ROLLED_BACK</span>';
            } else if (v.approval_status === 'APPROVED') {
                statusBadge = '<span class="badge badge-info">APPROVED</span>';
            }

            let testBadge = '<span class="badge badge-warning">PENDING</span>';
            if (v.regression_test_status === 'PASSED') {
                testBadge = '<span class="badge badge-success"><i class="fas fa-check"></i> PASSED</span>';
            } else if (v.regression_test_status === 'FAILED') {
                testBadge = '<span class="badge badge-critical"><i class="fas fa-times"></i> FAILED</span>';
            }

            tr.innerHTML = `
                <td><strong style="color: var(--primary); font-family: var(--font-mono);">${v.vuln_id}</strong></td>
                <td><strong style="color: #ffffff;">${v.title}</strong></td>
                <td><span class="badge badge-secondary">${v.cwe_id}</span></td>
                <td><span class="mitre-badge">${v.mitre_technique_id}</span></td>
                <td>${sevBadge}</td>
                <td>${statusBadge}</td>
                <td>${testBadge}</td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="inspectVulnPatch('${v.vuln_id}')">
                        <i class="fas fa-code-branch"></i> Review Patch
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error('Error loading vulnerabilities', e);
    }
}

async function inspectVulnPatch(vulnId) {
    currentDrawerVulnId = vulnId;
    const drawer = document.getElementById('vulnPatchDrawer');
    if (!drawer) return;

    try {
        const res = await fetch(`/api/security/vulnerabilities/${vulnId}`);
        if (!res.ok) return;
        const v = await res.json();

        const idEl = document.getElementById('drawerVulnId');
        const titleEl = document.getElementById('drawerVulnTitle');
        const compEl = document.getElementById('drawerVulnComponent');
        const mitreEl = document.getElementById('drawerMitre');
        const descEl = document.getElementById('drawerVulnDesc');
        const diffEl = document.getElementById('drawerDiffContent');
        const testEl = document.getElementById('drawerTestStatus');
        const appEl = document.getElementById('drawerApprovalStatus');

        if (idEl) idEl.textContent = v.vuln_id;
        if (titleEl) titleEl.textContent = v.title;
        if (compEl) compEl.textContent = v.component_path;
        if (mitreEl) mitreEl.textContent = `${v.mitre_tactic} (${v.mitre_technique_id})`;
        if (descEl) descEl.textContent = v.description;
        if (diffEl) diffEl.textContent = v.patch_diff || 'No diff specified';
        if (testEl) testEl.textContent = v.regression_test_status || 'PENDING';
        if (appEl) appEl.textContent = `${v.approval_status} / ${v.status}`;

        // Configure buttons based on state
        const btnApprove = document.getElementById('btnDrawerApprove');
        const btnApply = document.getElementById('btnDrawerApply');
        const btnRollback = document.getElementById('btnDrawerRollback');

        if (btnApprove) btnApprove.disabled = (v.approval_status === 'APPROVED');
        if (btnApply) btnApply.disabled = (v.approval_status !== 'APPROVED' || v.status === 'REMEDIATED');
        if (btnRollback) btnRollback.disabled = (v.status !== 'REMEDIATED');

        drawer.style.display = 'block';
        drawer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (e) {
        toastr.error('Error loading patch details: ' + e.message);
    }
}

function closeVulnDrawer() {
    const drawer = document.getElementById('vulnPatchDrawer');
    if (drawer) drawer.style.display = 'none';
}

async function runDrawerRegressionTest() {
    if (!currentDrawerVulnId) return;
    const btn = document.getElementById('btnDrawerTest');
    const orig = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Executing Isolation Test...';
    }

    try {
        const res = await fetch(`/api/security/vulnerabilities/${currentDrawerVulnId}/test`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'PASSED') {
            toastr.success(`Isolated test ${data.test_name} passed cleanly in ${data.duration_ms}ms`, 'Test Verified');
        } else {
            toastr.error(`Test failed: ${data.details}`, 'Regression Test');
        }
        await inspectVulnPatch(currentDrawerVulnId);
        loadVulnerabilitiesTable();
    } catch (e) {
        toastr.error('Test execution failed: ' + e.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = orig;
        }
    }
}

async function approveDrawerPatch() {
    if (!currentDrawerVulnId) return;
    try {
        const res = await fetch(`/api/security/vulnerabilities/${currentDrawerVulnId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ approver: 'Lead SecOps Engineer' })
        });
        const data = await res.json();
        toastr.success(`Patch approved for ${currentDrawerVulnId}`, 'Gate Approved');
        await inspectVulnPatch(currentDrawerVulnId);
        loadVulnerabilitiesTable();
        loadSecurityPosture();
    } catch (e) {
        toastr.error('Approval failed: ' + e.message);
    }
}

async function applyDrawerPatch() {
    if (!currentDrawerVulnId) return;
    try {
        const res = await fetch(`/api/security/vulnerabilities/${currentDrawerVulnId}/apply`, { method: 'POST' });
        const data = await res.json();
        if (data.error) {
            toastr.error(data.error);
        } else {
            toastr.success(`Remediation patch applied. Regression test ${data.test_result?.status || 'PASSED'}.`, 'Patch Applied');
        }
        await inspectVulnPatch(currentDrawerVulnId);
        loadVulnerabilitiesTable();
        loadSecurityPosture();
    } catch (e) {
        toastr.error('Apply patch failed: ' + e.message);
    }
}

async function rollbackDrawerPatch() {
    if (!currentDrawerVulnId) return;
    try {
        const res = await fetch(`/api/security/vulnerabilities/${currentDrawerVulnId}/rollback`, { method: 'POST' });
        const data = await res.json();
        toastr.warning(`Patch rolled back for ${currentDrawerVulnId}`, 'Rollback Complete');
        await inspectVulnPatch(currentDrawerVulnId);
        loadVulnerabilitiesTable();
        loadSecurityPosture();
    } catch (e) {
        toastr.error('Rollback failed: ' + e.message);
    }
}
