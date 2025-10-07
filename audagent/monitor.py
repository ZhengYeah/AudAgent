"""
Agent Monitor Module

Monitors AI agent interactions and data flows in real-time.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ActionType(Enum):
    """Types of actions that can be monitored."""
    DATA_COLLECTION = "data_collection"
    DATA_STORAGE = "data_storage"
    DATA_SHARING = "data_sharing"
    DATA_PROCESSING = "data_processing"
    DATA_DELETION = "data_deletion"


@dataclass
class AgentAction:
    """Represents an action performed by an AI agent."""
    timestamp: datetime
    action_type: ActionType
    data_category: str
    purpose: Optional[str] = None
    destination: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type.value,
            "data_category": self.data_category,
            "purpose": self.purpose,
            "destination": self.destination,
            "metadata": self.metadata
        }


class AgentMonitor:
    """Monitors AI agent behavior and data flows."""
    
    def __init__(self, agent_id: str):
        """
        Initialize the agent monitor.
        
        Args:
            agent_id: Unique identifier for the agent being monitored
        """
        self.agent_id = agent_id
        self.action_log: List[AgentAction] = []
        self.active = False
    
    def start_monitoring(self):
        """Start monitoring agent actions."""
        self.active = True
        self.action_log = []
    
    def stop_monitoring(self):
        """Stop monitoring agent actions."""
        self.active = False
    
    def log_action(
        self,
        action_type: ActionType,
        data_category: str,
        purpose: Optional[str] = None,
        destination: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentAction:
        """
        Log an action performed by the agent.
        
        Args:
            action_type: Type of action being performed
            data_category: Category of data involved
            purpose: Purpose of the action
            destination: Where data is being sent (for sharing actions)
            metadata: Additional metadata about the action
            
        Returns:
            The created AgentAction object
        """
        if not self.active:
            raise RuntimeError("Monitor is not active. Call start_monitoring() first.")
        
        action = AgentAction(
            timestamp=datetime.now(),
            action_type=action_type,
            data_category=data_category,
            purpose=purpose,
            destination=destination,
            metadata=metadata or {}
        )
        
        self.action_log.append(action)
        return action
    
    def get_actions(
        self,
        action_type: Optional[ActionType] = None,
        data_category: Optional[str] = None
    ) -> List[AgentAction]:
        """
        Retrieve logged actions, optionally filtered.
        
        Args:
            action_type: Filter by action type
            data_category: Filter by data category
            
        Returns:
            List of matching actions
        """
        actions = self.action_log
        
        if action_type:
            actions = [a for a in actions if a.action_type == action_type]
        
        if data_category:
            actions = [a for a in actions if a.data_category == data_category]
        
        return actions
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of monitored actions.
        
        Returns:
            Dictionary with monitoring statistics
        """
        return {
            "agent_id": self.agent_id,
            "total_actions": len(self.action_log),
            "actions_by_type": {
                action_type.value: len([a for a in self.action_log if a.action_type == action_type])
                for action_type in ActionType
            },
            "data_categories_accessed": list(set(a.data_category for a in self.action_log)),
            "monitoring_active": self.active
        }
