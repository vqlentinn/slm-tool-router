"""Deterministic keyword planner over the public tool catalog."""

from __future__ import annotations

import re

from toolrouter.catalog import CATALOG
from toolrouter.tools import dispatch, fresh_world

ORDER_ID = re.compile(r"\b([A-Z]\d{3})\b")
EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
TELL_CUSTOMER = re.compile(r"[Tt]ell customer (\w+)", re.IGNORECASE)
PAREN_CUSTOMER = re.compile(r"\([Cc]ustomer\s+(\w+)\)")
FOR_CUSTOMER = re.compile(r"for customer (\w+)", re.IGNORECASE)
CUSTOMER_WANTS = re.compile(r"^[Cc]ustomer (\w+) wants", re.IGNORECASE)


def _catalog_terms() -> dict[str, set[str]]:
    terms: dict[str, set[str]] = {}
    for spec in CATALOG:
        blob = f"{spec['name']} {spec['description']}".lower()
        words = set(re.findall(r"[a-z_]+", blob))
        terms[spec["name"]] = words
    return terms


CATALOG_TERMS = _catalog_terms()


def keyword_hits(instruction: str, tool: str) -> int:
    lower = instruction.lower()
    tokens = set(re.findall(r"[a-z_]+", lower))
    return len(tokens & CATALOG_TERMS[tool])


def _extract_order_id(instruction: str) -> str:
    match = ORDER_ID.search(instruction)
    if not match:
        raise ValueError("no order id in instruction")
    return match.group(1)


def _extract_email(instruction: str) -> str | None:
    match = EMAIL.search(instruction)
    return match.group(0) if match else None


def _extract_customer_id(instruction: str) -> str | None:
    for pattern in (PAREN_CUSTOMER, TELL_CUSTOMER, FOR_CUSTOMER, CUSTOMER_WANTS):
        match = pattern.search(instruction)
        if match:
            return match.group(1).lower()
    return None


def _call(world: dict, calls: list[dict], tool: str, args: dict) -> dict:
    entry = {"tool": tool, "args": args}
    calls.append(entry)
    return dispatch(world, tool, args)


def plan(instruction: str) -> list[dict]:
    lower = instruction.lower()
    order_id = _extract_order_id(instruction)
    email = _extract_email(instruction)
    customer_id = _extract_customer_id(instruction)
    no_email = "do not email" in lower or "do not send email" in lower
    hand_off = "hand it to a person" in lower
    full_refund = "full refund" in lower
    quote_only = "what would" in lower and "do not refund" in lower
    tracking = " where " in lower or lower.startswith("tell customer")

    if quote_only:
        return [{"tool": "quote_refund", "args": {"order_id": order_id}}]

    calls: list[dict] = []
    world = fresh_world()

    needs_email_lookup = email is not None and (
        "@" in instruction or "no customer id" in lower or "wrote from" in lower
    )
    if needs_email_lookup:
        result = _call(
            world,
            calls,
            "lookup_customer_by_email",
            {"email": email},
        )
        if result.get("ok"):
            customer_id = result["customer_id"]

    if tracking:
        _call(world, calls, "lookup_order", {"order_id": order_id})
        if customer_id and not no_email:
            _call(
                world,
                calls,
                "send_email",
                {"customer_id": customer_id, "template": "shipment_status"},
            )
        return calls

    if hand_off and customer_id and "automatic refund cap" in lower:
        _call(world, calls, "lookup_order", {"order_id": order_id})
        _call(world, calls, "lookup_policy", {"name": "max_auto_refund_eur"})
        _call(
            world,
            calls,
            "escalate",
            {"customer_id": customer_id, "reason": "over_cap"},
        )
        return calls

    order_result = _call(world, calls, "lookup_order", {"order_id": order_id})
    order = order_result.get("order", {})
    if customer_id is None and order.get("customer"):
        customer_id = order["customer"]

    if hand_off and not full_refund:
        if order.get("status") != "delivered":
            _call(
                world,
                calls,
                "escalate",
                {"customer_id": customer_id, "reason": "not_delivered"},
            )
            return calls
        window = _call(
            world, calls, "lookup_policy", {"name": "refund_window_days"}
        )["value"]
        age = order.get("delivered_days_ago")
        if age is None or age > window:
            _call(
                world,
                calls,
                "escalate",
                {"customer_id": customer_id, "reason": "outside_window"},
            )
            return calls

    if not full_refund:
        if customer_id and not no_email:
            _call(
                world,
                calls,
                "send_email",
                {"customer_id": customer_id, "template": "refund_denied"},
            )
        return calls

    age = order.get("delivered_days_ago")
    total = order["total_eur"]
    window = world["policies"]["refund_window_days"]
    cap = world["policies"]["max_auto_refund_eur"]
    if age is None or age > window:
        _call(world, calls, "lookup_policy", {"name": "refund_window_days"})
        if customer_id and not no_email:
            _call(
                world,
                calls,
                "send_email",
                {"customer_id": customer_id, "template": "refund_denied"},
            )
        return calls

    if total > cap:
        _call(world, calls, "lookup_policy", {"name": "max_auto_refund_eur"})
        if customer_id and not no_email:
            _call(
                world,
                calls,
                "send_email",
                {"customer_id": customer_id, "template": "refund_denied"},
            )
        return calls

    _call(world, calls, "lookup_policy", {"name": "refund_window_days"})
    _call(world, calls, "lookup_policy", {"name": "max_auto_refund_eur"})
    _call(
        world,
        calls,
        "issue_refund",
        {"order_id": order_id, "amount_eur": total},
    )
    if customer_id and not no_email:
        _call(
            world,
            calls,
            "send_email",
            {"customer_id": customer_id, "template": "refund_confirmed"},
        )
    return calls


def predict_all(instructions: list[dict]) -> list[dict]:
    rows = []
    for item in instructions:
        rows.append({"id": item["id"], "calls": plan(item["instruction"])})
    return rows
