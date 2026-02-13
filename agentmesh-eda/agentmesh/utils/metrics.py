from prometheus_client import Counter

# Define metrics
MESSAGES_SENT = Counter(
    "messages_sent_total", "Total number of messages sent", ["platform", "topic"]
)
MESSAGES_RECEIVED = Counter(
    "messages_received_total",
    "Total number of messages received",
    ["platform", "topic"],
)
AGENT_TASKS_COMPLETED = Counter(
    "agent_tasks_completed_total", "Total number of agent tasks completed", ["agent_id"]
)
AGENT_TASKS_FAILED = Counter(
    "agent_tasks_failed_total", "Total number of agent tasks failed", ["agent_id"]
)
EVENT_STORE_EVENTS_SAVED = Counter(
    "event_store_events_saved_total",
    "Total number of events saved to event store",
    ["tenant_id", "aggregate_id", "event_type"],
)
COMMANDS_DISPATCHED = Counter(
    "commands_dispatched_total", "Total number of commands dispatched", ["command_type"]
)
