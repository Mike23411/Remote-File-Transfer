import getpass
import os
import select
import socket
import sys
import time
import traceback
from paramiko.py3compat import input
import auth
import json
import file_transmit
from termcolor import colored
from my_path import myPath, print_ls
from channel import chanMessageInterface
import argparse
import gui

import paramiko


class Client:
    def __init__(self):
        self.hostname = None
        self.username = ""
        self.port = None
        self.sock = None
        self.chan = None
        self.transport = None
        self.local_path = myPath('C:/')
        self.remote_path = None
        self.chan_intf = None

        self.read_hostname()

    def send_command(self, cmd, arg=None):
        if cmd == 'download':
            server_path = self.remote_path.path / arg
            arg = {
                'client_path': self.local_path.__str__(),
                'server_path': server_path.__str__()
            }
        msg = {
            'type': 'command',
            'data': {
                'command': cmd,
                'argument': arg
            }
        }
        json_msg = json.dumps(msg)
        self.chan_intf.send(json_msg)

    def recv_data(self):
        msg = None
        while msg is None:
            msg = self.chan_intf.recv()
        json_msg = json.loads(msg)
        return json_msg

    def attempt_connection(self):
        reconnect = True
        retry = None
        while (reconnect):
            if not self.connect():
                while retry not in ['y', 'n']:
                    print('Connection failed, retry? [y/n]:')
                    retry = input()
                    if retry == 'y':
                        reconnect = True
                    elif retry == 'n':
                        reconnect = False
                    else:
                        print('Invalid input')
                        retry = None
            else:
                self.chan_intf = chanMessageInterface(self.chan)
                return True
        return False

    def quit(self):
        self.chan.close()
        self.transport.close()
        sys.exit(0)

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.hostname, self.port))
        except Exception as e:
            print("*** Connect failed: " + str(e))
            traceback.print_exc()
            sys.exit(1)
        try:
            self.transport = paramiko.Transport(self.sock)
            try:
                self.transport.start_client()
            except paramiko.SSHException as e:
                print("*** SSH negotiation failed.", e)
                sys.exit(1)

            try:
                keys = paramiko.util.load_host_keys(
                    os.path.expanduser("~/.ssh/known_hosts")
                )
            except IOError:
                try:
                    keys = paramiko.util.load_host_keys(
                        os.path.expanduser("~/ssh/known_hosts")
                    )
                except IOError:
                    print("*** Unable to open host keys file")
                    keys = {}

            # check server's host key -- this is important.
            key = self.transport.get_remote_server_key()
            if self.hostname not in keys:
                print("*** WARNING: Unknown host key!")
            elif key.get_name() not in keys[self.hostname]:
                print("*** WARNING: Unknown host key!")
            elif keys[self.hostname][key.get_name()] != key:
                print("*** WARNING: Host key has changed!!!")
                sys.exit(1)
            else:
                print("*** Host key OK.")
            # get username
            if self.username == "":
                default_username = getpass.getuser()
                self.username = input("Username [%s]: " % default_username)
                if len(self.username) == 0:
                    self.username = default_username

            auth.agent_auth(self.transport, self.username)
            if not self.transport.is_authenticated():
                auth.manual_auth(self.username, self.hostname, self.transport)
            if not self.transport.is_authenticated():
                print("*** Authentication failed. :(")
                self.transport.close()
                sys.exit(1)

            self.chan = self.transport.open_session()
            self.chan.get_pty()
            self.chan.invoke_shell()
        except Exception as e:
            print("*** Caught exception: " + str(e.__class__) + ": " + str(e))
            traceback.print_exc()
            try:
                self.transport.close()
            except:
                pass
            return False
        return True

    def read_hostname(self):
        if len(sys.argv) > 1:
            self.hostname = sys.argv[1]
            if self.hostname.find("@") >= 0:
                self.username, self.hostname = self.hostname.split("@")
        else:
            self.hostname = input("Hostname: ")
        if len(self.hostname) == 0:
            print("*** Hostname required.")
            sys.exit(1)
        self.port = 22
        if self.hostname.find(":") >= 0:
            self.hostname, portstr = self.hostname.split(":")
            self.port = int(portstr)

    def take_user_input(self):
        c = input()
        if c == 'commands':
            print('ls: List local directories and files')
            print('lsr: List remote directories and files')
            print('cd: Change local directory')
            print('cdr: Change remote directory')
            print('download [filename]: download remote file from host to current local dir')
            print('upload [filename]: upload local file to current remote dir')
            print('preview [filename]: preview file on remote host')
            print('quit: Quit remote file transfer')
            return None
        elif 'download ' in c \
                or 'upload ' in c \
                or 'preview ' in c:
            msg = c.split()
            if len(msg) < 2:
                print("Too few arguments")
                return None
            elif len(msg) > 2:
                print("Too many arguments")
                return None
            return msg
        elif 'cd ' in c:
            msg = c.split()
            if len(msg) < 2:
                print("Too few arguments")
                return None
            msg = ['cd', c[3:]]
            return msg
        elif 'cdr ' in c:
            msg = c.split()
            if len(msg) < 2:
                print("Too few arguments")
                return None
            msg = ['cdr', c[4:]]
            return msg
        elif c not in ['ls', 'lsr', 'quit']:
            print('Invalid command, enter commands for full list of commands')
            return None
        else:
            return [c]

    def upload_file(self, filename):
        path = self.local_path.path / filename
        print(path)
        file_transmit.send_file(self.chan_intf, path.__str__(), self.remote_path.__str__())

    def download_file(self):
        print('Downloading...')
        file_transmit.receive_file(self.chan_intf)

    def list_dir(self):
        self.local_path.ls(print_ls=True)

    def change_dir(self, new_dir):
        self.local_path.cd_mult(new_dir)

    def preview(self):
        file_transmit.preview_download(self.chan_intf)


def main():
    paramiko.util.log_to_file("demo.log")
    client = Client()
    if not client.attempt_connection():
        sys.exit(1)

    print("Connection established!")

    cmd = {'type': 'path_request', 'data': None}
    client.chan.send(json.dumps(cmd))

    recvd_cmd = client.recv_data()
    if recvd_cmd['type'] == 'path':
        client.remote_path = myPath(recvd_cmd['data']['path'])

    while True:
        print(client.local_path.__str__() + '$', end=' ')  # print current path here, placeholder for now
        cmd = client.take_user_input()
        if cmd is None:
            continue
        if cmd[0] == 'ls':
            client.list_dir()
        elif cmd[0] == 'cd':
            client.change_dir(cmd[1])
        elif cmd[0] == 'lsr':
            print('Remote Path: ', end='')
            print(client.remote_path)
            client.send_command(cmd[0])
            resp = client.recv_data()
            if not resp['error']:
                print_ls(resp['data']['ls'])
        elif cmd[0] == 'cdr':
            client.send_command(cmd[0], cmd[1])
            resp = client.recv_data()
            if not resp['error']:
                client.remote_path = myPath(resp['data']['path'])
            print('Remote Path: ', end='')
            print(client.remote_path)
        elif cmd[0] == 'upload':
            client.send_command(cmd[0], cmd[1])
            client.upload_file(cmd[1])
        elif cmd[0] == 'download':
            client.send_command(cmd[0], cmd[1])
            client.download_file()
        elif cmd[0] == 'preview':
            client.send_command(cmd[0], cmd[1])
            client.preview()
        elif cmd[0] == 'quit':
            client.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Transfer files with remote host')
    parser.add_argument('--gui', help='Start client with gui')

    args = parser.parse_args()

    if args.gui:
        gui.main()
    else:
        main()
