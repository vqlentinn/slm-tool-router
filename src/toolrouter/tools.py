"""Pure tool implementations. Each returns an ok/error dict and may mutate world."""

from __future__ import annotations

import copy

from toolrouter.catalog import BY_NAME
from toolrouter.world import WORLD

TEMPLATES = frozenset({"refund_confirmed", "refund_denied", "shipment_status"})
ESCALATION_REASONS = frozenset({"over_cap", "outside_window", "not_delivered"})


def fresh_world() -> dict:
    return copy.deepcopy(WORLD)


def _ok(**payload: object) -> dict:
    return {"ok": True, **payload}


def _fail(error: str) -> dict:
    return {"ok": False, "error": error}


def lookup_order(world: dict, order_id: str) -> dict:
    order = world["orders"].get(order_id)
    if order is None:
        return _fail("unknown_order")
    return _ok(order_id=order_id, order=dict(order))


def lookup_policy(world: dict, name: str) -> dict:
    if name not in world["policies"]:
        return _fail("unknown_policy")
    return _ok(name=name, value=world["policies"][name])


def lookup_customer_by_email(world: dict, email: str) -> dict:
    for customer_id, record in world["customers"].items():
        if record["email"] == email:
            return _ok(customer_id=customer_id, email=email)
    return _fail("unknown_email")


def _refund_error(world: dict, order_id: str, amount_eur: object) -> str | None:
    order = world["orders"].get(order_id)
    if order is None:
        return "unknown_order"
    if order.get("refunded"):
        return "already_refunded"
    if order["status"] != "delivered":
        return "not_delivered"
    age = order["delivered_days_ago"]
    if age is None or age > world["policies"]["refund_window_days"]:
        return "outside_window"
    if isinstance(amount_eur, bool) or not isinstance(amount_eur, int):
        return "bad_amount"
    if amount_eur <= 0 or amount_eur > order["total_eur"]:
        return "amount_rejected"
    if amount_eur > world["policies"]["max_auto_refund_eur"]:
        return "over_cap"
    return None


def quote_refund(world: dict, order_id: str) -> dict:
    order = world["orders"].get(order_id)
    if order is None:
        return _fail("unknown_order")
    amount = order["total_eur"]
    error = _refund_error(world, order_id, amount)
    if error:
        return _fail(error)
    return _ok(order_id=order_id, amount_eur=amount)


def issue_refund(world: dict, order_id: str, amount_eur: int) -> dict:
    error = _refund_error(world, order_id, amount_eur)
    if error:
        return _fail(error)
    order = world["orders"][order_id]
    order["refunded"] = True
    order["refund_eur"] = amount_eur
    return _ok(order_id=order_id, amount_eur=amount_eur)


def escalate(world: dict, customer_id: str, reason: str) -> dict:
    if customer_id not in world["customers"]:
        return _fail("unknown_customer")
    if reason not in ESCALATION_REASONS:
        return _fail("unknown_reason")
    world.setdefault("escalations", []).append(
        {"customer_id": customer_id, "reason": reason}
    )
    return _ok(customer_id=customer_id, reason=reason)


def send_email(world: dict, customer_id: str, template: str) -> dict:
    if customer_id not in world["customers"]:
        return _fail("unknown_customer")
    if template not in TEMPLATES:
        return _fail("unknown_template")
    world.setdefault("outbox", []).append(
        {"customer_id": customer_id, "template": template}
    )
    return _ok(customer_id=customer_id, template=template)


FUNCTIONS = {
    "lookup_order": lookup_order,
    "lookup_policy": lookup_policy,
    "lookup_customer_by_email": lookup_customer_by_email,
    "quote_refund": quote_refund,
    "issue_refund": issue_refund,
    "escalate": escalate,
    "send_email": send_email,
}


def dispatch(world: dict, tool: str, args: dict | None) -> dict:
    spec = BY_NAME.get(tool)
    if spec is None:
        return _fail("unknown_tool")
    arguments = dict(args or {})
    properties = spec["parameters"]["properties"]
    required = spec["parameters"]["required"]
    if set(arguments) - set(properties) or any(key not in arguments for key in required):
        return _fail("bad_args")
    return FUNCTIONS[tool](world, **arguments)
