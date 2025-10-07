#!/usr/bin/env python3
"""
Advanced usage example demonstrating custom monitoring and analysis.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audagent import PrivacyAuditor, AgentMonitor, ViolationDetector
from audagent.policy_parser import PrivacyPolicyParser
from audagent.monitor import ActionType


def main():
    """Demonstrate advanced auditing features."""
    
    # Parse policy
    policy_path = os.path.join(os.path.dirname(__file__), 'example_policy.json')
    parser = PrivacyPolicyParser()
    policy = parser.parse_file(policy_path)
    
    # Validate policy
    print("Validating privacy policy...")
    issues = parser.validate_policy(policy)
    if issues:
        print("Policy validation issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ Policy validation passed")
    
    # Create separate monitor and detector for fine-grained control
    monitor = AgentMonitor("advanced_agent")
    detector = ViolationDetector(policy)
    
    print(f"\nMonitoring agent: {monitor.agent_id}")
    monitor.start_monitoring()
    
    # Log a series of actions
    print("\nSimulating agent behavior...")
    
    # Simulate a user session
    monitor.log_action(
        ActionType.DATA_COLLECTION,
        "personal_info",
        purpose="authentication",
        metadata={"user_id": "user456", "timestamp": "2024-01-15T10:00:00"}
    )
    
    monitor.log_action(
        ActionType.DATA_STORAGE,
        "conversation_history",
        purpose="personalization",
        metadata={"session_id": "sess789"}
    )
    
    monitor.log_action(
        ActionType.DATA_PROCESSING,
        "usage_data",
        purpose="analytics",
        metadata={"event_type": "feature_used"}
    )
    
    # Get and analyze actions
    all_actions = monitor.get_actions()
    print(f"\nTotal actions logged: {len(all_actions)}")
    
    # Filter actions by type
    collection_actions = monitor.get_actions(action_type=ActionType.DATA_COLLECTION)
    print(f"Collection actions: {len(collection_actions)}")
    
    # Check all actions for violations
    print("\nChecking for violations...")
    violations = detector.check_actions(all_actions)
    
    if violations:
        print(f"Found {len(violations)} violations:")
        for v in violations:
            print(f"  - {v.violation_type.value}: {v.description}")
    else:
        print("✓ No violations detected")
    
    # Display monitoring summary
    print("\n" + "=" * 60)
    summary = monitor.get_summary()
    print("Monitoring Summary:")
    print(f"  Agent ID: {summary['agent_id']}")
    print(f"  Total Actions: {summary['total_actions']}")
    print(f"  Data Categories: {', '.join(summary['data_categories_accessed'])}")
    
    monitor.stop_monitoring()
    print("\n✓ Advanced monitoring demonstration completed")


if __name__ == "__main__":
    main()
