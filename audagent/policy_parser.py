"""
Privacy Policy Parser Module

Parses and structures privacy policies for AI agents.
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DataCategory:
    """Represents a category of data mentioned in the privacy policy."""
    name: str
    description: str
    allowed_purposes: List[str] = field(default_factory=list)
    retention_period: Optional[str] = None
    sharing_allowed: bool = False
    sharing_with: List[str] = field(default_factory=list)


@dataclass
class PrivacyPolicy:
    """Structured representation of a privacy policy."""
    name: str
    version: str
    data_categories: Dict[str, DataCategory] = field(default_factory=dict)
    prohibited_actions: List[str] = field(default_factory=list)
    required_consents: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PrivacyPolicyParser:
    """Parser for privacy policies in various formats."""
    
    def __init__(self):
        """Initialize the privacy policy parser."""
        self.supported_formats = ["json", "yaml"]
    
    def parse_json(self, policy_json: str) -> PrivacyPolicy:
        """
        Parse a privacy policy from JSON format.
        
        Args:
            policy_json: JSON string containing the privacy policy
            
        Returns:
            Structured PrivacyPolicy object
        """
        data = json.loads(policy_json)
        return self._build_policy_from_dict(data)
    
    def parse_file(self, filepath: str) -> PrivacyPolicy:
        """
        Parse a privacy policy from a file.
        
        Args:
            filepath: Path to the policy file
            
        Returns:
            Structured PrivacyPolicy object
        """
        with open(filepath, 'r') as f:
            if filepath.endswith('.json'):
                data = json.load(f)
                return self._build_policy_from_dict(data)
            else:
                raise ValueError(f"Unsupported file format: {filepath}")
    
    def _build_policy_from_dict(self, data: Dict[str, Any]) -> PrivacyPolicy:
        """Build a PrivacyPolicy object from a dictionary."""
        policy = PrivacyPolicy(
            name=data.get("name", "Unknown Policy"),
            version=data.get("version", "1.0"),
            prohibited_actions=data.get("prohibited_actions", []),
            required_consents=data.get("required_consents", []),
            metadata=data.get("metadata", {})
        )
        
        # Parse data categories
        for cat_name, cat_data in data.get("data_categories", {}).items():
            category = DataCategory(
                name=cat_name,
                description=cat_data.get("description", ""),
                allowed_purposes=cat_data.get("allowed_purposes", []),
                retention_period=cat_data.get("retention_period"),
                sharing_allowed=cat_data.get("sharing_allowed", False),
                sharing_with=cat_data.get("sharing_with", [])
            )
            policy.data_categories[cat_name] = category
        
        return policy
    
    def validate_policy(self, policy: PrivacyPolicy) -> List[str]:
        """
        Validate a privacy policy for completeness.
        
        Args:
            policy: The privacy policy to validate
            
        Returns:
            List of validation warnings/errors
        """
        issues = []
        
        if not policy.name:
            issues.append("Policy name is missing")
        
        if not policy.data_categories:
            issues.append("No data categories defined")
        
        for cat_name, category in policy.data_categories.items():
            if not category.allowed_purposes:
                issues.append(f"Category '{cat_name}' has no allowed purposes")
        
        return issues
