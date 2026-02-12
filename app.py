from flask import Flask, send_from_directory, render_template, request, jsonify
from pathlib import Path
from datetime import timedelta


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    # defaults
    app.config.from_mapping(
        SECRET_KEY="dev",
        DB_PATH=str(Path(app.instance_path) / "wifi_portal.db"),
        SESSION_DURATION=300,  # default grant per bottle (seconds)
        MOCK_SENSOR=True,
    )

    if test_config:
        app.config.update(test_config)

    # ensure instance folder exists
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # late imports to avoid circular
    from db import init_db
    from services.access_control import AccessController
    from services.session import SessionManager
    from routes.portal import bp as portal_bp
    from routes.rating import bp as rating_bp

    # init db
    init_db(app)

    # services
    app.extensions["access_controller"] = AccessController(app)
    app.extensions["session_manager"] = SessionManager(app, app.extensions["access_controller"])

    # register blueprints
    app.register_blueprint(portal_bp)
    app.register_blueprint(rating_bp)

    @app.route("/")
    def index():
        session_id = request.args.get('session')
        session_data = None
        
        if session_id:
            # Fetch session from database or in-memory store
            session_data = app.extensions["session_manager"].get_session(session_id)
            
        return render_template('index.html', session=session_data)

    @app.route("/favicon.ico")
    def favicon():
        # serve favicon from project root (where app.py resides) if present
        return send_from_directory(app.root_path, "favicon.ico")

    @app.route('/rate.html')
    def rate():
        return render_template('rate.html')

    @app.route('/api/session/<session_id>')
    def get_session_api(session_id):
        session = app.extensions["session_manager"].get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'session_id': session.id,
            'expires_at': int(session.expires_at.timestamp()),
            'bottles': session.bottles,
            'minutes': session.minutes
        })

    @app.route('/api/bottle', methods=['POST'])
    def register_bottle():
        data = request.get_json()
        session_id = data.get('session_id')
        
        session = app.extensions["session_manager"].get_session(session_id)
        if not session:
            return jsonify({'error': 'Invalid session'}), 400
        
        # Add 2 minutes per bottle
        session.bottles += 1
        session.minutes += 2
        session.expires_at += timedelta(minutes=2)
        app.extensions["session_manager"].save_session(session)
        
        return jsonify({
            'minutes_added': 2,
            'session': {
                'session_id': session.id,
                'expires_at': int(session.expires_at.timestamp()),
                'bottles': session.bottles,
                'minutes': session.minutes
            }
        })

    return app


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="E-Connect captive portal (dev)")
    parser.add_argument("--mock", dest="mock", action="store_true", help="Enable mock sensor")
    parser.add_argument("--no-mock", dest="mock", action="store_false", help="Disable mock sensor")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Do not execute system commands (iptables)")
    parser.add_argument("--apply", dest="dry_run", action="store_false", help="Apply system commands for real (careful)")
    parser.add_argument("--session-duration", dest="session_duration", type=int, default=None, help="Default session duration (seconds)")
    parser.set_defaults(mock=True, dry_run=True)
    args = parser.parse_args()

    cfg = {
        "MOCK_SENSOR": bool(args.mock),
        "DRY_RUN": bool(args.dry_run),
    }
    if args.session_duration:
        cfg["SESSION_DURATION"] = int(args.session_duration)

    # enable iptables by default on non-windows platforms when not dry-run
    import platform
    if platform.system().lower() != "windows" and not args.dry_run:
        cfg["USE_IPTABLES"] = True

    app = create_app(test_config=cfg)
    app.run(debug=True, host="0.0.0.0")
