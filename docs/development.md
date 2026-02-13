# Development vs Production

## Dev Tools

- `templates/partials/mock_dev_panel.html` + `static/js/mockDevPanel.js`:
  - Floating “🧪 DEV TOOLS” panel.
  - Buttons:
    - “Simulate Bottle Insert”.
    - “Start New Session”.
    - “Stop Current Session”.
- Enabled by including the partial in `index.html`:

  ```jinja2
  {% include 'partials/mock_dev_panel.html' %}
  ```

- To disable in production:
  - Comment or remove that include from `index.html`.
  - Optionally remove the `initMockDevPanel` import/call from `static/js/init.js`.

## Mock vs Real Sensor

- Config flag: `app.config["MOCK_SENSOR"]`.
- Current state:
  - Mock sensor is used implicitly via dev tools and `/api/bottle` tests.
  - Real hardware sensor is not yet wired in.

### TODO for Real Hardware

- Implement a `GPIOSensor` or similar in `services/sensor.py`:

  ```python
  class GPIOSensor(SensorInterface):
      def __init__(self, app, pin):
          super().__init__(app)
          # Configure GPIO pin
      def start(self):
          # Register edge/callback for bottle detection
  ```

- On detection:
  - Determine the current session for the device:
    - Either call `/api/bottle` from a local helper, or
    - Use `db.get_session_for_device` and update DB directly.
- Wire into `create_app`:
  - If `MOCK_SENSOR` is `False`, instantiate and `start()` the real sensor at app startup.

## Access Control Integration

- `services/session.py` sketches a design for connecting session status to network access.
- Intended behaviour:
  - When a session becomes `active`, grant network access (via iptables, firewall, or VLAN).
  - When a session is expired or revoked, remove that access.
- TODO:
  - Implement an `AccessController` that:
    - Adds/removes iptables rules for client IP/MAC.
  - Hook it into session lifecycle events:
    - On `activate`/`expire`, update firewall state accordingly.

## Production Hardening Checklist

- Disable dev panel and debug logs.
- Serve app behind HTTPS or on a trusted LAN.
- Restrict admin endpoints, logs, and monitoring.
- Regularly rotate and backup the SQLite database.
- Add basic monitoring/alerts for:
  - Bottle count anomalies.
  - Session creation/expiry errors.
  - Rating submission failures.