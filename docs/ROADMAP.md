# Thing Planner WorkOS Roadmap
> v0.3.0 update: the backend now uses normalized relational tables with demo authentication and /api/state compatibility serialization. See `DATABASE_SCHEMA_v0.3.0.md` and `AUTH_v0.3.0.md`.


## v0.1 — Workspace Shell and Interactive Prototype

Status: Built in this package.

- App shell
- Purple global rail
- Context sidebars
- Home and Inbox
- Spaces hierarchy
- Task List, Board, Calendar, Gantt, and Table views
- Task drawer
- Dashboard templates
- Actionable dashboard reports
- Forms templates and form builder
- AI assistant
- Planner
- Automations library
- Docs, Goals, Teams, Whiteboards placeholders
- LocalStorage persistence
- Docker packaging

## v0.3 — Production Data Layer

- FastAPI or NestJS backend
- PostgreSQL database
- Real workspace, space, folder, list, and task CRUD
- User/auth model
- Role model
- REST API endpoints
- OpenAPI specification
- Seed database
- Docker Compose with API + web + Postgres

## v0.3 — Task Management Hardening

- Nested subtasks
- Task relationships
- Dependencies
- Checklists
- Attachments
- Comments and mentions
- Activity log
- Bulk actions
- Saved views
- View filters, grouping, and sorting
- Custom task types
- Custom statuses per space/list

## v0.4 — Custom Fields and Forms

- Custom field schema
- Field value storage
- Form builder persistence
- Public form links
- Conditional logic
- Form-to-task mapping
- AI form classification
- Submission analytics

## v0.5 — Dashboards and Reports

- Dashboard builder persistence
- Card layout engine
- KPI cards
- Editable report tables
- Time tracking reports
- Portfolio rollups
- Drill-down filters
- AI dashboard summaries

## v0.6 — Automations

- Event bus
- Trigger / condition / action registry
- Automation builder
- Run logs
- Manual button automations
- Templates for project, scheduling, engineering, and CRM workflows
- Webhook action

## v0.7 — Planner and Scheduling

- Day/week/month planner
- Recurring tasks
- Time blocking
- Calendar integration framework
- AI daily plan
- AI rescheduling
- Workload conflict detection

## v0.8 — Gantt and Portfolio Planning

- Real timeline engine
- Dependency editor
- Critical path
- Baselines
- Delay propagation
- Milestones
- Portfolio timeline
- Export PDF/PNG

## v0.9 — Docs, Wiki, and Knowledge

- Rich text editor
- Pages and subpages
- Task/doc links
- Version history
- Decision records
- Protected docs
- AI doc summary/action extraction

## v1.0 — Production Demo

- Auth
- Database
- API
- Real-time updates
- Dashboard persistence
- Docker production profile
- README, screenshots, install guide
- Seed templates for PM, CRM, ITSM, Agile, Agencies, Campaigns, and Executive reporting
