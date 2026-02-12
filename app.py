from flask import Flask, send_from_directory, render_template, request, jsonify
from pathlib import Path
from datetime import datetime, timezone
import db
import time

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DB_PATH=str(Path(app.instance_path) / "wifi_portal.db"),
        SESSION_DURATION=300,
        MOCK_SENSOR=True,
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_db(app)

    # TODO: On Pi, initialize AccessController and SessionManager
    # Sample implementation:
    """
    from services.access_control import AccessController
    from services.session import SessionManager
    
    # Initialize access controller for iptables management
    access_controller = AccessController(app)
    app.extensions["access_controller"] = access_controller
    
    # Initialize session manager for monitoring active sessions
    session_manager = SessionManager(app, access_controller)
    app.extensions["session_manager"] = session_manager
    
    # Start background thread to check for expired sessions
    session_manager.start_monitoring()
    """
    
    from routes.portal import bp as portal_bp
    from routes.rating import bp as rating_bp

    app.register_blueprint(portal_bp)
    app.register_blueprint(rating_bp)

    @app.route("/")
    def index():
        session_id = request.args.get('session')
        session_data = None
        
        if session_id:
            session_data = db.get_session(int(session_id))
            
        return render_template('index.html', session=session_data)

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(app.root_path, "favicon.ico")

    @app.route('/rate.html')
    def rate():
        session_id = request.args.get('session')
        return render_template('rate.html', session_id=session_id)

    # Get session data
    @app.route('/api/session/<int:session_id>')
    def get_session_api(session_id):
        session = db.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify(session)

    # Register a bottle insertion
    @app.route('/api/bottle', methods=['POST'])
    def register_bottle():
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'No session_id provided'}), 400
        
        session = db.get_session(session_id)
        if not session:
            return jsonify({'error': 'Invalid session'}), 400
        
        if session['status'] not in ('inserting', 'awaiting_insertion'):
            return jsonify({'error': 'Session not accepting bottles'}), 400
        
        # Add bottle (2 minutes = 120 seconds)
        db.add_bottle_to_session(session_id, seconds_per_bottle=120)
        
        # TODO: On Pi, trigger physical feedback (LED, sound, etc.)
        # Sample implementation:
        """
        import RPi.GPIO as GPIO
        
        # Light up LED to confirm bottle detection
        LED_PIN = 18
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(LED_PIN, GPIO.OUT)
        
        # Blink LED 3 times
        for _ in range(3):
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(0.2)
        
        # Or play a sound
        import pygame
        pygame.mixer.init()
        success_sound = pygame.mixer.Sound('/path/to/success.wav')
        success_sound.play()
        """
        
        updated_session = db.get_session(session_id)
        
        return jsonify({
            'success': True,
            'bottles_inserted': updated_session['bottles_inserted'],
            'seconds_earned': updated_session['seconds_earned'],
            'minutes_earned': updated_session['seconds_earned'] // 60
        })

    # Activate session (start Wi-Fi access)
    @app.route('/api/session/<int:session_id>/activate', methods=['POST'])
    def activate_session(session_id):
        session = db.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if session['bottles_inserted'] == 0:
            return jsonify({'error': 'No bottles inserted'}), 400
        
        # Start the session
        db.start_session(session_id)
        
        # TODO: On Pi, grant iptables access for this MAC address
        # Sample implementation:
        """
        mac_address = session['mac_address']
        access_controller = app.extensions.get("access_controller")
        
        if access_controller:
            # Grant internet access via iptables
            access_controller.grant_access(mac_address)
            print(f"✓ Granted access to MAC: {mac_address}")
        """
        
        updated_session = db.get_session(session_id)
        
        return jsonify({
            'success': True,
            'session': updated_session
        })

    # Update session status
    @app.route('/api/session/<int:session_id>/status', methods=['POST'])
    def update_status(session_id):
        data = request.get_json()
        status = data.get('status')
        
        if status not in db.ALL_SESSION_STATUSES:
            return jsonify({'error': 'Invalid status'}), 400
        
        db.update_session_status(session_id, status)
        
        return jsonify({'success': True})

    # Expire session
    @app.route('/api/session/<int:session_id>/expire', methods=['POST'])
    def expire_session(session_id):
        session = db.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        db.update_session_status(session_id, db.STATUS_EXPIRED)
        
        # TODO: On Pi, revoke iptables access
        # Sample implementation:
        """
        mac_address = session['mac_address']
        access_controller = app.extensions.get("access_controller")
        
        if access_controller:
            # Revoke internet access via iptables
            access_controller.revoke_access(mac_address)
            print(f"✓ Revoked access from MAC: {mac_address}")
        """
        
        return jsonify({'success': True})

    # Create session endpoint for dev tools
    @app.route('/api/session/create', methods=['POST'])
    def create_session_api():
        data = request.get_json()
        mac_address = data.get('mac_address', request.remote_addr)
        ip_address = data.get('ip_address', request.remote_addr)
        
        # Create new session
        session_id = db.create_session(mac_address, ip_address)
        session = db.get_session(session_id)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': session['status'],
            'mac_address': mac_address,
            'ip_address': ip_address
        })

    # TODO: On Pi, add captive portal detection endpoint
    # This is where the OS detects the portal and redirects the user
    @app.route('/generate_204')
    @app.route('/connecttest.txt')
    @app.route('/hotspot-detect.html')
    def captive_portal_detect():
        """Captive portal detection endpoints for various OS."""
        
        # TODO: Extract MAC from request or ARP table
        # Sample implementation:
        """
        import subprocess
        
        # Get client IP
        client_ip = request.remote_addr
        
        # Look up MAC address from ARP table
        try:
            arp_output = subprocess.check_output(['arp', '-n', client_ip]).decode()
            # Parse ARP output to extract MAC (format varies by OS)
            # Example line: "192.168.1.100   ether   aa:bb:cc:dd:ee:ff   C   wlan0"
            for line in arp_output.split('\n'):
                if client_ip in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        mac_address = parts[2]  # MAC is typically 3rd column
                        break
            else:
                mac_address = client_ip  # Fallback to IP if MAC not found
        except Exception as e:
            print(f"Failed to get MAC from ARP: {e}")
            mac_address = client_ip  # Fallback
        """
        
        # For now, use IP as placeholder
        mac_address = request.remote_addr
        
        # Check if session exists for this MAC
        session = db.get_session_by_mac(mac_address)
        
        if session and session['status'] == 'active':
            # Already has active session, return success
            return '', 204
        
        if not session:
            # Create new session
            session_id = db.create_session(mac_address, request.remote_addr)
        else:
            session_id = session['id']
        
        # Redirect to portal with session ID
        return f'<html><body><script>window.location.href="/?session={session_id}";</script></body></html>'

    return app


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="EcoNeT captive portal")
    parser.add_argument("--mock", dest="mock", action="store_true", help="Enable mock sensor")
    parser.add_argument("--no-mock", dest="mock", action="store_false", help="Disable mock sensor")
    parser.set_defaults(mock=True)
    args = parser.parse_args()

    cfg = {"MOCK_SENSOR": bool(args.mock)}

    app = create_app(test_config=cfg)
    
    # Register db teardown
    app.teardown_appcontext(db.close_db)
    
    app.run(debug=True, host="0.0.0.0")
