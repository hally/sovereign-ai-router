from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml

from .policy_engine import evaluate_policy
from .provider_registry import load_provider_registry


REPO_ROOT = Path(__file__).resolve().parents[1]
PROVIDERS_PATH = REPO_ROOT / "providers" / "providers.yml"
POLICY_PATH = REPO_ROOT / "policies" / "policy.yml"


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def route_request(request: Dict[str, Any]) -> Dict[str, Any]:
    providers_doc = _load_yaml(PROVIDERS_PATH)
    policy_doc = _load_yaml(POLICY_PATH)

    registry = load_provider_registry(providers_doc)
    decision = evaluate_policy(request, policy_doc, registry)

    response: Dict[str, Any] = {
        "decision": decision.decision,
        "reason_codes": decision.reason_codes,
        "trace": decision.trace,
    }

    if decision.selected:
        endpoint = None
        try:
            from .provider_registry import resolve_endpoint
            endpoint = resolve_endpoint(registry, decision.selected)
        except Exception:
            endpoint = None

        response["selected"] = {
            "provider": decision.selected.provider,
            "region": decision.selected.region,
            "model": decision.selected.model,
            "endpoint": endpoint,
        }

    return response


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    API Gateway proxy integration expects:
      - event["body"] as JSON string (often)
    """
    body = event.get("body")
    if isinstance(body, str):
        try:
            request = json.loads(body)
        except json.JSONDecodeError:
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON body"})}
    elif isinstance(body, dict):
        request = body
    else:
        # allow direct invoke with event as request
        request = event

    result = route_request(request)

    return {
        "statusCode": 200 if result.get("decision") == "ALLOW" else 403,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(result),
    }