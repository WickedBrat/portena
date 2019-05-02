from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
import base64
import socket
import threading

s = socket.socket()
s.bind(('', 8000))
s.listen(10)

def accept_connections_from_other_node(s):
    while True:
        c, addr = s.accept()      
        print 'Got connection from', addr
        data = s.recv()
        print(data)

listening_thread = threading.Thread(target = accept_connections_from_other_node, args = (s,))
listening_thread.start()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

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
    s.send(str(message).encode())
    s.close()
    # print('received message: ', base64.b64encode((message['data']['audioBlob'])))
    # socketio.emit('message', str(
    #     {
    #         u'data': {
    #             u'audioUrl': message['data']['audioUrl'], 
    #             u'audioBlob': base64.b64encode(message['data']['audioBlob'])
    #         },
    #         u'yo': u'yoyo'
    #     }
    # ))

if __name__ == '__main__':
    socketio.run(app)
