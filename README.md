# Sovereign AI Router

A policy-driven multi-cloud control plane that routes AI inference requests to an approved provider, region, and model based on jurisdiction and data classification.

This project demonstrates centralized compliance enforcement, policy-as-code, and explainable routing decisions across simulated AWS and Azure providers.

---

## Problem Statement

Organizations operating across multiple jurisdictions face increasing regulatory complexity:

- AI models are distributed across cloud providers
- Data residency laws differ by region
- Developers may unintentionally violate compliance constraints
- There is often no centralized enforcement or audit trail

Compliance enforcement should not be delegated to individual application teams.

---

## Solution Overview

The Sovereign AI Router centralizes routing decisions and enforces policy before AI inference is executed.Provider targets are abstracted via a registry; policies select an approved provider/region/model and the router resolves a provider-specific endpoint without hardcoding compliance in application code.

The system evaluates:

- Jurisdiction (e.g., EU, UAE)
- Data classification (e.g., PII, GOV)
- Approved provider regions
- Allowed models

It returns a deterministic decision including:

- `ALLOW` or `DENY`
- Selected provider / region / model
- Reason codes
- Full evaluation trace

---

## Architecture

**Control Plane**
- AWS Lambda (routing engine)
- API Gateway (HTTP interface)
- Terraform (Infrastructure as Code)

**Policy Layer**
- `policies/policy.yml` — Compliance rules (policy-as-code)
- `providers/providers.yml` — Multi-cloud provider registry

---

## Repository Structure

```text
sovereign-ai-router/
├── router/                 # Routing engine + Lambda handler
├── policies/policy.yml     # Compliance rules
├── providers/providers.yml # Provider capability registry
├── terraform/              # AWS infrastructure
├── requirements.txt
└── README.md
```
## Example Request

bash
curl -X POST https://<api-id>.execute-api.<region>.amazonaws.com/route \
  -H "content-type: application/json" \
  -d "{\"jurisdiction\":\"EU\",\"data_classification\":\"PII\"}"

## Example Response (Allowed)
{
  "decision": "ALLOW",
  "selected": {
    "provider": "azure",
    "region": "westeurope",
    "model": "sim-gpt"
  },
  "reason_codes": [
    "EU_RESIDENCY_REQUIRED",
    "PII_RESTRICTED"
  ],
  "trace": [...]
}

## Example Response (Denied)
{
  "decision": "DENY",
  "reason_codes": ["NO_MATCHING_POLICY"]
}

## Policy Example
rules:
  - name: EU_PII_must_stay_in_EU
    when:
      jurisdiction: EU
      data_classification: PII
    allow:
      - provider: azure
        region: westeurope
        model: sim-gpt
      - provider: aws
        region: eu-central-1
        model: sim-claude
    reason_codes:
      - EU_RESIDENCY_REQUIRED
      - PII_RESTRICTED
   
## Deployment
- terraform init
- terraform apply

## Destroy when not in use:
- terraform destroy
