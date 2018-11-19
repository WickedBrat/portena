#!/usr/bin/python

import socket
import time
from network import LoRa
import _thread
import gc

message_list = {'xx-yy': ['zz']}
client_username = {}

header = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Portena</title>
        <style>
            body {
                background-color: grey;
            }
            * {
                color: white;
            }
        </style>
    </head>
    <body>
    <center><h1>Portena</h1>
"""

introductory_text = header + """
        <form method="post">
            <input type="text" name="username">
            <button type="submit">Submit Username</button>
        </form>
        </center>
    </body>
    </html>
    """


def generate_dynamic_user_list():
    dynamic_user_list = ''
    for key, user in client_username:
        dynamic_user_list += '<a href="/users/%s">%s</a><br>' % (user, user)
    return dynamic_user_list


user_page_response_content = header + """
        <h2>This is users page</h2>
        <a href="/users"><h3>View of online users</h3></a>
        %s
        </center>
    </body>
    </html>
    """ % generate_dynamic_user_list()


def generate_from_to_user_message_list(from_user, to_user):
    message = {}
    message['string'] = ''
    message['length'] = 0
    compare = []
    compare.append(from_user + '-' + to_user)
    compare.append(to_user + '-' + from_user)
    if (from_user + '-' + to_user) in message_list.keys():
        message['length'] = len(message_list[from_user + '-' + to_user])
        for messages in message_list[from_user + '-' + to_user]:
            message['string'] += to_user + '-> ' + messages + '<br>'
    else:
        message['length'] = len(message_list[to_user + '-' + from_user])
        for messages in message_list[to_user + '-' + from_user]:
            message['string'] += to_user + '-> ' + messages + '<br>'
    return message


def get_user_message_page(from_user, to_user, message):
    user_message_page = header + """
        <form method="post">
            <p>%s</p>
            <input type="text" from_user=""
            <input type="text" name="message">
            <button type="submit">Submit</button>
        </form>
        </center>
        <script>
            setInterval(function () {
                var xhr = new XMLHttpRequest();
                xhr.open('POST', '192.168.4.1', true)
                xhr.setRequestHeader('Refresh', 'yes');
                xhr.setRequestHeader('MessageLength', '%d');
                xhr.send()
                xhr.onreadystatechange = function() {
                    if (this.readyState == 4 && this.status == 200) {
                        location.replace('192.168.4.1');
                    }
                };
            }, 5000);
        </script>
    </body>
    </html>
    """ % (message['string'], message['length'])
    return user_message_page


def get_normalised_string(string):
    words = string.split('+')
    normalised_string = ' '.join(words)
    return normalised_string


class Server:
    """ Class describing a simple HTTP server objects."""

    def __init__(self, port=808):
        """ Constructor """
        self.host = ''
        self.port = port
        self.www_dir = 'www'
        self.username = ''

    def listen_at_all_times(self, conn):
        """This function recieves data at all times."""
        while True:
            data = conn.recv(300)
            if data:
                print(data)
                message_list[data.split('*')[0]] = data.split('*')[1]
            time.sleep(0.5)

    def activate_server(self):
        """ Attempts to aquire the socket and launch the server """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print("Launching HTTP server on ", self.host, ":", self.port)
            self.socket.bind((self.host, self.port))

        except Exception as e:
            print("Warning: Could not aquite port:",
                  self.port, " : ERROR: ", e, "\n")
            print("I will try a higher port")
            user_port = self.port
            self.port = 8080

            try:
                print("Launching HTTP server on ", self.host, ":", self.port)
                self.socket.bind((self.host, self.port))

            except Exception as e:
                print("ERROR: Failed to acquire sockets for ports ",
                      user_port, " and 8080. ")
                print("Try running the Server in a privileged user mode.")
                self.shutdown()
                import sys
                sys.exit(1)

        print("Server successfully acquired the socket with port:", self.port)
        print("Press Ctrl+C to shut down the server and exit.")
        self._wait_for_connections()

    def shutdown(self):
        """ Shut down the server """
        try:
            print("Shutting down the server")
            s.socket.shutdown(socket.SHUT_RDWR)

        except Exception as e:
            print(
                "Warning: could not shut down the socket. Maybe it was already closed?", e)

    def _gen_headers(self,  code):
        """ Generates HTTP response Headers. Ommits the first line! """

        # determine response code
        h = ''
        if (code == 200):
            h = 'HTTP/1.1 200 OK\n'
        elif(code == 404):
            h = 'HTTP/1.1 404 Not Found\n'

        # write further headers
        #  current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        h += 'Date: ' + 'today' + '\n'
        h += 'Server: Simple-Python-HTTP-Server\n'
        # signal that the conection wil be closed after complting the request
        h += 'Connection: close\n\n'

        return h

    def send_to_frontend(self, conn, response_content):
        response_headers = self._gen_headers(200)
        server_response = response_headers.encode()  # return headers for GET and HEAD
        server_response += response_content  # return additional conten for GET only
        print('++++++++++++++++**/*//*', gc.mem_free())
        try:
            conn.send(server_response)
            conn.close()
        except Exception as e:
            print(e)

    # def update_again(self, conn, message, username):
    #     message_string_operations('add', message, self.username)
    #     self.send_to_frontend(conn, )

    def _wait_for_connections(self):
        """ Main loop awaiting connections """

        lora = LoRa(mode=LoRa.LORA)
        s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        s.setblocking(False)
        _thread.start_new_thread(self.listen_at_all_times, (s,))

        while True:
            gc.collect()
            print("\n -- Awaiting new connection/request from clients -- ")
            self.socket.listen(3)
            conn, addr = self.socket.accept()
            print('\n -- Recieved connection from ',
                  addr[0], ' with port ', addr[1])

            data = conn.recv(1024)
            string = bytes.decode(data)
            options = {}

            split_string = string.split(' ')
            request_method = split_string[0]

            print("Method: ", request_method)
            print("Request body: ", string)

            for option in string.split('\n'):
                options[option[:option.find(':')]
                        ] = option[option.find(':')+2:]

            print('+'*100 + '\n', string)

            if request_method == 'GET':
                # Code for when user connects to the WiFi for the first time. i.e. Introductory page.
                if (options['User-Agent'] not in client_username.keys()) or client_username[options['User-Agent']] == '':
                    client_username[options['User-Agent']] = ''
                    self.send_to_frontend(conn, introductory_text)
                    continue

                routes = split_string[1].split('/')

                # Code for when user wants the page for the list of users. i.e. Users page.
                if routes[1] == 'users':
                    if split_string[1][6:7] == '/':
                        to_user = routes[2]
                        from_user = client_username[options['User-Agent']]
                        if ((from_user + '-' + to_user) not in message_list) or ((to_user + '-' + from_user) not in message_list):
                            message_list[from_user + '-' + to_user] = []
                            self.send_to_frontend(
                                conn, get_user_message_page(client_username[options['User-Agent']],
                                                            to_user, {'string': '', 'length': 0}))
                            continue
                        self.send_to_frontend(
                            conn, get_user_message_page(client_username[options['User-Agent']],
                                                        to_user, generate_from_to_user_message_list(
                                                            from_user, to_user)
                                                        ))
                        continue
                    self.send_to_frontend(conn, header + """
                            <h2>This is users page</h2>
                            <a href="/users"><h3>View of online users</h3></a>
                            %s
                            </center>
                        </body>
                        </html>
                        """ % generate_dynamic_user_list())
                    continue

                # Code for when user sees the page. i.e. Message page.

            if request_method == 'POST':
                if 'username' in split_string[-1][8:]:
                    client_username[options['User-Agent']
                                    ] = split_string[-1][51:]
                    self.send_to_frontend(conn, user_page_response_content)
                    continue

                if 'message' in split_string[-1]:
                    from_user = client_username[options['User-Agent']]
                    to_user = split_string[1].split('/')[2]
                    if (from_user + '-' + to_user) in message_list.keys():
                        s.send(from_user + '-' + to_user + '*' +
                               from_user + ': ' + split_string[-1][50:])
                        message_list[from_user + '-' +
                                     to_user].append(split_string[-1][50:])
                    else:
                        s.send(to_user + '-' + from_user + '*' +
                               from_user + ': ' + split_string[-1][50:])
                        message_list[to_user + '-' +
                                     from_user].append(split_string[-1][50:])
                    self.send_to_frontend(
                        conn, get_user_message_page(client_username[options['User-Agent']],
                                                    to_user, generate_from_to_user_message_list(
                                                        from_user, to_user)
                                                    ))
                    continue

            conn.close()

            # recieved_post_data = split_string[-1][split_string[-1].find(
            #     'message')+8:]

            # if (request_method == 'POST' and ('username' in split_string[-1])):
            #     self.username = split_string[-1][split_string[-1].find(
            #         'username')+9:]
            #     self.send_to_frontend(conn)
            #     continue

            # if (request_method == 'POST' and split_string[8][:1] == 'y'):
            #     print(len(message_list), '+'*100, int(split_string[7][:1]))
            #     if len(message_list) > int(split_string[7][:1]):
            #         self.send_to_frontend(conn)
            #     continue

            # if (request_method == 'POST'):
            #     s.send(self.username + ': ' + recieved_post_data)
            #     self.update_again(conn, recieved_post_data, self.username)

            # #  text_message.append(recieved_post_data)
            # #  self.update_again(conn, recieved_post_data)
            # # if string[0:3] == 'GET':

            # if (request_method == 'GET') | (request_method == 'HEAD'):
            #     # file_requested = string[4:]
            #    #  # split on space "GET /file.html" -into-> ('GET','file.html',...)
            #    #  file_requested = split_string
            #    #  file_requested = file_requested[1] # get 2nd element

            #    #  # Check for URL arguments. Disregard them
            #    #  file_requested = file_requested.split('?')[0]  # disregard anything after '?'

            #    #  if (file_requested == '/'):  # in case no file is specified by the browser
            #    #      file_requested = '/index.html' # load index.html by default

            #    #  file_requested = self.www_dir + file_requested
            #    #  print ("Serving web page [",file_requested,"]")

            #     try:
            #         print(message_list)
            #         response_headers = self._gen_headers(200)

            #     except Exception as e:  # in case file was not found, generate 404 page
            #         print("Warning, file not found. Serving response code 404\n", e)
            #         response_headers = self._gen_headers(404)

            #         if (request_method == 'GET'):
            #             response_content = b"<html><body><p>Error 404: File not found</p><p>Python HTTP server</p></body></html>"

            # server_response = response_headers.encode()  # return headers for GET and HEAD
            # if (request_method == 'GET'):
            #     server_response += response_content  # return additional conten for GET only

            # conn.send(server_response)


def graceful_shutdown(sig, dummy):
    """ This function shuts down the server. It's triggered
    by SIGINT signal """
    s.shutdown()  # shut down the server
    import sys
    sys.exit(1)

# shut down on ctrl+c
# signal.signal(signal.SIGINT, graceful_shutdown)


print("Starting web server")
s = Server(80)  # construct server object
s.activate_server()  # aquire the socket
