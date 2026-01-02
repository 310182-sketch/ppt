Release v2.0

Changes:
- Add Canva OAuth endpoints (`/api/canva/oauth/start`, `/api/canva/oauth/callback`) and local token store for development.
- Enhance proxy (`/api/proxy/fetch`) to support `Authorization: Bearer <token>` via `CANVA_ACCESS_TOKEN` env or saved OAuth tokens.
- Add `backend/docs/canva_integration.md` with OAuth guide and examples.

Notes:
- This release adds OAuth integration scaffolding. For production, do NOT store secrets in repo; use Secret Manager and implement refresh-token flow.
