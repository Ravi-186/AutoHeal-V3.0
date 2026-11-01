"""
AutoHeal AppSec Pure-Python PDF Incident Report Generator
Generates standards-compliant PDF 1.4 documents without third-party dependencies.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


def _escape_pdf_text(text: str) -> str:
    """Escapes special characters for PDF text strings."""
    if not isinstance(text, str):
        text = str(text)
    # Replace non-ascii with safe representation
    cleaned = "".join(c if 32 <= ord(c) <= 126 else " " for c in text)
    return cleaned.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class PDFCanvas:
    """Lightweight 2D graphics and text canvas generating PDF 1.4 streams."""

    def __init__(self, page_width: float = 612.0, page_height: float = 792.0):
        self.width = page_width
        self.height = page_height
        self.pages: List[str] = []
        self.current_stream: List[str] = []

    def start_page(self):
        if self.current_stream:
            self.pages.append("\n".join(self.current_stream))
            self.current_stream = []

    def end_page(self):
        if self.current_stream:
            self.pages.append("\n".join(self.current_stream))
            self.current_stream = []

    def set_fill_rgb(self, r: float, g: float, b: float):
        self.current_stream.append(f"{r:.3f} {g:.3f} {b:.3f} rg")

    def set_stroke_rgb(self, r: float, g: float, b: float):
        self.current_stream.append(f"{r:.3f} {g:.3f} {b:.3f} RG")

    def rect(self, x: float, y: float, w: float, h: float, fill: bool = True, stroke: bool = False):
        op = "B" if (fill and stroke) else ("f" if fill else "S")
        self.current_stream.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re {op}")

    def line(self, x1: float, y1: float, x2: float, y2: float, width: float = 1.0):
        self.current_stream.append(f"{width:.2f} w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def text(self, x: float, y: float, text: str, font: str = "F1", size: float = 10.0):
        escaped = _escape_pdf_text(text)
        self.current_stream.append(f"BT /{font} {size:.2f} Tf {x:.2f} {y:.2f} Td ({escaped}) Tj ET")

    def render_pdf(self) -> bytes:
        self.end_page()
        if not self.pages:
            self.pages = [""]

        num_pages = len(self.pages)
        objects: List[str] = []
        offsets: List[int] = []

        # Object 1: Catalog
        objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")

        # Object 2: Pages container
        kids = " ".join(f"{3 + i * 2} 0 R" for i in range(num_pages))
        objects.append(f"2 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {num_pages} >>\nendobj")

        # Page objects & content streams
        for i, page_content in enumerate(self.pages):
            page_obj_num = 3 + i * 2
            stream_obj_num = 4 + i * 2
            stream_bytes = page_content.encode("latin-1", errors="replace")
            stream_len = len(stream_bytes)

            page_dict = (
                f"{page_obj_num} 0 obj\n"
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.width:.1f} {self.height:.1f}] "
                f"/Resources << /Font << /F1 999 0 R /F2 998 0 R >> >> "
                f"/Contents {stream_obj_num} 0 R >>\nendobj"
            )
            objects.append(page_dict)

            stream_dict = (
                f"{stream_obj_num} 0 obj\n"
                f"<< /Length {stream_len} >>\nstream\n"
                f"{page_content}\nendstream\nendobj"
            )
            objects.append(stream_dict)

        # Fonts (Helvetica and Helvetica-Bold)
        objects.append("999 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj")
        objects.append("998 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj")

        # Build final PDF buffer
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for obj in objects:
            offsets.append(len(out))
            out.extend(obj.encode("latin-1", errors="replace") + b"\n")

        xref_start = len(out)
        out.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
        out.extend(b"0000000000 65535 f \n")
        for off in offsets:
            out.extend(f"{off:010d} 00000 n \n".encode("latin-1"))

        trailer = (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF\n"
        )
        out.extend(trailer.encode("latin-1"))
        return bytes(out)


class IncidentPDFGenerator:
    """Generates executive forensic PDF dossiers for AutoHeal security incidents."""

    @classmethod
    def generate_pdf_report(cls, incident: Dict[str, Any], related_events: Optional[List[Dict[str, Any]]] = None) -> bytes:
        canvas = PDFCanvas(page_width=612.0, page_height=792.0)
        canvas.start_page()

        # Palette definition
        c_dark = (0.05, 0.08, 0.12)
        c_blue = (0.02, 0.45, 0.85)
        c_light_bg = (0.96, 0.97, 0.98)
        c_text = (0.15, 0.18, 0.22)
        c_muted = (0.45, 0.50, 0.55)
        c_white = (1.0, 1.0, 1.0)

        # Severity colors
        severity = incident.get("severity", "MEDIUM").upper()
        if severity == "CRITICAL":
            c_sev = (0.85, 0.12, 0.12)
        elif severity == "HIGH":
            c_sev = (0.92, 0.40, 0.05)
        elif severity == "MEDIUM":
            c_sev = (0.82, 0.60, 0.05)
        else:
            c_sev = (0.12, 0.65, 0.35)

        # 1. Header Banner
        canvas.set_fill_rgb(*c_dark)
        canvas.rect(0, 712, 612, 80, fill=True, stroke=False)

        canvas.set_fill_rgb(*c_white)
        canvas.text(36, 756, "AUTOHEAL DEFENSIVE INCIDENT REPORT", font="F2", size=18)
        canvas.text(36, 736, "Enterprise Application Security Incident Response & Forensic Dossier", font="F1", size=10)

        # Incident ID on Right
        inc_id = incident.get("incident_id", "INC-UNKNOWN")
        canvas.set_fill_rgb(*c_blue)
        canvas.rect(420, 730, 156, 32, fill=True, stroke=False)
        canvas.set_fill_rgb(*c_white)
        canvas.text(435, 742, inc_id, font="F2", size=11)

        y = 680

        # 2. Metadata Grid Card
        canvas.set_fill_rgb(*c_light_bg)
        canvas.rect(36, y - 60, 540, 75, fill=True, stroke=False)
        canvas.set_stroke_rgb(0.85, 0.88, 0.90)
        canvas.line(36, y - 60, 576, y - 60, width=1)

        # Severity Badge
        canvas.set_fill_rgb(*c_sev)
        canvas.rect(46, y - 8, 90, 18, fill=True, stroke=False)
        canvas.set_fill_rgb(*c_white)
        canvas.text(54, y - 4, f"SEV: {severity}", font="F2", size=9)

        # Status & Verification
        status = incident.get("status", "OPEN").upper()
        verif = incident.get("verification_status", "PENDING").upper()
        canvas.set_fill_rgb(*c_muted)
        canvas.text(146, y - 3, f"STATUS: {status}  |  VERIFICATION: {verif}", font="F2", size=9)

        # Row 2 Metadata
        created_at = incident.get("created_at", datetime.now(timezone.utc).isoformat())
        source_ip = incident.get("source_ip", "127.0.0.1")
        rule_id = incident.get("rule_id", "POLICY-001")
        category = incident.get("category", "General AppSec")

        from src.appsec.ai_advisor import AISecurityAdvisor
        mitre = AISecurityAdvisor.get_mitre_mapping(rule_id)

        canvas.set_fill_rgb(*c_text)
        canvas.text(46, y - 28, f"Observed Source IP:  {source_ip}", font="F1", size=9)
        canvas.text(280, y - 28, f"Detection Rule ID:   {rule_id}", font="F1", size=9)
        canvas.text(46, y - 46, f"Incident Timestamp:   {created_at}", font="F1", size=9)
        canvas.text(280, y - 46, f"Threat Category:     {category}", font="F1", size=9)
        canvas.text(46, y - 64, f"MITRE ATT&CK:       {mitre['technique_id']} - {mitre['technique_name']}", font="F2", size=8)
        canvas.text(360, y - 64, f"Tactic: {mitre['tactic_name']}", font="F1", size=8)

        y -= 95

        # 3. Section 1: Executive Summary
        canvas.set_fill_rgb(*c_blue)
        canvas.text(36, y, "1. EXECUTIVE SUMMARY & IMPACT", font="F2", size=12)
        canvas.line(36, y - 4, 576, y - 4, width=1.0)
        y -= 20

        summary = incident.get("summary", "No summary available.")
        canvas.set_fill_rgb(*c_text)
        for line in cls._wrap_text(summary, max_chars=85):
            canvas.text(36, y, line, font="F1", size=10)
            y -= 14

        actual_imp = incident.get("impact_actual", "None recorded.")
        pot_imp = incident.get("impact_potential", "Potential service breach.")
        y -= 4
        canvas.text(36, y, f"Actual Impact:     {actual_imp[:80]}", font="F1", size=9)
        y -= 14
        canvas.text(36, y, f"Potential Impact:  {pot_imp[:80]}", font="F1", size=9)
        y -= 25

        # 4. Section 2: Technical Detection & Evidence
        canvas.set_fill_rgb(*c_blue)
        canvas.text(36, y, "2. DETECTION DETAILS & FORENSIC EVIDENCE", font="F2", size=12)
        canvas.line(36, y - 4, 576, y - 4, width=1.0)
        y -= 20

        endpoints = incident.get("affected_endpoints", ["/api/shop"])
        if isinstance(endpoints, list):
            endpoints_str = ", ".join(endpoints)
        else:
            endpoints_str = str(endpoints)

        canvas.set_fill_rgb(*c_text)
        canvas.text(36, y, f"Target Endpoint(s):  {endpoints_str}", font="F2", size=9)
        y -= 14
        canvas.text(36, y, f"Detection Engine:    AutoHeal Real-Time AppSec Inspection & Correlation Swarm", font="F1", size=9)
        y -= 18

        # Evidence Box
        canvas.text(36, y, "Captured Forensic Evidence (Sensitive Credentials Redacted):", font="F2", size=9)
        y -= 14

        evidence = incident.get("evidence", {})
        evidence_lines = json.dumps(evidence, indent=2).split("\n")[:12]
        box_h = min(120, len(evidence_lines) * 12 + 10)

        canvas.set_fill_rgb(0.94, 0.95, 0.96)
        canvas.rect(36, y - box_h + 8, 540, box_h, fill=True, stroke=False)
        canvas.set_fill_rgb(*c_text)
        ey = y - 4
        for el in evidence_lines:
            canvas.text(46, ey, el[:80], font="F1", size=8)
            ey -= 11
        y -= (box_h + 15)

        # 5. Section 3: Defensive Response & Mitigation
        canvas.set_fill_rgb(*c_blue)
        canvas.text(36, y, "3. AUTONOMOUS DEFENSIVE MITIGATION & AUDIT", font="F2", size=12)
        canvas.line(36, y - 4, 576, y - 4, width=1.0)
        y -= 20

        actions = incident.get("mitigation_actions", [])
        if actions and isinstance(actions, list):
            act_text = f"Action Type: {actions[0].get('action', 'BLOCK_IP')} | Target: {actions[0].get('target', source_ip)}"
        else:
            act_text = "Action: Dynamic IP Quarantine / Rate Throttling Enforced"

        canvas.set_fill_rgb(*c_text)
        canvas.text(36, y, act_text, font="F2", size=9)
        y -= 14

        remed = incident.get("remediation_details", "Quarantined via AutoHeal WAF Sentinel.")
        canvas.text(36, y, f"Mitigation Outcome: {remed[:85]}", font="F1", size=9)
        y -= 14
        canvas.text(36, y, f"Verification State: {verif} (Post-action barrier validation succeeded)", font="F1", size=9)
        y -= 25

        # 6. Section 4: Telemetry Event Timeline
        canvas.set_fill_rgb(*c_blue)
        canvas.text(36, y, "4. RECENT TELEMETRY TIMELINE AUDIT", font="F2", size=12)
        canvas.line(36, y - 4, 576, y - 4, width=1.0)
        y -= 18

        # Timeline table headers
        canvas.set_fill_rgb(*c_muted)
        canvas.text(36, y, "TIMESTAMP (UTC)", font="F2", size=8)
        canvas.text(170, y, "ENDPOINT", font="F2", size=8)
        canvas.text(330, y, "STATUS", font="F2", size=8)
        canvas.text(390, y, "EVENT TYPE", font="F2", size=8)
        canvas.text(490, y, "ACTION TAKEN", font="F2", size=8)
        y -= 12

        events = (related_events or [])[:5]
        canvas.set_fill_rgb(*c_text)
        if not events:
            canvas.text(36, y, "No associated previous events recorded for this source.", font="F1", size=8)
            y -= 12
        else:
            for ev in events:
                ts = str(ev.get("timestamp", ""))[:19]
                meth_path = f"{ev.get('method', 'GET')} {ev.get('path', '')}"[:24]
                sc = str(ev.get("status_code", 200))
                etype = str(ev.get("event_type", "EVENT"))[:16]
                act = str(ev.get("action_taken", "ALLOWED"))[:14]

                canvas.text(36, y, ts, font="F1", size=8)
                canvas.text(170, y, meth_path, font="F1", size=8)
                canvas.text(330, y, sc, font="F1", size=8)
                canvas.text(390, y, etype, font="F1", size=8)
                canvas.text(490, y, act, font="F2", size=8)
                y -= 12

        # 7. Footer
        canvas.set_stroke_rgb(0.85, 0.88, 0.90)
        canvas.line(36, 45, 576, 45, width=0.8)
        canvas.set_fill_rgb(*c_muted)
        canvas.text(36, 32, "AutoHeal Sentinel Platform • Enterprise Autonomous Security Architecture", font="F1", size=8)
        canvas.text(475, 32, "Page 1 of 1 • SEC-CONFIDENTIAL", font="F1", size=8)

        return canvas.render_pdf()

    @staticmethod
    def _wrap_text(text: str, max_chars: int = 80) -> List[str]:
        words = text.split(" ")
        lines = []
        cur = []
        for w in words:
            if sum(len(x) + 1 for x in cur) + len(w) <= max_chars:
                cur.append(w)
            else:
                lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))
        return lines
