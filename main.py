from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "rifjsdjk"
socketio = SocketIO(app)

rooms = {}

# Generate a unique room code
def generate_unique_code(length):
    while True:
        code = "".join(random.choice(ascii_uppercase) for _ in range(length))
        if code not in rooms:
            return code

# Home route
@app.route("/", methods=["GET", "POST"])
def home():
    session.clear()

    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = 'join' in request.form
        create = 'create' in request.form

        if not name:
            return render_template("home.html", error="Please enter a name.")

        if join and not code:
            return render_template("home.html", error="Please enter a room code.", name=name)

        room = code
        if create:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", name=name)

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")

# Room route
@app.route("/room")
def room():
    room = session.get("room")
    name = session.get("name")

    if not room or not name or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

# SocketIO message event
@socketio.on("message")
def handle_message(data):
    room = session.get("room")
    name = session.get("name")

    if room not in rooms:
        return

    content = {"name": name, "message": data["data"]}
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{name} said: {data['data']}")

# SocketIO connect event
@socketio.on("connect")
def handle_connect(auth):
    room = session.get("room")
    name = session.get("name")

    if not room or not name or room not in rooms:
        return

    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

# SocketIO disconnect event
@socketio.on("disconnect")
def handle_disconnect():
    room = session.get("room")
    name = session.get("name")

    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left room {room}")

# Run the app
if __name__ == "__main__":
    socketio.run(app, debug=True)
