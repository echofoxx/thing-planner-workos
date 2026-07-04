# Thing Planner WorkOS v0.3.0 Auth Foundation

v0.3.0 adds a demo authentication layer. This is suitable for local prototype/demo use and sets up the route structure for production authentication.

## Demo account

```text
Email: echofoxx@gmail.com
Password: thingplanner
```

## Endpoints

```text
POST /api/auth/login
POST /api/auth/demo-login
GET  /api/auth/me
```

## Token model

The backend issues a lightweight signed bearer token using HMAC SHA-256. It is intentionally simple for local use. For production, replace this with one of the following:

- Auth.js / NextAuth
- Keycloak
- Cognito
- Supabase Auth
- SAML/OIDC enterprise SSO

## Production hardening still needed

- Enforce permissions on all write endpoints.
- Replace local HMAC token with standards-based JWT/OIDC.
- Add refresh tokens or session rotation.
- Add password reset and invite flow.
- Add audit events for permission changes.
- Add rate limiting and lockouts.
- Add SSO/SCIM for enterprise mode.
