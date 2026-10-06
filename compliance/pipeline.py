"""
Module 4 — Compliance pipeline stub.
Module 6 Project 4 adds sanctions screening between AML and approval.
"""

from __future__ import annotations

from typing import Any

PIPELINE_STEPS = [
    "kyc_check",
    "aml_analysis",
    "approval",
]


def get_pipeline_sequence() -> list[dict[str, Any]]:
    """Return the current compliance pipeline sequence."""
    return [
        {"step": 1, "name": "kyc_check", "description": "Verify customer identity"},
        {"step": 2, "name": "aml_analysis", "description": "Anti-money laundering screening"},
        {"step": 3, "name": "approval", "description": "Final compliance approval"},
    ]
