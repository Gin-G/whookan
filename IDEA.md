---
status: active
progress: 65
---

# WhoKan

<!--
IdeaBRD parses this file. It is the source of truth for this idea's tile:
the app re-reads it on every open and commits its own edits back here, so
the shape below matters more than it looks. Anything the parser
(backend/app/ideafile.py) can't read is dropped silently.

  frontmatter  status: one of idea, active, paused, done. progress: 0-100.
               Any other key is ignored.
  # heading    The idea title (first H1).
  prose        Everything outside the Todos section becomes the tile's
               notes, shown on the board — so keep it short. Documentation
               written here is published, not filed away.
  ## Todos     That heading exactly (or "## To-Dos"); "## ToDo", "## TODO"
               and "## Tasks" do not match and the whole list is lost.
               Inside it, only "- [ ] open" / "- [x] done" lines survive:
               sub-headings and blank-line grouping are discarded, and a
               wrapped item is cut at the line break, so keep each to-do on
               one line. The next "## " heading ends the list.
  (#12)        A to-do ending in an issue reference is backed by that issue
               in this repo. The issue wins: its title becomes the to-do's
               text and its open/closed state the checkbox, both here and on
               the board. Ticking the box in the app closes the issue.

Working in this repo? This file is the to-do list — use it rather than
starting a parallel one. Tick items off as you finish them, add new ones as
you find them, and keep status/progress honest: a TODO.md, a plan in a chat
window or a checklist in a commit message is invisible to everyone reading
the board. For work worth assigning, discussing, or writing up at length,
open a real issue and append its "(#12)" to the line — the item is then
tracked by number instead of text, and the issue holds the detail this file
has no room for (prose here is published to the board, not filed away).

To-dos without an issue are matched to the board by exact text, so rewording
one replaces it rather than editing it in place — expect a checked item to
come back unchecked if you reword it. Issue-backed to-dos are matched by
number instead, so keep the "(#12)" and reword freely; drop the reference and
the item becomes an ordinary to-do again (the issue itself is left alone).

HTML comments are stripped on read, so this block never reaches the board.
-->

Internal skill-discovery platform: people list what they know, search colleagues by skill, ask for help, and build a reputation from help actually given. Each skill carries a forum for durable Q&A and a live chat room for the quick stuff.

Live at https://whokan.nickknows.net — FastAPI + Postgres (CNPG), vanilla JS + Alpine frontend, Helm/ArgoCD GitOps on Kubernetes. Registration, skills, search, help requests, forum and chat all work end to end, covered by 141 backend tests plus post-deploy smoke tests against the live URL.

The gaps are the back half of the product loop and production hardening: the help/reputation flow can be gamed by anyone confirming their own help, and a temporary debug handler is still leaking stack traces in production.

## Todos

- [ ] P0: Remove the debug exception handler in main.py that returns stack traces to callers
- [ ] P0: Require the requester, not the helper, to confirm help before helped_count increments
- [ ] P0: Set helper_id and use the in_progress status when someone offers help
- [ ] P0: Reject help confirmation on requests already completed or cancelled
- [ ] P0: Give the requester a way to cancel an open help request
- [ ] P0: Route help requests to the colleague they were addressed to, or drop the per-person UI
- [ ] P0: Set BACKEND_CORS_ORIGINS in the backend Deployment — prod falls back to a placeholder
- [ ] P0: Delete the fake SECRET_KEY env var from the frontend Deployment
- [ ] P1: Delete the legacy index.html SPA and fix the /index.html vs /login.html redirect split
- [ ] P1: Move rank computation server-side out of assets/js/app.js
- [ ] P1: Add edit, delete and moderation for forum posts, comments and chat messages
- [ ] P1: Add in-app notifications for help requests, replies and mentions
- [ ] P1: Normalise skill names so Node.js, NodeJS and node js are one skill rather than three
- [ ] P1: Add skill endorsements so claimed skills can be corroborated
- [ ] P1: Paginate GET /users/ and GET /help-requests
- [ ] P1: Add password reset, email verification and account deletion
- [ ] P1: Build an admin surface for users, duplicate skills and content moderation
- [ ] P1: Decide whether WhoKan is single or multi tenant — nothing scopes data by company
- [ ] P2: Add readiness and liveness probes to the backend and frontend Deployments
- [ ] P2: Add resource requests and limits to the backend and frontend Deployments
- [ ] P2: Configure CNPG backups — one instance today with no backup stanza
- [ ] P2: Build images with COPY from the build context instead of git clone inside the Dockerfile
- [ ] P2: Drop --reload from the production backend uvicorn command
- [ ] P2: Add rate limiting to registration, login, help requests, forum posts and chat
- [ ] P2: Run the backend multi-replica to exercise the Redis pub/sub path, or drop that path
- [ ] P2: Replace print() with structured logging and add metrics
- [ ] P2: Measure and gate test coverage in CI — pytest-cov is installed but never invoked
- [ ] P2: Add frontend behavioural tests beyond node --check
- [ ] P2: Pin floating deps and de-duplicate python-multipart and passlib in requirements.txt
- [ ] P2: Migrate off pydantic v1 — BaseSettings, @validator and orm_mode are all v1-only
- [ ] P2: Decide whether helped_count should decay so early users do not hold a permanent lead
- [ ] P2: Check actual chat usage before investing further in WebSockets and Redis
- [ ] P3: Rename README to README.md and rewrite it — it documents an in-memory DB and old layout
- [ ] P3: Delete the stray root alembic.ini — the real one is whokan/backend/alembic.ini
- [ ] P3: Untrack the 1.8 MB generated_users.json and generated_user_profiles.json fixtures
- [ ] P3: Add .env.example documenting the required variables
- [ ] P3: Add a LICENSE file — the README claims MIT and none is present
- [ ] P3: Widen the backend workflow path filter to cover whohelm/ changes
