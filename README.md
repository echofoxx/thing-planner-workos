# Thing Planner WorkOS v0.1.0

A ClickUp-inspired, independently branded WorkOS prototype for project management, dashboards, forms, AI assistance, automations, planning, docs, whiteboards, goals, and team collaboration.

This release is a front-end foundation build. It is designed to demonstrate the product shell, user experience, navigation model, task views, actionable dashboards, form intake, and AI-agent direction before adding the production API and database layer.

## What is included

- Purple global app rail with Home, Spaces, Planner, AI, Teams, Docs, Dashboards, Whiteboards, Forms, Clips, Goals, More, Invite, and Upgrade.
- Secondary contextual sidebar for each module.
- Workspace top bar with workspace selector, global search, AI chat shortcut, utility icons, and user avatar.
- Home inbox with Primary, Other, Later, and Cleared tabs.
- Spaces hierarchy with Team Space, Projects, Project 1, Project 2, and Project Notes.
- Task management with List, Board, Calendar, Gantt, and Table views.
- Task drawer with assignee, status, due date, priority, description, comments, AI actions, and risk check.
- Kanban board with drag-and-drop status updates.
- Dashboard template page and live Executive PMO Dashboard.
- Workable dashboard reports where status can be changed directly from dashboard cards.
- Forms template page and Project Intake form builder that creates tasks.
- AI assistant page with project summary, task generation, status report, and task location simulations.
- Planner page with AI daily schedule concept.
- Automations library with project, scheduling, engineering, and agency templates.
- Docs/wiki cards, goals/OKR cards, teams hub, clips placeholder, and whiteboard canvas.
- LocalStorage persistence and reset demo data action.
- Dockerfile and docker-compose.yml for local hosting.

## Run locally without Docker

Open `index.html` in a browser.

For a local server:

```bash
python3 -m http.server 8098
```

Then open:

```text
http://localhost:8098
```

## Run with Docker

```bash
docker compose up --build -d
```

Then open:

```text
http://localhost:8098
```

## Reset demo data

In the app, go to:

```text
More → Reset demo data
```

Or clear browser local storage for the site.

## Important product note

This build intentionally avoids using ClickUp logos, brand assets, protected artwork, or exact product identity. The layout and interaction pattern are inspired by the screenshots and the requested plan, but the product should continue as an independently branded WorkOS.

## Recommended next release

v0.2 should add a backend API, database persistence, authentication, and real CRUD endpoints while preserving this front-end shell.
