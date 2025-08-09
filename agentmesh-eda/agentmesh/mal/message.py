from dataclasses import dataclass, field
from typing import Dict, Any
import uuid
from datetime import datetime


@dataclass
class UniversalMessage:
    metadata: Dict[str, Any] = field(default_factory=dict)
    routing: Dict[str, Any] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    security: Dict[str, Any] = field(default_factory=dict)
    tenant_id: str = "default_tenant"

    def __post_init__(self):
        if not self.metadata.get("id"):
            self.metadata["id"] = str(uuid.uuid4())
        if not self.metadata.get("timestamp"):
            self.metadata["timestamp"] = datetime.utcnow().isoformat()

    def serialize(self) -> bytes:
        import json

        return json.dumps(self.__dict__).encode("utf-8")

    @classmethod
    def deserialize(cls, data: bytes) -> "UniversalMessage":
        import json

        return cls(**json.loads(data))
