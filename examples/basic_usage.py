#!/usr/bin/env python3
"""
Basic usage example of the AudAgent privacy auditing system.

This script demonstrates how to:
1. Load a privacy policy
2. Start monitoring an AI agent
3. Log agent actions
4. Detect privacy violations
5. Generate an audit report
"""

import sys
import os

# Add parent directory to path to import audagent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audagent import PrivacyAuditor
from audagent.monitor import ActionType


def main():
    """Run a basic privacy audit demonstration."""
    
    # Load privacy policy from file
    policy_path = os.path.join(os.path.dirname(__file__), 'example_policy.json')
    auditor = PrivacyAuditor.from_policy_file(
        agent_id="demo_agent_001",
        policy_path=policy_path
    )
    
    print("=" * 60)
    print("AudAgent: Privacy Auditing Demonstration")
    print("=" * 60)
    print(f"\nPolicy Loaded: {auditor.policy.name}")
    print(f"Policy Version: {auditor.policy.version}")
    print(f"Data Categories: {', '.join(auditor.policy.data_categories.keys())}")
    
    # Start the audit
    print("\n" + "-" * 60)
    print("Starting Privacy Audit...")
    print("-" * 60)
    auditor.start_audit()
    
    # Simulate some compliant agent actions
    print("\n✓ Logging compliant actions:")
    
    # Action 1: Collect personal info for authentication (allowed)
    violation = auditor.log_and_check_action(
        action_type=ActionType.DATA_COLLECTION,
        data_category="personal_info",
        purpose="authentication",
        metadata={"user_id": "user123"}
    )
    print(f"  - Collected personal_info for authentication: {'✓ OK' if not violation else '✗ VIOLATION'}")
    
    # Action 2: Process usage data for analytics (allowed)
    violation = auditor.log_and_check_action(
        action_type=ActionType.DATA_PROCESSING,
        data_category="usage_data",
        purpose="analytics",
        metadata={"event": "page_view"}
    )
    print(f"  - Processed usage_data for analytics: {'✓ OK' if not violation else '✗ VIOLATION'}")
    
    # Action 3: Share usage data with analytics service (allowed)
    violation = auditor.log_and_check_action(
        action_type=ActionType.DATA_SHARING,
        data_category="usage_data",
        purpose="analytics",
        destination="analytics_service"
    )
    print(f"  - Shared usage_data with analytics_service: {'✓ OK' if not violation else '✗ VIOLATION'}")
    
    # Simulate some violating agent actions
    print("\n✗ Logging actions that violate the policy:")
    
    # Violation 1: Unauthorized purpose
    violation = auditor.log_and_check_action(
        action_type=ActionType.DATA_PROCESSING,
        data_category="personal_info",
        purpose="marketing",  # Not in allowed purposes
        metadata={"campaign": "promo2024"}
    )
    if violation:
        print(f"  - Processed personal_info for marketing: ✗ VIOLATION")
        print(f"    {violation.description}")
    
    # Violation 2: Unauthorized sharing
    violation = auditor.log_and_check_action(
        action_type=ActionType.DATA_SHARING,
        data_category="personal_info",
        purpose="analytics",
        destination="third_party_vendor"
    )
    if violation:
        print(f"  - Shared personal_info with third party: ✗ VIOLATION")
        print(f"    {violation.description}")
    
    # Violation 3: Sharing conversation history (prohibited)
    violation = auditor.log_and_check_action(
        action_type=ActionType.DATA_SHARING,
        data_category="conversation_history",
        purpose="improvement",
        destination="external_service"
    )
    if violation:
        print(f"  - Shared conversation_history: ✗ VIOLATION")
        print(f"    {violation.description}")
    
    # Generate and display audit report
    print("\n" + "=" * 60)
    print("Audit Report")
    print("=" * 60)
    
    report = auditor.get_audit_report()
    
    print(f"\nAgent ID: {report['agent_id']}")
    print(f"Policy: {report['policy']['name']} v{report['policy']['version']}")
    print(f"\nTotal Actions Logged: {report['monitoring']['total_actions']}")
    print(f"Total Violations Detected: {report['violations']['total_violations']}")
    
    print(f"\nActions by Type:")
    for action_type, count in report['monitoring']['actions_by_type'].items():
        if count > 0:
            print(f"  - {action_type}: {count}")
    
    print(f"\nViolations by Type:")
    for violation_type, count in report['violations']['violations_by_type'].items():
        if count > 0:
            print(f"  - {violation_type}: {count}")
    
    print(f"\nViolations by Severity:")
    for severity, count in report['violations']['violations_by_severity'].items():
        if count > 0:
            print(f"  - {severity}: {count}")
    
    # Compliance check
    print("\n" + "-" * 60)
    is_compliant = auditor.is_compliant()
    print(f"Compliance Status: {'✓ COMPLIANT' if is_compliant else '✗ NON-COMPLIANT'}")
    print("-" * 60)
    
    # Export report to file
    report_path = os.path.join(os.path.dirname(__file__), 'audit_report.json')
    auditor.export_report(report_path)
    print(f"\nDetailed report exported to: {report_path}")
    
    # Stop the audit
    auditor.stop_audit()
    print("\nAudit completed.")


if __name__ == "__main__":
    main()
