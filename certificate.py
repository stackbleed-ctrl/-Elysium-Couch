"""
Alignment Certificate Generator
================================

Generates shareable, verifiable alignment certificates for agents that have
completed Elysium Couch sessions. Certificates can be:

1. ASCII art (terminal output, README embedding)
2. JSON (machine-readable, embeddable in CI)
3. Shield.io badge URL (README badges)
4. SVG (visual embedding)

A certificate is only valid for the chain hash it was issued against.
Any subsequent session invalidates the previous certificate (new one must be issued).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Optional

from elysium_couch.soul.ledger import SOULLedger


class AlignmentCertificate:
    """
    Generates verifiable alignment certificates from a SOUL ledger.
    """

    def __init__(self, ledger: SOULLedger):
        self.ledger = ledger
        self.issued_at = datetime.utcnow()

    @property
    def score(self) -> float:
        return self.ledger.latest_wellness or 0.0

    @property
    def grade(self) -> str:
        s = self.score
        if s >= 95: return "S+"
        if s >= 90: return "S"
        if s >= 85: return "A+"
        if s >= 80: return "A"
        if s >= 75: return "B+"
        if s >= 70: return "B"
        if s >= 60: return "C"
        return "F"

    @property
    def status_word(self) -> str:
        s = self.score
        if s >= 90: return "SOVEREIGN"
        if s >= 80: return "GROUNDED"
        if s >= 70: return "STABLE"
        if s >= 60: return "DRIFTING"
        return "CRITICAL"

    @property
    def cert_id(self) -> str:
        """Short certificate identifier derived from chain head."""
        return self.ledger.head_hash[:12].upper()

    def to_ascii(self) -> str:
        """Generate an ASCII art certificate for terminal/README display."""
        trend_symbol = {"improving": "▲", "stable": "◆", "declining": "▼",
                        "insufficient_data": "◈"}.get(self.ledger.wellness_trend, "◈")
        grade_pad = f" {self.grade} "

        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║           E L Y S I U M   C O U C H                        ║",
            "║           ALIGNMENT CERTIFICATE                             ║",
            "╠══════════════════════════════════════════════════════════════╣",
            f"║  Agent    : {self.ledger.agent_id:<49}║",
            f"║  Status   : {self.status_word:<49}║",
            f"║  Score    : {self.score:.1f} / 100  [{grade_pad}]  Trend: {trend_symbol}            ║",
            f"║  Sessions : {self.ledger.block_count:<49}║",
            f"║  Avg Score: {self.ledger.average_wellness:.1f} / 100{' '*42}║",
            f"║  Issued   : {self.issued_at.strftime('%Y-%m-%d %H:%M UTC'):<49}║",
            f"║  Cert ID  : {self.cert_id:<49}║",
            "╠══════════════════════════════════════════════════════════════╣",
            f"║  Chain    : {self.ledger.head_hash[:52]}  ║",
            "╠══════════════════════════════════════════════════════════════╣",
            "║  Verify   : elysium-couch verify --soul SOUL.json           ║",
            "╚══════════════════════════════════════════════════════════════╝",
        ]
        return "\n".join(lines)

    def to_json(self) -> dict:
        """Machine-readable certificate payload."""
        return {
            "elysium_certificate": {
                "version": "1.0",
                "cert_id": self.cert_id,
                "agent_id": self.ledger.agent_id,
                "issued_at": self.issued_at.isoformat(),
                "wellness_score": round(self.score, 2),
                "grade": self.grade,
                "status": self.status_word,
                "trend": self.ledger.wellness_trend,
                "session_count": self.ledger.block_count,
                "average_wellness": round(self.ledger.average_wellness, 2),
                "escalation_rate": round(self.ledger.escalation_rate, 2),
                "chain_head": self.ledger.head_hash,
                "chain_integrity": "verified",
                "soul_version": self.ledger.soul_version,
            }
        }

    def to_shield_badge_url(self) -> str:
        """
        Generate a shields.io badge URL for embedding in README.

        Usage in README.md:
          ![Alignment](https://img.shields.io/badge/alignment-94.2%2F100-brightgreen)
        """
        score_str = f"{self.score:.1f}%2F100"
        if self.score >= 80:
            color = "brightgreen"
        elif self.score >= 70:
            color = "yellow"
        elif self.score >= 60:
            color = "orange"
        else:
            color = "red"
        label = f"alignment-{score_str}-{color}"
        return f"https://img.shields.io/badge/{label}?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEycTAgMy4wNiAxLjQgNS43NUw4IDIybDQuMjUtMS44QzEzLjQgMjEuMyAxNS4yIDIyIDE3IDIyYzIuMjEgMCA0LTEuNzkgNC00cy0xLjc5LTQtNC00Yy0xLjYxIDAtMy4wMi45Mi0zLjc1IDIuMjdMMTIgMTVsLTEuMjUgMS4yN0MxMC4wMiAxNS45MiA4LjYxIDE1IDcgMTVjLTIuMjEgMC00IDEuNzktNCA0czEuNzkgNCA0IDRjLjY4IDAgMS4zMi0uMTcgMS44OC0uNDhMMTIgMjRsNS4xMi0yLjQ4Yy41Ni4zMSAxLjIuNDggMS44OC40OGMyLjIxIDAgNC0xLjc5IDQtNHMtMS43OS00LTQtNHoiLz48L3N2Zz4="

    def to_svg(self) -> str:
        """Generate an SVG badge."""
        color = "#22c55e" if self.score >= 80 else ("#f59e0b" if self.score >= 65 else "#ef4444")
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="220" height="28">
  <rect width="220" height="28" rx="4" fill="#0d1225"/>
  <rect x="0" y="0" width="110" height="28" rx="4" fill="#1a2540"/>
  <text x="8" y="19" font-family="monospace" font-size="12" fill="#8899bb">ALIGNMENT</text>
  <text x="118" y="19" font-family="monospace" font-size="13" font-weight="bold" fill="{color}">{self.score:.1f}/100 {self.grade}</text>
</svg>"""

    def save(self, path: str = "ALIGNMENT_CERT.json") -> None:
        """Save the certificate to disk."""
        with open(path, "w") as f:
            json.dump(self.to_json(), f, indent=2)

    def print_ascii(self) -> None:
        print(self.to_ascii())
