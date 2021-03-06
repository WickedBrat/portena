from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
import base64
import json

import socket
import threading


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


s = socket.socket()
port = 12345
s.bind(('', port))
s.listen(5)


def wait_for_clients(s):
    while True:
        c, addr = s.accept()
        print 'Got connection from', addr
        partial_content = ''
        while True:
            data = c.recv(2049)
            if not data:
                break
            partial_content += data

        data = partial_content.decode()
        # data = c.recv(40048).decode()
        if data:
            print(data, data.find("'requesting_gid'"))
            if data.find('"requesting_gid":') > 0:
                print('requesting_gid')
                socketio.emit("userRequestedToCall", data)
            if data.find('"acceptance":') > 0:
                print('acceptanceAck')
                socketio.emit('acceptanceAck', data)
            if data.find('"audioUrl":') > 0:
                print('recievedAudio')
                socketio.emit('recievedAudio', data)
            else:
                print('Message Reply')
                socketio.emit('reply', data)
        c.close()


listen = threading.Thread(target=wait_for_clients, args=(s,))
listen.start()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/users')
def users():
    return render_template('users.html')


@app.route('/users/<GID>')
def chat(GID):
    return render_template('chat.html', user_gid=GID)


@socketio.on('message')
def handle_message(message):
    print(message)
    c = socket.socket()
    c.connect(('192.168.43.243', 12345))
    c.send(json.dumps(message).encode())
    c.close()


@socketio.on('requestToCall')
def handle_call_req(gid_info):
    c = socket.socket()
    c.connect(('192.168.43.243', 12345))
    c.send(json.dumps(gid_info).encode())
    c.close()


@socketio.on('callActionFromUser')
def handle_call_req(acceptance):
    c = socket.socket()
    c.connect(('192.168.43.243', 12345))
    c.send(json.dumps(acceptance).encode())
    c.close()


@socketio.on('audioEmitted')
def handle_call_req(audioEmitted):
    c = socket.socket()
    c.connect(('192.168.43.243', 12345))
    audioEmitted['callAudio']['audioBlob'] = base64.b64encode(audioEmitted['callAudio']['audioBlob'])
    content = json.dumps(audioEmitted)
    c.send(content.encode())
    # c.send(json.dumps(audioEmitted).encode())
    c.close()


if __name__ == '__main__':
    socketio.run(app)
