# Quick Start Guide

This guide will help you get started with AudAgent in 5 minutes.

## Installation

```bash
# Clone the repository
git clone https://github.com/ZhengYeah/AudAgent.git
cd AudAgent

# No installation needed - pure Python with no external dependencies
```

## 5-Minute Tutorial

### Step 1: Run the Basic Example

```bash
cd examples
python basic_usage.py
```

This will show you:
- ✓ How to load a privacy policy
- ✓ How to monitor agent actions
- ✓ How violations are detected
- ✓ How to generate audit reports

### Step 2: Understand the Output

The example will show:
- **Compliant actions** (✓ OK): Actions that follow the policy
- **Violations** (✗ VIOLATION): Actions that break the policy
- **Audit Report**: Summary of all monitored activities

### Step 3: Create Your Own Policy

Create `my_policy.json`:

```json
{
  "name": "My AI Agent Privacy Policy",
  "version": "1.0",
  "data_categories": {
    "user_data": {
      "description": "User information",
      "allowed_purposes": ["service_delivery"],
      "sharing_allowed": false
    }
  }
}
```

### Step 4: Write Your First Audit Script

```python
from audagent import PrivacyAuditor
from audagent.monitor import ActionType

# Load your policy
auditor = PrivacyAuditor.from_policy_file(
    agent_id="my_agent",
    policy_path="my_policy.json"
)

# Start auditing
auditor.start_audit()

# Monitor an action
violation = auditor.log_and_check_action(
    action_type=ActionType.DATA_COLLECTION,
    data_category="user_data",
    purpose="service_delivery"
)

if violation:
    print(f"Violation detected: {violation.description}")
else:
    print("Action is compliant!")

# Check overall compliance
if auditor.is_compliant():
    print("✓ Agent is compliant with privacy policy")
else:
    print("✗ Agent has privacy violations")
```

## What's Next?

1. **Explore Examples**: Check out `advanced_usage.py` for more features
2. **Run Tests**: `python -m unittest tests.test_audagent`
3. **Read the Docs**: See the [README.md](../README.md) for full documentation
4. **Customize**: Create your own privacy policies and audit scenarios

## Key Concepts

- **Privacy Policy**: Defines what data can be collected and how it can be used
- **Agent Actions**: Data collection, storage, sharing, processing, deletion
- **Violations**: Actions that don't comply with the policy
- **Audit Report**: Summary of all actions and detected violations

## Common Use Cases

1. **Development**: Test your AI agent during development
2. **Testing**: Automated privacy testing in CI/CD
3. **Compliance**: Verify GDPR, CCPA compliance
4. **Monitoring**: Real-time privacy monitoring in production

## Need Help?

- Check the examples in `examples/`
- Read the full [README.md](../README.md)
- Open an issue on GitHub
