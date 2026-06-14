"""
Plugin Base Class

Abstract base class for all plugins in the system.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict


class PluginBase(ABC):
    """Abstract base class for plugins"""

    def __init__(self):
        self.id = str(uuid.uuid4())
        self.name = "unknown"
        self.version = "1.0.0"
        self.status = "initialized"
        self.created_at = datetime.now(timezone.utc)
        self.last_executed = None
        self.execution_count = 0
        self.error_count = 0

    @abstractmethod
    def load(self, config: Dict[str, Any]) -> bool:
        """Load plugin with configuration"""
        pass

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plugin with given context"""
        pass

    @abstractmethod
    def unload(self) -> bool:
        """Unload plugin and cleanup resources"""
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get current plugin status"""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_executed": (
                self.last_executed.isoformat() if self.last_executed else None
            ),
            "execution_count": self.execution_count,
            "error_count": self.error_count,
        }

    def update_execution_stats(self, success: bool):
        """Update execution statistics"""
        self.execution_count += 1
        self.last_executed = datetime.now(timezone.utc)
        if not success:
            self.error_count += 1
