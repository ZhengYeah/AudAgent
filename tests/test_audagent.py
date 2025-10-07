"""
Test suite for the AudAgent privacy auditing system.

Run with: python -m pytest tests/
"""

import unittest
import json
import os
import tempfile
from datetime import datetime

from audagent import PrivacyAuditor, PrivacyPolicyParser, AgentMonitor, ViolationDetector
from audagent.policy_parser import DataCategory, PrivacyPolicy
from audagent.monitor import ActionType
from audagent.detector import ViolationType


class TestPolicyParser(unittest.TestCase):
    """Test the PrivacyPolicyParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = PrivacyPolicyParser()
        self.sample_policy = {
            "name": "Test Policy",
            "version": "1.0",
            "data_categories": {
                "personal_info": {
                    "description": "Personal data",
                    "allowed_purposes": ["authentication"],
                    "sharing_allowed": False
                }
            }
        }
    
    def test_parse_json(self):
        """Test parsing JSON policy."""
        policy_json = json.dumps(self.sample_policy)
        policy = self.parser.parse_json(policy_json)
        
        self.assertEqual(policy.name, "Test Policy")
        self.assertEqual(policy.version, "1.0")
        self.assertIn("personal_info", policy.data_categories)
    
    def test_parse_file(self):
        """Test parsing policy from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_policy, f)
            temp_path = f.name
        
        try:
            policy = self.parser.parse_file(temp_path)
            self.assertEqual(policy.name, "Test Policy")
        finally:
            os.unlink(temp_path)
    
    def test_validate_policy(self):
        """Test policy validation."""
        policy = PrivacyPolicy(name="Test", version="1.0")
        issues = self.parser.validate_policy(policy)
        
        self.assertIn("No data categories defined", issues)
    
    def test_data_category_creation(self):
        """Test DataCategory creation."""
        category = DataCategory(
            name="test_data",
            description="Test data category",
            allowed_purposes=["testing"],
            sharing_allowed=True
        )
        
        self.assertEqual(category.name, "test_data")
        self.assertEqual(category.allowed_purposes, ["testing"])
        self.assertTrue(category.sharing_allowed)


class TestAgentMonitor(unittest.TestCase):
    """Test the AgentMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = AgentMonitor("test_agent")
    
    def test_monitor_initialization(self):
        """Test monitor initialization."""
        self.assertEqual(self.monitor.agent_id, "test_agent")
        self.assertFalse(self.monitor.active)
        self.assertEqual(len(self.monitor.action_log), 0)
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor.active)
        
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.active)
    
    def test_log_action(self):
        """Test logging actions."""
        self.monitor.start_monitoring()
        
        action = self.monitor.log_action(
            action_type=ActionType.DATA_COLLECTION,
            data_category="personal_info",
            purpose="authentication"
        )
        
        self.assertEqual(action.action_type, ActionType.DATA_COLLECTION)
        self.assertEqual(action.data_category, "personal_info")
        self.assertEqual(len(self.monitor.action_log), 1)
    
    def test_log_action_without_monitoring(self):
        """Test that logging without monitoring raises error."""
        with self.assertRaises(RuntimeError):
            self.monitor.log_action(
                ActionType.DATA_COLLECTION,
                "personal_info"
            )
    
    def test_get_actions_filter(self):
        """Test filtering actions."""
        self.monitor.start_monitoring()
        
        self.monitor.log_action(ActionType.DATA_COLLECTION, "personal_info")
        self.monitor.log_action(ActionType.DATA_PROCESSING, "personal_info")
        self.monitor.log_action(ActionType.DATA_COLLECTION, "usage_data")
        
        collection_actions = self.monitor.get_actions(action_type=ActionType.DATA_COLLECTION)
        self.assertEqual(len(collection_actions), 2)
        
        personal_info_actions = self.monitor.get_actions(data_category="personal_info")
        self.assertEqual(len(personal_info_actions), 2)
    
    def test_get_summary(self):
        """Test getting monitoring summary."""
        self.monitor.start_monitoring()
        
        self.monitor.log_action(ActionType.DATA_COLLECTION, "personal_info")
        self.monitor.log_action(ActionType.DATA_PROCESSING, "usage_data")
        
        summary = self.monitor.get_summary()
        
        self.assertEqual(summary["agent_id"], "test_agent")
        self.assertEqual(summary["total_actions"], 2)
        self.assertTrue(summary["monitoring_active"])


class TestViolationDetector(unittest.TestCase):
    """Test the ViolationDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.policy = PrivacyPolicy(name="Test Policy", version="1.0")
        self.policy.data_categories["personal_info"] = DataCategory(
            name="personal_info",
            description="Personal data",
            allowed_purposes=["authentication"],
            sharing_allowed=False
        )
        self.policy.prohibited_actions = ["data_sharing:personal_info"]
        
        self.detector = ViolationDetector(self.policy)
        self.monitor = AgentMonitor("test_agent")
        self.monitor.start_monitoring()
    
    def test_detect_unauthorized_purpose(self):
        """Test detecting unauthorized purpose violation."""
        action = self.monitor.log_action(
            ActionType.DATA_PROCESSING,
            "personal_info",
            purpose="marketing"  # Not in allowed_purposes
        )
        
        violation = self.detector.check_action(action)
        
        self.assertIsNotNone(violation)
        self.assertEqual(violation.violation_type, ViolationType.UNAUTHORIZED_PURPOSE)
        self.assertEqual(violation.severity, "high")
    
    def test_detect_unauthorized_sharing(self):
        """Test detecting unauthorized sharing violation."""
        action = self.monitor.log_action(
            ActionType.DATA_SHARING,
            "personal_info",
            destination="third_party"
        )
        
        violation = self.detector.check_action(action)
        
        self.assertIsNotNone(violation)
        self.assertEqual(violation.violation_type, ViolationType.UNAUTHORIZED_SHARING)
    
    def test_detect_prohibited_action(self):
        """Test detecting prohibited action."""
        action = self.monitor.log_action(
            ActionType.DATA_SHARING,
            "personal_info",
            purpose="authentication"
        )
        
        violation = self.detector.check_action(action)
        
        self.assertIsNotNone(violation)
        # Should detect unauthorized sharing first
        self.assertEqual(violation.violation_type, ViolationType.UNAUTHORIZED_SHARING)
    
    def test_compliant_action(self):
        """Test that compliant actions don't trigger violations."""
        action = self.monitor.log_action(
            ActionType.DATA_COLLECTION,
            "personal_info",
            purpose="authentication"
        )
        
        violation = self.detector.check_action(action)
        
        self.assertIsNone(violation)
    
    def test_get_violations(self):
        """Test retrieving violations."""
        action1 = self.monitor.log_action(
            ActionType.DATA_PROCESSING,
            "personal_info",
            purpose="marketing"
        )
        action2 = self.monitor.log_action(
            ActionType.DATA_SHARING,
            "personal_info"
        )
        
        self.detector.check_action(action1)
        self.detector.check_action(action2)
        
        all_violations = self.detector.get_violations()
        self.assertEqual(len(all_violations), 2)
        
        sharing_violations = self.detector.get_violations(
            violation_type=ViolationType.UNAUTHORIZED_SHARING
        )
        self.assertEqual(len(sharing_violations), 1)
    
    def test_get_summary(self):
        """Test getting violation summary."""
        action = self.monitor.log_action(
            ActionType.DATA_PROCESSING,
            "personal_info",
            purpose="marketing"
        )
        self.detector.check_action(action)
        
        summary = self.detector.get_summary()
        
        self.assertEqual(summary["total_violations"], 1)
        self.assertEqual(summary["policy_name"], "Test Policy")


