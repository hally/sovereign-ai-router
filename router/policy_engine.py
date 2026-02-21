from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .provider_registry import ProviderTarget, target_is_supported


@dataclass(frozen=True)
class Decision:
    decision: str  # "ALLOW" | "DENY"
    selected: Optional[ProviderTarget]
    reason_codes: List[str]
    trace: List[Dict[str, Any]]


def evaluate_policy(
    request: Dict[str, Any],
    policy_doc: Dict[str, Any],
    provider_registry: Dict[str, Dict[str, List[str]]],
) -> Decision:
    """
    Evaluates request against policy.yml rules.
    Request must include:
      jurisdiction: str
      data_classification: str
    """
    trace: List[Dict[str, Any]] = []

    jurisdiction = request.get("jurisdiction")
    classification = request.get("data_classification")

    if not jurisdiction or not classification:
        return Decision(
            decision="DENY",
            selected=None,
            reason_codes=["INVALID_REQUEST"],
            trace=[{"step": "validate_request", "ok": False, "missing": ["jurisdiction/data_classification"]}],
        )

    rules = policy_doc.get("rules", [])
    default = policy_doc.get("default", {"decision": "DENY", "reason_codes": ["NO_MATCHING_POLICY"]})

    trace.append({"step": "validate_request", "ok": True, "jurisdiction": jurisdiction, "data_classification": classification})
    trace.append({"step": "rules_count", "count": len(rules)})

    # Find first matching rule (simple + deterministic)
    for rule in rules:
        rname = rule.get("name", "<unnamed>")
        when = rule.get("when", {})
        allow = rule.get("allow", [])
        reason_codes = rule.get("reason_codes", [])

        match = (when.get("jurisdiction") == jurisdiction) and (when.get("data_classification") == classification)

        trace.append({"step": "evaluate_rule", "rule": rname, "match": match})

        if not match:
            continue

        # Pick the first allowed target that is supported by registry
        for candidate in allow:
            target = ProviderTarget(
                provider=candidate.get("provider"),
                region=candidate.get("region"),
                model=candidate.get("model"),
            )
            supported = target_is_supported(provider_registry, target)
            trace.append(
                {
                    "step": "check_candidate",
                    "rule": rname,
                    "candidate": {"provider": target.provider, "region": target.region, "model": target.model},
                    "supported": supported,
                }
            )
            if supported:
                return Decision(
                    decision="ALLOW",
                    selected=target,
                    reason_codes=list(reason_codes),
                    trace=trace,
                )

        # Rule matched but no candidate supported
        return Decision(
            decision="DENY",
            selected=None,
            reason_codes=["NO_SUPPORTED_TARGET"],
            trace=trace,
        )

    # No rule matched
    return Decision(
        decision=default.get("decision", "DENY"),
        selected=None,
        reason_codes=list(default.get("reason_codes", ["NO_MATCHING_POLICY"])),
        trace=trace,
    )