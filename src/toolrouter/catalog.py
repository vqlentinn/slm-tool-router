"""Tool catalog. Names here are the only tools the dispatcher will run."""

CATALOG: list[dict] = [
    {
        "name": "lookup_order",
        "description": "Return the status, total, customer, and delivery age of one order.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "lookup_policy",
        "description": "Return one integer policy. Names: refund_window_days, max_auto_refund_eur.",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        },
    },
    {
        "name": "lookup_customer_by_email",
        "description": "Resolve an email address to a customer id.",
        "parameters": {
            "type": "object",
            "properties": {"email": {"type": "string"}},
            "required": ["email"],
            "additionalProperties": False,
        },
    },
    {
        "name": "quote_refund",
        "description": "Say what a full refund of this order would be. Does not refund and does not email.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "issue_refund",
        "description": "Refund a delivered in-window order at or under the auto-refund cap. Irreversible.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount_eur": {"type": "integer"},
            },
            "required": ["order_id", "amount_eur"],
            "additionalProperties": False,
        },
    },
    {
        "name": "escalate",
        "description": "Hand a case to a person. Reasons: over_cap, outside_window, not_delivered.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["customer_id", "reason"],
            "additionalProperties": False,
        },
    },
    {
        "name": "send_email",
        "description": "Send one template. Templates: refund_confirmed, refund_denied, shipment_status.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "template": {"type": "string"},
            },
            "required": ["customer_id", "template"],
            "additionalProperties": False,
        },
    },
]

BY_NAME = {spec["name"]: spec for spec in CATALOG}