class TestPrivacyAuditor(unittest.TestCase):
    """Test the PrivacyAuditor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.policy = PrivacyPolicy(name="Test Policy", version="1.0")
        self.policy.data_categories["personal_info"] = DataCategory(
            name="personal_info",
            description="Personal data",
            allowed_purposes=["authentication"],
            sharing_allowed=False
        )
        
        self.auditor = PrivacyAuditor("test_agent", self.policy)
    
    def test_auditor_initialization(self):
        """Test auditor initialization."""
        self.assertEqual(self.auditor.agent_id, "test_agent")
        self.assertEqual(self.auditor.policy.name, "Test Policy")
        self.assertFalse(self.auditor.audit_active)
    
    def test_start_stop_audit(self):
        """Test starting and stopping audit."""
        self.auditor.start_audit()
        self.assertTrue(self.auditor.audit_active)
        self.assertTrue(self.auditor.monitor.active)
        
        self.auditor.stop_audit()
        self.assertFalse(self.auditor.audit_active)
        self.assertFalse(self.auditor.monitor.active)
    
    def test_log_and_check_action(self):
        """Test logging and checking actions."""
        self.auditor.start_audit()
        
        # Compliant action
        violation = self.auditor.log_and_check_action(
            ActionType.DATA_COLLECTION,
            "personal_info",
            purpose="authentication"
        )
        self.assertIsNone(violation)
        
        # Non-compliant action
        violation = self.auditor.log_and_check_action(
            ActionType.DATA_PROCESSING,
            "personal_info",
            purpose="marketing"
        )
        self.assertIsNotNone(violation)
    
    def test_is_compliant(self):
        """Test compliance checking."""
        self.auditor.start_audit()
        
        # Start compliant
        self.assertTrue(self.auditor.is_compliant())
        
        # Add violation
        self.auditor.log_and_check_action(
            ActionType.DATA_PROCESSING,
            "personal_info",
            purpose="marketing"
        )
        
        # Now non-compliant
        self.assertFalse(self.auditor.is_compliant())
    
    def test_get_audit_report(self):
        """Test generating audit report."""
        self.auditor.start_audit()
        
        self.auditor.log_and_check_action(
            ActionType.DATA_COLLECTION,
            "personal_info",
            purpose="authentication"
        )
        
        report = self.auditor.get_audit_report()
        
        self.assertEqual(report["agent_id"], "test_agent")
        self.assertEqual(report["policy"]["name"], "Test Policy")
        self.assertIn("monitoring", report)
        self.assertIn("violations", report)
    
    def test_export_report(self):
        """Test exporting audit report."""
        self.auditor.start_audit()
        
        self.auditor.log_and_check_action(
            ActionType.DATA_COLLECTION,
            "personal_info",
            purpose="authentication"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            self.auditor.export_report(temp_path)
            self.assertTrue(os.path.exists(temp_path))
            
            with open(temp_path, 'r') as f:
                report = json.load(f)
                self.assertEqual(report["agent_id"], "test_agent")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_from_policy_file(self):
        """Test creating auditor from policy file."""
        policy_data = {
            "name": "File Policy",
            "version": "1.0",
            "data_categories": {
                "test_data": {
                    "description": "Test",
                    "allowed_purposes": ["testing"]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name
        
        try:
            auditor = PrivacyAuditor.from_policy_file("test_agent", temp_path)
            self.assertEqual(auditor.policy.name, "File Policy")
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
