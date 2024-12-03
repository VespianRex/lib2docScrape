from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class QualityIssue(BaseModel):
    """Model for quality issues found during crawling."""
    type: str = Field(description="Type of quality issue")
    severity: str = Field(default="warning", description="Issue severity")
    message: str = Field(description="Issue description")
    rule_name: str = "general"  # Default rule name for backward compatibility
    location: str = Field(default="", description="Location where issue was found")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the issue")

    def __init__(self, **data):
        if "location" in data and isinstance(data["location"], dict):
            if "url" in data["location"]:
                data["location"] = data["location"]["url"]
        super().__init__(**data) 