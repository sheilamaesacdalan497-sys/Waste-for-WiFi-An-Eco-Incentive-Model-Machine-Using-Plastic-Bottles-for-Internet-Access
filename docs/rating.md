# Rating Flow and Security

## Goals

- Only the device that owns a session can submit a rating.
- No `session_id` is exposed in the public rating URL.
- One rating per session.
- q1–q10 required (1–5); comment optional.

## Endpoints

### GET `/rating`

- Uses `routes.portal.get_device_identifier`:
  - Determines device MAC (or cookie‑based identifier) and IP.
- Calls `db.get_session_for_device(..., statuses=(STATUS_ACTIVE, STATUS_EXPIRED))`.
- Requires `bottles_inserted > 0`.
- If no eligible session:
  - Redirects to `/`.
- If eligible:
  - Renders `templates/rate.html` (no `session_id` in the URL).

### POST `/api/rating`

- Identifies the session by device, not by URL:
  - `get_session_for_device(..., statuses=ALL_SESSION_STATUSES)`.
- Enforces one rating per session:
  - Uses `db.get_rating_by_session(session_id)`.
- Validates request JSON:
  - `q1`..`q10` must be present, each an integer in `[1, 5]`.
  - `comment` is optional; leading/trailing whitespace trimmed.
- Persists rating with:
  - `db.submit_rating(session_id, answers, comment)`.
- Returns JSON:
  - On success: `{"success": true}`.
  - On error: `{"error": "...", ...}` with appropriate HTTP status.

### GET `/api/rating/status`

- For the current device:
  - Determines session with `get_session_for_device`.
  - Checks any existing rating via `get_rating_by_session`.
- Returns:
  - `{ "has_session": bool, "has_rating": bool, "session_id": <id or null> }`.
- Used on the main page to disable the **Rate EcoNeT** button if already rated.

## Frontend Behaviour

### Main Page (`index.html` + `init.js`)

- **Rate EcoNeT** button:
  - Navigates to `/rating`.
- On load:
  - `initRatingButtonState()` calls `/api/rating/status`:
    - If `has_rating` is true:
      - Disables the Rate button (HTML `disabled` + CSS class).
- After rating submission:
  - Rating page sets `localStorage['rating_submitted'] = '1'` and redirects to `/`.
  - `init.js` reads this flag and shows a single “Thanks for your feedback!” success toast, then clears the flag.

### Rating Page (`rate.html` + `rating.js`)

- `rating.js`:
  - Validates q1–q10:
    - All must have selected values (1–5).
  - Reads optional comment from the textarea.
  - Submits JSON to `/api/rating`.
  - On validation failure:
    - Shows a toast asking the user to complete all questions.
  - On API error:
    - Shows an error toast based on API’s error message.
  - On success:
    - Sets `localStorage['rating_submitted'] = '1'`.
    - Redirects back to `/` where the success toast is shown.

## Database

- Table `ratings`:
  - Columns for `session_id`, `q1`..`q10`, `comment`, `submitted_at`.
  - Foreign key to `sessions(id)`.
  - One rating per session enforced by application logic (`get_rating_by_session` check).