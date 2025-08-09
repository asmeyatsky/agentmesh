from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Agent:
    id: str
    tenant_id: str = "default_tenant"  # Add tenant_id
    capabilities: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
