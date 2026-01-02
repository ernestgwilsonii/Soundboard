import pytest
from app import create_app, socketio
from flask_socketio import SocketIOTestClient

def test_broadcast_board_update_event():
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    
    # Create two clients
    client1 = socketio.test_client(flask_app)
    client2 = socketio.test_client(flask_app)
    
    # Both join room 1
    client1.emit('join_board', {'board_id': 1})
    client2.emit('join_board', {'board_id': 1})
    
    # Clear received events
    client1.get_received()
    client2.get_received()
    
    # Simulate a backend broadcast (normally called from routes)
    from app.socket_events import broadcast_board_update
    with flask_app.app_context():
        broadcast_board_update(1, 'sound_uploaded', {'name': 'Test Sound'})
    
    # Check if client 1 and 2 received the update
    received1 = client1.get_received()
    received2 = client2.get_received()
    
    assert any(e['name'] == 'board_updated' for e in received1)
    assert any(e['name'] == 'board_updated' for e in received2)
    
    client1.disconnect()
    client2.disconnect()

def test_slot_locking_events():
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    
    client1 = socketio.test_client(flask_app)
    client2 = socketio.test_client(flask_app)
    assert client1.is_connected()
    assert client2.is_connected()
    
    client1.emit('join_board', {'board_id': 1})
    client2.emit('join_board', {'board_id': 1})
    
    client1.get_received()
    client2.get_received()
    
    # Client 1 requests a lock
    client1.emit('request_lock', {'board_id': 1, 'sound_id': 456})
    
    # Client 2 should receive slot_locked
    received2 = client2.get_received()
    assert any(e['name'] == 'slot_locked' and e['args'][0]['sound_id'] == 456 for e in received2)
    
    # Client 1 should NOT receive slot_locked (include_self=False)
    received1 = client1.get_received()
    assert not any(e['name'] == 'slot_locked' for e in received1)
    
    # Client 1 releases lock
    client1.emit('release_lock', {'board_id': 1, 'sound_id': 456})
    received2 = client2.get_received()
    assert any(e['name'] == 'slot_released' and e['args'][0]['sound_id'] == 456 for e in received2)
    
    client1.disconnect()
    client2.disconnect()
