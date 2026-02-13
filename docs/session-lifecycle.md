# Session Lifecycle

## 1. Portal Entry / Captive Detection

Devices hit standard captive‑portal URLs:

- `/generate_204`
- `/connecttest.txt`
- `/hotspot-detect.html`

Flow:

1. Resolve client IP → MAC via `services.network.get_mac_for_ip`.
2. `db.get_session_for_device`:
   - If an existing session in (`awaiting_insertion`, `inserting`, `active`) is found → reuse it.
   - Otherwise, create a new `awaiting_insertion` session.
3. Return a minimal page redirecting the browser to `/?session=<id>` (handled by `index.html`).

## 2. Index Page Boot

- `init.js` calls `lookupSession()`:
  - `/api/session/lookup` returns or creates the current session for this device.
- `sessionManager.loadSession()`:
  - Saves session data to `pendingSessionData` and `currentSessionId`.
  - If `status='active'` and `session_end` is in the future:
    - Starts `startSessionCountdown(sessionData, onExpire)`.
  - Updates button states (e.g., enable/disable Insert/Rate).

## 3. Starting Bottle Insertion

When user clicks **Insert Plastic Bottle**:

1. `sessionManager.createSession()` calls `/api/session/create`:
   - Uses `db.acquire_insertion_lock`:
     - Guarantees at most one `status='inserting'` (machine‑wide).
     - If this device already has `active` or `awaiting_insertion` session:
       - That row is transitioned to `inserting`.
     - If another session is already `inserting`:
       - Returns HTTP 409 (machine busy).
2. On success:
   - Insert modal opens.
   - `startBottleTimer(sessionId, initialBottles, initialSeconds)` starts a 3‑minute insertion timer.

## 4. Recording Bottles

Bottle events come from:

- Real sensor (future GPIO integration), or
- Mock dev panel via `/api/bottle`.

Server:

- `/api/bottle`:
  - Valid only for sessions with status `inserting` or `active`.
  - Updates:
    - `bottles_inserted += count`.
    - `seconds_earned += count * 120`.
  - Extends `session_end`:
    - If session is active or was active before returning to inserting, extend from existing `session_end`.
    - For purely new `inserting` sessions, `session_end` remains `None` until activation.

Client:

- `sessionManager` updates:
  - Bottle count in the modal.
  - “time earned” label.
  - Enables **Done** button when at least 1 bottle has been seen.

## 5. Committing Bottles / Starting Wi‑Fi Session

Triggered by:

- Bottle timer end, or
- User clicking **Done** in insert modal.

`bottles-committed` handler:

1. Computes bottle **delta** (local vs server) to avoid double counting.
2. Posts missing bottles via `/api/bottle`.
3. Two flows:

### 5.1 New or Inactive Session

- The session was not active before inserting.
- Call `/api/session/<id>/activate`:
  - Sets `status='active'`, `session_start`, `session_end`.
- Client:
  - Starts `startSessionCountdown(...)`.
  - Marks user as connected and updates buttons.

### 5.2 Already Active Session

- The session had a running timer before opening the insert modal.
- Avoid resetting start/end:

1. Post bottle delta to `/api/bottle`.
2. Call `/api/session/unlock`:
   - If bottles exist → sets status back to `active`.
3. Fetch updated session via `/api/session/<id>`.
4. Call `startSessionCountdown` with the updated `session_end`:
   - Timer continues from remaining time plus new earned seconds (no reset).

## 6. Countdown and Expiry

`startSessionCountdown(sessionData, onExpire)`:

- Shows the timer card, sets text in `#timer`.
- Every second:
  - Decrements remaining seconds.
  - Updates `#timer` in “X min. YY sec.” format.
  - At 60s remaining:
    - Calls `showToast('You have 1 minute left on your Wi‑Fi session. Please finalize your use.', 'info')`.
  - At 30s remaining:
    - Calls `showToast('Only 30 seconds left on your Wi‑Fi session.', 'warning')`.
  - At 0:
    - Calls `onExpire()`:
      - Backend: `/api/session/<id>/expire` marks session as `STATUS_EXPIRED`.
      - Frontend: clears `currentSessionId`, updates buttons, marks disconnected.
    - Hides the timer card.
    - Reloads the page.

Background cleanup (in a thread started from `create_app`):

- `expire_stale_awaiting_sessions` – cleans old `awaiting_insertion` sessions.
- `expire_finished_active_sessions` – marks over‑time `active` sessions as `expired`.