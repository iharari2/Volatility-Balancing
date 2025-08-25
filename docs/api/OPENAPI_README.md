# API Governance
- All external HTTP APIs must be captured in **OpenAPI 3.0** under `/docs/api/openapi.yaml`.
- Changes require a docs PR; CI validates schema.

## Local Preview
- Use Redocly or Swagger‑UI to render.

## Versioning
- SemVer on endpoints; breaking changes require major bump and deprecation notes in PRD.
