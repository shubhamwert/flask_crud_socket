from flask_socketio import SocketIO, emit,join_room, disconnect
socketio = SocketIO( cors_allowed_origins="*",path="/notification/ws")  # Enable CORS for testing

@socketio.on('connect')
def on_connect(auth):
    print("Client connected")
    emit('message', {'data': 'Connected to WebSocket'})
    user_id = auth.get("user_id") if auth else None
    if not user_id:
        print("User ID missing in auth")
        disconnect()
        return

    join_room(f"user_{user_id}")
    print(f"User {user_id} connected and joined room user_{user_id}")
    emit('message', {'data': f'Connected to room user_{user_id}'})
@socketio.on('disconnect')
def on_disconnect():
    print("Client disconnected")


def notify_users(permitted_users,issue):
    for users in permitted_users:
        socketio.emit('new_issue', issue, room=f"user_{users.user_id}")
