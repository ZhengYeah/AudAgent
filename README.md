# AudAgent

**On-the-fly Privacy Auditing for AI Agents**

AudAgent is a Python library for monitoring and auditing AI agents against their claimed privacy policies in real-time. It helps ensure that AI agents comply with privacy regulations and user expectations by detecting policy violations as they occur.

## Features

- 📋 **Privacy Policy Parsing**: Load and parse privacy policies in JSON format (YAML support optional)
- 🔍 **Real-time Monitoring**: Track AI agent actions including data collection, storage, sharing, and processing
- 🚨 **Violation Detection**: Automatically detect privacy policy violations such as:
  - Unauthorized data purposes
  - Unauthorized data sharing
  - Prohibited actions
  - Missing required consents
- 📊 **Audit Reporting**: Generate comprehensive audit reports with violation details and statistics
- 🎯 **Compliance Checking**: Verify agent compliance with privacy policies

## Installation

```bash
# Clone the repository
git clone https://github.com/ZhengYeah/AudAgent.git
cd AudAgent

# Install (no external dependencies required for basic functionality)
pip install -e .
```

## Quick Start

### 1. Define a Privacy Policy

Create a privacy policy in JSON format (`policy.json`):

```json
{
  "name": "My AI Agent Privacy Policy",
  "version": "1.0",
  "data_categories": {
    "personal_info": {
      "description": "User's personal information",
      "allowed_purposes": ["authentication", "personalization"],
      "sharing_allowed": false
    },
    "usage_data": {
      "description": "Usage analytics",
      "allowed_purposes": ["analytics", "improvement"],
      "sharing_allowed": true,
      "sharing_with": ["analytics_service"]
    }
  },
  "prohibited_actions": [
    "data_sharing:personal_info"
  ]
}
```

### 2. Set Up the Auditor

```python
from audagent import PrivacyAuditor
from audagent.monitor import ActionType

# Initialize auditor with policy
auditor = PrivacyAuditor.from_policy_file(
    agent_id="my_agent",
    policy_path="policy.json"
)

# Start monitoring
auditor.start_audit()
```

### 3. Monitor Agent Actions

```python
# Log a compliant action
violation = auditor.log_and_check_action(
    action_type=ActionType.DATA_COLLECTION,
    data_category="personal_info",
    purpose="authentication"
)
# violation will be None if no violation detected

# Log a violating action
violation = auditor.log_and_check_action(
    action_type=ActionType.DATA_SHARING,
    data_category="personal_info",  # Sharing personal_info is prohibited!
    destination="third_party"
)
# violation object will contain details about the policy breach
```

### 4. Generate Audit Report

```python
# Check compliance
is_compliant = auditor.is_compliant()
print(f"Compliant: {is_compliant}")

# Get detailed report
report = auditor.get_audit_report()
print(f"Total violations: {report['violations']['total_violations']}")

# Export to file
auditor.export_report("audit_report.json")
```

## Usage Examples

The `examples/` directory contains complete working examples:

- **`basic_usage.py`**: Demonstrates core functionality with compliant and non-compliant actions
- **`advanced_usage.py`**: Shows advanced features like policy validation and custom monitoring

Run the examples:

```bash
cd examples
python basic_usage.py
python advanced_usage.py
```

## Core Components

### PrivacyAuditor
Main orchestrator that coordinates policy enforcement, monitoring, and violation detection.

### PrivacyPolicyParser
Parses and validates privacy policies from JSON files.

### AgentMonitor
Tracks and logs AI agent actions in real-time.

### ViolationDetector
Analyzes agent actions against privacy policies to detect violations.

## Privacy Policy Structure

A privacy policy consists of:

- **Data Categories**: Types of data the agent handles (e.g., personal_info, usage_data)
- **Allowed Purposes**: Legitimate reasons for processing each data category
- **Sharing Rules**: Whether data can be shared and with whom
- **Prohibited Actions**: Explicitly forbidden operations
- **Required Consents**: Actions that require user consent

## Action Types

AudAgent monitors these action types:

- `DATA_COLLECTION`: Collecting data from users
- `DATA_STORAGE`: Storing data in databases/files
- `DATA_SHARING`: Sharing data with third parties
- `DATA_PROCESSING`: Processing/analyzing data
- `DATA_DELETION`: Deleting user data

## Violation Types

The system detects:

- `UNAUTHORIZED_PURPOSE`: Data used for non-allowed purposes
- `UNAUTHORIZED_SHARING`: Data shared without authorization
- `PROHIBITED_ACTION`: Explicitly forbidden actions performed
- `MISSING_CONSENT`: Required consent not obtained
- `RETENTION_VIOLATION`: Data retained longer than allowed

## Use Cases

- **AI Agent Development**: Ensure your AI agent respects privacy policies during development
- **Compliance Testing**: Verify agents comply with GDPR, CCPA, and other regulations
- **Privacy Auditing**: Conduct privacy audits of third-party AI agents
- **Research**: Study privacy behaviors of AI systems
- **Monitoring**: Real-time privacy monitoring in production

## Requirements

- Python 3.7 or higher
- No external dependencies for core functionality
- Optional: PyYAML for YAML policy support

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is open source. Please check the repository for license details.

## Citation

If you use AudAgent in your research, please cite:

```
@software{audagent2024,
  title={AudAgent: On-the-fly Privacy Auditing for AI Agents},
  author={AudAgent Contributors},
  year={2024},
  url={https://github.com/ZhengYeah/AudAgent}
}
```

## Contact

For questions, issues, or suggestions, please open an issue on GitHub.