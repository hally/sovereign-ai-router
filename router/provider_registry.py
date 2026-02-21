from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ProviderTarget:
    provider: str
    region: str
    model: str


def load_provider_registry(yaml_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalized registry:
      registry[provider][region] = {"endpoint": str, "models": [str, ...]}
    """
    if "providers" not in yaml_data or not isinstance(yaml_data["providers"], list):
        raise ValueError("Invalid providers.yml: missing 'providers' list")

    registry: Dict[str, Dict[str, Dict[str, Any]]] = {}

    for p in yaml_data["providers"]:
        name = p.get("name")
        regions = p.get("regions", [])
        if not name or not isinstance(regions, list):
            raise ValueError("Invalid providers.yml: provider entries must include name and regions[]")

        registry[name] = {}
        for r in regions:
            rname = r.get("name")
            endpoint = r.get("endpoint")
            models = r.get("models", [])
            if not rname or not isinstance(models, list) or not endpoint:
                raise ValueError(f"Invalid providers.yml: region must include name, endpoint, models[] (provider={name})")

            registry[name][rname] = {"endpoint": endpoint, "models": models}

    return registry


def target_is_supported(registry: Dict[str, Any], target: ProviderTarget) -> bool:
    return (
        target.provider in registry
        and target.region in registry[target.provider]
        and target.model in registry[target.provider][target.region]["models"]
    )


def resolve_endpoint(registry: Dict[str, Any], target: ProviderTarget) -> Optional[str]:
    try:
        return registry[target.provider][target.region]["endpoint"]
    except Exception:
        return None