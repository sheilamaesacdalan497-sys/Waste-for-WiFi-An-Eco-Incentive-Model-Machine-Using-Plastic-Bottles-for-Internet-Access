# Architecture

## Backend (Flask)

- `app.py`
  - Creates the Flask app and config (`DB_PATH`, `SESSION_DURATION`, `MOCK_SENSOR`, cleanup intervals).
  - Registers blueprints (`routes/portal.py`, `routes/rating.py`).
  - Exposes API routes for:
    - Sessions: create, lookup, activate, expire, unlock, get by id.
    - Bottle events: `/api/bottle`.
    - Rating: `/rating` (page), `/api/rating`, `/api/rating/status`.
    - Captive portal detection: `/generate_204`, `/connecttest.txt`, `/hotspot-detect.html`.

- `db.py`
  - SQLite helpers and schema.
  - Tables:
    - `sessions` – one row per device session:
      - `awaiting_insertion` → user has not started inserting bottles yet.
      - `inserting` → insertion lock held, insert modal open.
      - `active` → Wi‑Fi session running.
      - `expired` → finished sessions.
    - `ratings` – one rating per session (q1–q10 + optional comment).
    - `system_logs` – events such as `session_started`, `session_expired`, `bottle_inserted`, `rating_submitted`.
  - Key helpers:
    - `create_session`, `get_session`, `update_session`, `update_session_status`.
    - `acquire_insertion_lock` for machine‑wide “inserting” lock.
    - Cleanup: `expire_stale_awaiting_sessions`, `expire_finished_active_sessions`.
    - Ratings: `submit_rating`, `get_rating_by_session`, rating stats, session stats.

- `services/`
  - `network.py` – resolves client IP → MAC on Linux (dnsmasq leases, `/proc/net/arp`, `arp`).
  - `sensor.py` – `MockSensor` for development; real GPIO sensor to be implemented.
  - `session.py` – legacy session manager for integration with a firewall/access controller.

## Frontend (HTML + JS)

- Templates:
  - `templates/index.html`
    - Main landing page: connection indicator, timer card (`#timer-card`, `#timer`), buttons:
      - **Insert Plastic Bottle**
      - **How It Works?**
      - **Rate EcoNeT**
    - Includes:
      - `partials/modal_insert_bottle.html` – insert modal + 3‑minute bottle timer.
      - `partials/modal_howitworks.html`.
      - `partials/mock_dev_panel.html` (DEV TOOLS; can be removed in production).
    - Toast container: `<div id="toasts" class="toasts"></div>`.

  - `templates/rate.html`
    - Stand‑alone rating form (q1–q10 + optional comment).
    - Uses `/static/js/rating.js`.

- JavaScript:

  - `static/js/dom.js`
    - `$()` helper, `openModal`, `closeModal`.
    - `showToast(message, type, duration)` and `window.showToast`.

  - `static/js/timer.js`
    - Bottle timer:
      - `startBottleTimer(sessionId, initialBottles, initialSeconds)`.
      - `registerBottle()`, updates “time earned” and enables **Done**.
    - Session countdown:
      - `startSessionCountdown(sessionData, onExpire)`:
        - Renders main timer.
        - Toasts at 60s and 30s remaining.
        - Calls `onExpire()` at 0, hides timer, reloads page.
      - `stopSessionCountdown()`.

  - `static/js/api/sessionApi.js`
    - HTTP helpers:
      - `lookupSession()` → `/api/session/lookup`.
      - `acquireInsertionLock()` → `/api/session/create`.
      - `unlockInsertion()` → `/api/session/unlock`.
      - Bottle posting and session activate helpers.

  - `static/js/sessionManager.js`
    - Central client‑side session state:
      - `currentSessionId`, `pendingSessionData`, bottle counters, flags for pre/post insertion state.
      - Persists `session_id` in `localStorage`.
    - Coordinates:
      - Entering `inserting` state and acquiring lock.
      - Committing bottles and activating/extending sessions.
      - Starting/stopping countdown via `timer.js`.
      - Handling already‑active sessions without resetting remaining time.

  - `static/js/init.js`
    - Bootstraps the main page:
      - Calls `lookupSession()` and `loadSession()`.
      - Wires buttons:
        - **Insert Plastic Bottle** → open modal & start bottle timer.
        - Modal **X** → cancel insertion and unlock.
        - **Rate EcoNeT** → navigate to `/rating`.
        - **How It Works?** → open info modal.
      - Checks `/api/rating/status` to disable **Rate** if session already rated.
      - Shows “Thanks for your feedback!” toast based on `localStorage` flag.
      - Optionally initializes dev panel.

  - `static/js/rating.js`
    - Handles rating form:
      - Validates q1–q10 (required, 1–5).
      - Comment optional.
      - Submits to `/api/rating`.
      - Sets `localStorage['rating_submitted']` on success, then redirects to `/`.

  - `static/js/mockDevPanel.js` (development only)
    - Floating dev panel to simulate bottles and sessions.
    - Should be disabled/removed in production.