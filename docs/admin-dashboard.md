# Admin Dashboard

This document describes the EcoNeT admin interface: URLs, security, layout, and data flows.

---

## Overview

The admin dashboard is a protected web UI for:

- Monitoring **active / ongoing sessions**
- Tracking **bottles today** and **total bottles**
- Viewing **aggregate rating means**
- Browsing **individual user reviews**

It is intended for operators of the EcoNeT machine, not end users.

---

## Routes

### HTML Views

- `GET /admin/login`
  - Renders `templates/admin_login.html`
  - Simple login form for admin username + password
- `POST /admin/login`
  - Validates credentials (see **Authentication**)
  - On success: sets admin session and redirects to `/admin`
  - On failure: re-renders login with an error
- `GET /admin`
  - Renders `templates/admin.html`
  - Requires valid admin session
- `GET /admin/logout`
  - Clears admin session and redirects back to `/admin/login` or main portal

### JSON APIs

Used by `static/js/admin.js`:

- `GET /api/admin/metrics`
  - Returns:
    - `active_sessions` (int)
    - `bottles_today` (int)
    - `total_bottles` (int)
    - `total_reviews` (int)
    - `rating_means` (object: `q1..q10`, `composite`)
    - `ongoing_sessions` (list of sessions with `id`, `status`, `bottles_inserted`, `session_end`, etc.)
- `GET /api/admin/ratings?from=YYYY-MM-DD&to=YYYY-MM-DD`
  - Returns list of rating rows:
    - `session_id`
    - `submitted_at` (UNIX ts)
    - `q1..q10` (scores)
    - `comment`

### WebSocket

- `WS /ws/admin`
  - Pushes live updates of:
    - KPI metrics
    - Rating means
    - Ongoing sessions
  - Frontend falls back to HTTP polling if WebSocket is unavailable.

---

## Authentication

Admin credentials are configured via environment variables:

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

Key pieces:

- `app.py`
  - `_check_admin_credentials(username, password)` compares against env vars
  - `require_admin` decorator guards /admin and admin APIs
- `admin_login.html`
  - Standard username/password form posting to `/admin/login`

Sessions (Flask `session`) are used so that subsequent admin requests do not need HTTP basic auth.

---

## UI Layout

### Login Page (`admin_login.html`)

- Centered card using `.app-root .card` + `.admin-login-form`
- Fields:
  - Username
  - Password
- Styles (in `admin.css`):
  - `.admin-login-form` controls max-width and vertical spacing
  - `.admin-login-field` groups label + input
  - Inputs are enlarged for easier typing
- On error, an inline `.admin-login-error` message is shown.

### Dashboard (`admin.html`)

Main layout:

- Wrapper: `.admin-root`
- Header: `.admin-header` with logo and title
- Content: `.admin-main` with sections:
  1. **KPI Cards** (`.admin-kpis`)
     - Active Sessions
     - Bottles Today
     - Total Bottles
     - Total Reviews
  2. **Ongoing Sessions** vs **Ratings Summary** (`.admin-grid`)
     - Grid ratio: `2fr : 1fr` (Ongoing Sessions wider)
     - Ongoing Sessions (left)
       - Filter: status dropdown
       - Table: `#table-ongoing`
       - Pagination: `#ongoing-pagination`
       - Cells centered (`.panel-ongoing .admin-table th/td`)
     - Ratings Summary (right)
       - Tiles for `Q1..Q10`
       - “Composite Mean” tile
  3. **User Reviews**
     - Date filter (from / to)
     - Table: `.admin-table--ratings` / `#table-ratings`
       - All cells centered
       - Last column is comment
     - Pagination: `#ratings-pagination`

Footer:

- `.site-footer` with a styled `Log out` button (`.admin-logout`)

---

## Tables & Pagination

Defined in `static/js/admin.js`.

### Ongoing Sessions Table

- Page size: `ONGOING_PAGE_SIZE = 10`
- Data source:
  - From `/api/admin/metrics` → `payload.ongoing_sessions`
  - If empty or error: dummy data from `makeDummyOngoingSessions()` for development
- Filtering:
  - Status dropdown filters `latestOngoing` into `ongoingFiltered`
- Pagination:
  - `renderOngoingPage()` slices `ongoingFiltered`
  - `renderOngoingPagination()` renders prev / page numbers / next (max `MAX_PAGES = 10`)

### User Reviews Table

- Page size: `RATINGS_PAGE_SIZE = 10`
- Data source:
  - From `/api/admin/ratings`
  - If none/error: dummy ratings via `makeDummyRatings()` for development
- Filters:
  - Optional `from` / `to` date
- Pagination:
  - Similar pattern to ongoing sessions (`renderRatingsPage`, `renderRatingsPagination`)

---

## Live Updates Flow

1. On load (`DOMContentLoaded`):
   - `initWebSocket()` connects to `/ws/admin`
   - `loadRatings({})` fetches initial ratings
2. WebSocket messages:
   - Parsed JSON payload with:
     - KPIs
     - Rating means
     - Ongoing sessions
   - UI updated via:
     - `updateKpis`
     - `updateRatingsSummary`
     - `renderOngoingTable`
3. Fallback:
   - On WS close/error: `startHttpPolling()` calls `fetchMetricsOnce()` every 5s

---

## Styling Notes

- Global gradient from `static/css/style.css`:
  - `body` uses a fixed, full-height gradient (`background-attachment: fixed; background-size: cover;`)
- Admin-specific styles in `static/css/admin.css`:
  - `.admin-grid` sets 2:1 column ratio
  - Tables use `font-size: 1rem` and extra spacing between header and rows
  - Admin logout button is styled via `.site-footer .admin-logout`

---

## Development Tips

- If debugging pagination or layout:
  - Ensure dummy data helpers (`makeDummyOngoingSessions`, `makeDummyRatings`) are present and being used when APIs return empty data.
- For styling updates:
  - Prefer editing `admin.css` (dashboard + login) rather than `style.css` (shared portal styles).
- For new metrics or filters:
  - Extend `/api/admin/metrics` and `/api/admin/ratings`
  - Update `admin.js` to consume the new fields
  - Add UI elements into `admin.html` and style them in `admin.css`