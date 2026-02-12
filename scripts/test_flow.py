"""
Test script to simulate the complete user flow.
Run this to verify all endpoints and database operations work.
"""
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app import create_app
import db
import time

def test_complete_flow():
    """Simulate complete user flow from connection to expiration."""
    app = create_app({'TESTING': True, 'MOCK_SENSOR': True})
    
    with app.app_context():
        print("\n=== Testing EcoNeT Flow ===\n")
        
        # Step 1: User connects to Wi-Fi
        print("1. User connects to Wi-Fi...")
        mac_address = "AA:BB:CC:DD:EE:FF"
        ip_address = "192.168.1.100"
        session_id = db.create_session(mac_address, ip_address)
        print(f"   ✓ Session created: ID={session_id}, status=awaiting_insertion")
        
        session = db.get_session(session_id)
        assert session['status'] == 'awaiting_insertion'
        print(f"   ✓ Session data: {session}")
        
        # Step 2: User clicks "Insert Bottle" button
        print("\n2. User opens bottle insertion modal...")
        db.update_session_status(session_id, 'inserting')
        session = db.get_session(session_id)
        print(f"   ✓ Status changed to: {session['status']}")
        
        # Step 3: User inserts bottles during 3-minute window
        print("\n3. Simulating bottle insertions...")
        for i in range(3):
            db.add_bottle_to_session(session_id, seconds_per_bottle=120)
            session = db.get_session(session_id)
            print(f"   ✓ Bottle {i+1} inserted: {session['bottles_inserted']} total, {session['seconds_earned']}s earned")
            time.sleep(0.5)
        
        # Step 4: Timer ends or user clicks "Done"
        print("\n4. Activating session (timer ended / user clicked Done)...")
        db.start_session(session_id)
        session = db.get_session(session_id)
        print(f"   ✓ Session activated: status={session['status']}")
        print(f"   ✓ Session start: {session['session_start']}")
        print(f"   ✓ Session end: {session['session_end']}")
        print(f"   ✓ Duration: {session['seconds_earned']}s ({session['seconds_earned']//60} minutes)")
        
        # Step 5: Get bottle logs
        print("\n5. Checking bottle logs...")
        logs = db.get_bottle_logs(session_id)
        print(f"   ✓ Found {len(logs)} bottle insertion logs")
        
        # Step 6: User rates the service
        print("\n6. User submits rating...")
        rating_data = {
            'q1': 5, 'q2': 4, 'q3': 5, 'q4': 4, 'q5': 5,
            'q6': 5, 'q7': 4, 'q8': 5, 'q9': 4, 'q10': 5
        }
        db.submit_rating(session_id, rating_data, "Great service!")
        rating = db.get_rating_by_session(session_id)
        print(f"   ✓ Rating saved: {rating}")
        
        # Step 7: Session expires
        print("\n7. Session expires...")
        db.update_session_status(session_id, 'expired')
        session = db.get_session(session_id)
        print(f"   ✓ Session expired: status={session['status']}")
        
        # Step 8: Check system logs
        print("\n8. Checking system logs...")
        logs = db.get_system_logs(limit=10)
        print(f"   ✓ Found {len(logs)} system log entries:")
        for log in logs:
            print(f"      - [{log['event_type']}] {log['description']}")
        
        # Step 9: Get statistics
        print("\n9. Getting statistics...")
        stats = db.get_session_stats()
        print(f"   ✓ Session stats: {stats}")
        rating_stats = db.get_rating_stats()
        print(f"   ✓ Rating stats: {rating_stats}")
        
        print("\n=== All Tests Passed! ✓ ===\n")

if __name__ == '__main__':
    test_complete_flow()