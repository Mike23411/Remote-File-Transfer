import base64
from binascii import hexlify
import os
import socket
import sys
import threading
import traceback
import json
from pathlib import Path
from channel import chanMessageInterface

import file_transmit
from my_path import myPath

import paramiko
from paramiko.py3compat import b, u, decodebytes

# setup logging
paramiko.util.log_to_file("demo_server.log")

host_key = paramiko.RSAKey(filename="test_rsa.key")
# host_key = paramiko.DSSKey(filename='test_dss.key')

print("Read key: " + u(hexlify(host_key.get_fingerprint())))


class Server(paramiko.ServerInterface):
    # 'data' is the output of base64.b64encode(key)
    # (using the "user_rsa_key" files)
    data = (
        b"AAAAB3NzaC1yc2EAAAABIwAAAIEAyO4it3fHlmGZWJaGrfeHOVY7RWO3P9M7hp"
        b"fAu7jJ2d7eothvfeuoRFtJwhUmZDluRdFyhFY/hFAh76PJKGAusIqIQKlkJxMC"
        b"KDqIexkgHAfID/6mqvmnSJf0b5W8v5h2pI/stOSwTQ+pxVhwJ9ctYDhRSlF0iT"
        b"UWT10hcuO4Ks8="
    )
    good_pub_key = paramiko.RSAKey(data=decodebytes(data))

    def __init__(self):
        self.event = threading.Event()
        print(self)

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if (username == "ben") and (password == "foo"):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        print("Auth attempt with key: " + u(hexlify(key.get_fingerprint())))
        if (username == "ben") and (key == self.good_pub_key):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_with_mic(
            self, username, gss_authenticated=paramiko.AUTH_FAILED, cc_file=None
    ):
        """
        .. note::
            We are just checking in `AuthHandler` that the given user is a
            valid krb5 principal! We don't check if the krb5 principal is
            allowed to log in on the server, because there is no way to do that
            in python. So if you develop your own SSH server with paramiko for
            a certain platform like Linux, you should call ``krb5_kuserok()`` in
            your local kerberos library to make sure that the krb5_principal
            has an account on the server and is allowed to log in as a user.
        .. seealso::
            `krb5_kuserok() man page
            <http://www.unix.com/man-page/all/3/krb5_kuserok/>`_
        """
        if gss_authenticated == paramiko.AUTH_SUCCESSFUL:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_keyex(
            self, username, gss_authenticated=paramiko.AUTH_FAILED, cc_file=None
    ):
        if gss_authenticated == paramiko.AUTH_SUCCESSFUL:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def enable_auth_gssapi(self):
        return True

    def get_allowed_auths(self, username):
        return "gssapi-keyex,gssapi-with-mic,password,publickey"

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(
            self, channel, term, width, height, pixelwidth, pixelheight, modes
    ):
        return True


class Listener:
    def __init__(self):
        self.sock = None
        self.client = None
        self.transport = None
        self.addr = None
        self.server = None
        self.chan = None
        self.default_path = None
        self.chan_intf = None
        self.local_path = myPath('C:/rftclient/demo')

    def start_listening(self):
        self.bind_to_socket()
        self.await_connection()
        self.establish_shell()
        self.authenticate()
        self.handle_commands()

    def bind_to_socket(self):
        # now connect
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(("", 5600))
        except Exception as e:
            print("*** Bind failed: " + str(e))
            traceback.print_exc()
            sys.exit(1)

    def await_connection(self):
        try:
            self.sock.listen(100)
            print("Listening for connection ...")
            self.client, self.addr = self.sock.accept()
        except Exception as e:
            print("*** Listen/accept failed: " + str(e))
            traceback.print_exc()
            sys.exit(1)

        print("Got a connection!")

    def establish_shell(self):
        DoGSSAPIKeyExchange = True
        try:
            self.transport = paramiko.Transport(self.client, gss_kex=DoGSSAPIKeyExchange)
            self.transport.set_gss_host(socket.getfqdn(""))
            try:
                self.transport.load_server_moduli()
            except:
                print("(Failed to load moduli -- gex will be unsupported.)")
                raise
            self.transport.add_server_key(host_key)
            self.server = Server()
            try:
                self.transport.start_server(server=self.server)
                #self.transport.set_subsystem_handler('file', rftHandler)
            except paramiko.SSHException:
                print("*** SSH negotiation failed.")
                sys.exit(1)
        except Exception as e:
            print("*** Caught exception: " + str(e.__class__) + ": " + str(e))
            traceback.print_exc()
            try:
                self.transport.close()
            except:
                pass
            sys.exit(1)

    def authenticate(self):
        # wait for auth
        self.chan = self.transport.accept(20)
        if self.chan is None:
            print("*** No channel.")
            sys.exit(1)
        print("Authenticated!")

        self.chan_intf = chanMessageInterface(self.chan)

        self.server.event.wait(100)
        if not self.server.event.is_set():
            print("*** Client never asked for a shell.")
            sys.exit(1)

    def send_response(self, path=None, dirs=None, err=None):
        msg = {
            'type': 'command_response',
            'data': {
                'path': path,
                'ls': dirs
            },
            'error': err
        }
        json_msg = json.dumps(msg)
        self.chan_intf.send(json_msg)

    def recv(self):
        msg = None
        while msg is None:
            msg = self.chan_intf.recv()
        try:
            json_msg = json.loads(msg)
        except json.decoder.JSONDecodeError:
            print('Decode error: ', end='')
            print(msg)
            return None
        return json_msg

    def handle_commands(self):
        while True:
            # main loop
            msg = self.recv()
            if not msg:
                continue
            elif msg['type'] == 'command':
                print(msg)
                data = msg['data']
                if data['command'] == 'lsr':
                    resp = [(x.name, x.is_dir()) for x in self.local_path.ls()]
                    self.send_response(dirs=resp)
                elif data['command'] == 'cdr':
                    arg = data['argument']
                    if not arg:
                        self.send_response(err='noarg')
                    elif self.local_path.cd_mult(arg):
                        self.send_response(path=self.local_path.__str__())
                    else:
                        self.send_response(err='invalid path')
                elif data['command'] == 'download':
                    print('Download request received')
                    server_path = data['argument']['server_path']
                    client_path = data['argument']['client_path']
                    file_transmit.send_file(self.chan_intf, server_path, client_path, server=True)
                elif data['command'] == 'upload':
                    print('Upload request received')
                    file_transmit.receive_file(self.chan_intf, server=True)
                elif data['command'] == 'preview':
                    print('Preview request received')
                    file_path = self.local_path.path / Path(data['argument'])
                    file = file_path.open(mode='r')
                    file_transmit.preview_upload(self.chan_intf, file.read())
            elif msg['type'] == 'path_request':
                if self.local_path:
                    msg = {'type': 'path', 'data': {'path': self.local_path.path.__str__()}}
                else:
                    msg = {'type': 'path', 'data': {'path': 'C:/'}}
                    self.local_path = myPath('C:/')
                self.chan_intf.send(json.dumps(msg))


if __name__ == '__main__':
    # possibly thread listeners, maybe make socket out here and pass socket into listener, have multiple transports
    listener = Listener()
    listener.start_listening()

    while True:
        pass
