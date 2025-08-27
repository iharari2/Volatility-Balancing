# ADR-0001: Monorepo Structure
Date: 2025-08-26
Status: Accepted

## Context
We had overlapping folder taxonomies which caused duplication and confusion.

## Decision
Unify docs under `/docs/*`; place server code under `/backend/app/*`; keep `/frontend`, `/infra`, `/scripts`. OpenAPI in `/docs/api`.

## Consequences
- Pros: discoverability, simpler onboarding, CI paths consistent
- Cons: one-time churn (git mv), PRs temporarily noisier
- Risks: stale imports if not updated carefully

## Alternatives
- Keep both structures and "live with it" — rejected due to ongoing confusion.
- Split into multi-repos — premature for our size and velocity.

## References
- README layout section
