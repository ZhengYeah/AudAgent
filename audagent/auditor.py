"""
Privacy Auditor Module

Main orchestrator for privacy auditing of AI agents.
"""

from typing import Dict, Any, Optional, List
import json

from .policy_parser import PrivacyPolicy, PrivacyPolicyParser
from .monitor import AgentMonitor, ActionType
from .detector import ViolationDetector, Violation


class PrivacyAuditor:
    """
    Main class for auditing AI agents against privacy policies.
    
    Orchestrates policy parsing, action monitoring, and violation detection.
    """
    
    def __init__(self, agent_id: str, policy: PrivacyPolicy):
        """
        Initialize the privacy auditor.
        
        Args:
            agent_id: Unique identifier for the agent being audited
            policy: The privacy policy to enforce
        """
        self.agent_id = agent_id
        self.policy = policy
        self.monitor = AgentMonitor(agent_id)
        self.detector = ViolationDetector(policy)
        self.audit_active = False
    
    @classmethod
    def from_policy_file(cls, agent_id: str, policy_path: str) -> "PrivacyAuditor":
        """
        Create a PrivacyAuditor from a policy file.
        
        Args:
            agent_id: Unique identifier for the agent
            policy_path: Path to the privacy policy file
            
        Returns:
            Initialized PrivacyAuditor instance
        """
        parser = PrivacyPolicyParser()
        policy = parser.parse_file(policy_path)
        return cls(agent_id, policy)
    
    def start_audit(self):
        """Start the privacy audit."""
        self.audit_active = True
        self.monitor.start_monitoring()
    
    def stop_audit(self):
        """Stop the privacy audit."""
        self.audit_active = False
        self.monitor.stop_monitoring()
    
    def log_and_check_action(
        self,
        action_type: ActionType,
        data_category: str,
        purpose: Optional[str] = None,
        destination: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Violation]:
        """
        Log an agent action and immediately check for violations.
        
        Args:
            action_type: Type of action being performed
            data_category: Category of data involved
            purpose: Purpose of the action
            destination: Where data is being sent (for sharing actions)
            metadata: Additional metadata
            
        Returns:
            A Violation object if a violation is detected, None otherwise
        """
        # Log the action
        action = self.monitor.log_action(
            action_type=action_type,
            data_category=data_category,
            purpose=purpose,
            destination=destination,
            metadata=metadata
        )
        
        # Check for violations
        violation = self.detector.check_action(action)
        return violation
    
    def run_audit(self) -> List[Violation]:
        """
        Run a complete audit of all logged actions.
        
        Returns:
            List of all detected violations
        """
        actions = self.monitor.get_actions()
        return self.detector.check_actions(actions)
    
    def get_audit_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive audit report.
        
        Returns:
            Dictionary containing audit results and statistics
        """
        return {
            "agent_id": self.agent_id,
            "policy": {
                "name": self.policy.name,
                "version": self.policy.version
            },
            "monitoring": self.monitor.get_summary(),
            "violations": self.detector.get_summary(),
            "audit_active": self.audit_active,
            "detailed_violations": [v.to_dict() for v in self.detector.violations]
        }
    
    def export_report(self, filepath: str):
        """
        Export the audit report to a JSON file.
        
        Args:
            filepath: Path where the report should be saved
        """
        report = self.get_audit_report()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
    
    def is_compliant(self) -> bool:
        """
        Check if the agent is compliant with the privacy policy.
        
        Returns:
            True if no violations detected, False otherwise
        """
        return len(self.detector.violations) == 0
