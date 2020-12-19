import paramiko
import rft_client
from my_path import myPath
import json
import sys


class clientIntf:
    def __init__(self):
        self.client = None

    def client_setup(self):
        paramiko.util.log_to_file("demo.log")
        self.client = rft_client.Client()
        if not self.client.attempt_connection():
            sys.exit(1)

        print("Connection established!")

        cmd = {'type': 'path_request', 'data': None}
        self.client.chan.send(json.dumps(cmd))

        recvd_cmd = self.client.recv_data()
        if recvd_cmd['type'] == 'path':
            self.client.remote_path = myPath(recvd_cmd['data']['path'])
        return self.client

    def event_handler(self, event, arg=None):
        print('Event handler: ', event)
        if event == 'Exit':
            self.client.quit()
        elif event == '->': # upload
            self.client.send_command('upload')
            self.client.upload_file(arg)
        elif event == '<-': # download
            self.client.send_command('download', arg)
            self.client.download_file()
        elif event == 'cd':
            self.client.change_dir(arg)
        elif event == 'cdr':
            self.client.send_command('cdr', arg)
            resp = self.client.recv_data()
            if not resp['error']:
                print('no error')
                self.client.remote_path = myPath(resp['data']['path'])
            print(resp['error'])
        elif event == 'REFRESH':
            self.client.send_command('lsr', None)
            resp = self.client.recv_data()
            if not resp['error']:
                print(resp['data']['ls'])
                return resp['data']['ls']
            print(resp['error'])

    def get_local_path(self):
        return self.client.local_path

    def get_remote_path(self):
        return self.client.remote_path

    def set_local_path(self, path):
        self.client.local_path = myPath(path)