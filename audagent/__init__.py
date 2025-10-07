"""
AudAgent: On-the-fly Privacy Auditing for AI Agents

This package provides tools to audit AI agents against their claimed privacy policies.
"""

__version__ = "0.1.0"

from .auditor import PrivacyAuditor
from .policy_parser import PrivacyPolicyParser
from .monitor import AgentMonitor
from .detector import ViolationDetector

__all__ = [
    "PrivacyAuditor",
    "PrivacyPolicyParser",
    "AgentMonitor",
    "ViolationDetector",
]
