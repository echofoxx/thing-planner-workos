# Thing Planner WorkOS v0.9.1 Release Notes

## Theme

UI Cleanup + Connected Functional Shell.

## Changes

- Cleaned the primary navigation rail to the requested nine modules: Home, Spaces, Planner, AI, Teams, Docs, Dashboard, Whiteboard, and Forms.
- Removed the default promo banner and helper/feedback popups that distracted from the application.
- Removed Invite, Upgrade, Clips, Goals, and More from the primary rail while keeping related functions accessible through working modules or settings.
- Rebuilt the top bar with compact API/auth connection pills.
- Added connection bootstrap retries while Docker services start.
- Added API discovery for `/api`, `localhost:8099/api`, and `127.0.0.1:8099/api`.
- Demo authentication auto-runs after a successful API health check.
- Quick Add Task now creates a real task and opens the task drawer instead of using a browser prompt.
- Gantt baseline capture creates a timestamped baseline without a browser prompt.
- Sidebar creation buttons now perform useful prototype actions where possible.

## Validation

- Frontend JavaScript syntax validated with `node --check`.
- Backend Python syntax validated with `py_compile`.

## Notes

If the top bar still shows Local mode, the frontend is running but the FastAPI service is not reachable yet. Start the Docker Compose stack and click the API connection pill to reconnect.
