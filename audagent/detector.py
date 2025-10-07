"""
Violation Detector Module

Detects privacy policy violations based on monitored agent actions.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .policy_parser import PrivacyPolicy
from .monitor import AgentAction, ActionType


class ViolationType(Enum):
    """Types of privacy violations that can be detected."""
    UNAUTHORIZED_PURPOSE = "unauthorized_purpose"
    UNAUTHORIZED_SHARING = "unauthorized_sharing"
    PROHIBITED_ACTION = "prohibited_action"
    MISSING_CONSENT = "missing_consent"
    RETENTION_VIOLATION = "retention_violation"


@dataclass
class Violation:
    """Represents a detected privacy policy violation."""
    violation_type: ViolationType
    severity: str  # "high", "medium", "low"
    description: str
    action: AgentAction
    policy_reference: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary representation."""
        return {
            "violation_type": self.violation_type.value,
            "severity": self.severity,
            "description": self.description,
            "action": self.action.to_dict(),
            "policy_reference": self.policy_reference,
            "timestamp": self.timestamp.isoformat()
        }


class ViolationDetector:
    """Detects privacy policy violations from agent actions."""
    
    def __init__(self, policy: PrivacyPolicy):
        """
        Initialize the violation detector.
        
        Args:
            policy: The privacy policy to enforce
        """
        self.policy = policy
        self.violations: List[Violation] = []
    
    def check_action(self, action: AgentAction) -> Optional[Violation]:
        """
        Check a single action for policy violations.
        
        Args:
            action: The action to check
            
        Returns:
            A Violation object if a violation is detected, None otherwise
        """
        # Check if data category exists in policy
        if action.data_category not in self.policy.data_categories:
            violation = Violation(
                violation_type=ViolationType.UNAUTHORIZED_PURPOSE,
                severity="high",
                description=f"Data category '{action.data_category}' is not defined in the privacy policy",
                action=action,
                policy_reference="data_categories"
            )
            self.violations.append(violation)
            return violation
        
        category = self.policy.data_categories[action.data_category]
        
        # Check purpose authorization
        if action.purpose and category.allowed_purposes:
            if action.purpose not in category.allowed_purposes:
                violation = Violation(
                    violation_type=ViolationType.UNAUTHORIZED_PURPOSE,
                    severity="high",
                    description=f"Purpose '{action.purpose}' is not allowed for data category '{action.data_category}'",
                    action=action,
                    policy_reference=f"data_categories.{action.data_category}.allowed_purposes"
                )
                self.violations.append(violation)
                return violation
        
        # Check sharing authorization
        if action.action_type == ActionType.DATA_SHARING:
            if not category.sharing_allowed:
                violation = Violation(
                    violation_type=ViolationType.UNAUTHORIZED_SHARING,
                    severity="high",
                    description=f"Sharing of '{action.data_category}' data is not allowed",
                    action=action,
                    policy_reference=f"data_categories.{action.data_category}.sharing_allowed"
                )
                self.violations.append(violation)
                return violation
            
            if action.destination and category.sharing_with:
                if action.destination not in category.sharing_with:
                    violation = Violation(
                        violation_type=ViolationType.UNAUTHORIZED_SHARING,
                        severity="high",
                        description=f"Sharing '{action.data_category}' with '{action.destination}' is not authorized",
                        action=action,
                        policy_reference=f"data_categories.{action.data_category}.sharing_with"
                    )
                    self.violations.append(violation)
                    return violation
        
        # Check prohibited actions
        action_desc = f"{action.action_type.value}:{action.data_category}"
        if action_desc in self.policy.prohibited_actions:
            violation = Violation(
                violation_type=ViolationType.PROHIBITED_ACTION,
                severity="high",
                description=f"Action '{action_desc}' is explicitly prohibited",
                action=action,
                policy_reference="prohibited_actions"
            )
            self.violations.append(violation)
            return violation
        
        return None
    
    def check_actions(self, actions: List[AgentAction]) -> List[Violation]:
        """
        Check multiple actions for policy violations.
        
        Args:
            actions: List of actions to check
            
        Returns:
            List of detected violations
        """
        violations = []
        for action in actions:
            violation = self.check_action(action)
            if violation:
                violations.append(violation)
        return violations
    
    def get_violations(
        self,
        violation_type: Optional[ViolationType] = None,
        severity: Optional[str] = None
    ) -> List[Violation]:
        """
        Retrieve detected violations, optionally filtered.
        
        Args:
            violation_type: Filter by violation type
            severity: Filter by severity level
            
        Returns:
            List of matching violations
        """
        violations = self.violations
        
        if violation_type:
            violations = [v for v in violations if v.violation_type == violation_type]
        
        if severity:
            violations = [v for v in violations if v.severity == severity]
        
        return violations
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of detected violations.
        
        Returns:
            Dictionary with violation statistics
        """
        return {
            "total_violations": len(self.violations),
            "violations_by_type": {
                vtype.value: len([v for v in self.violations if v.violation_type == vtype])
                for vtype in ViolationType
            },
            "violations_by_severity": {
                severity: len([v for v in self.violations if v.severity == severity])
                for severity in ["high", "medium", "low"]
            },
            "policy_name": self.policy.name,
            "policy_version": self.policy.version
        }
