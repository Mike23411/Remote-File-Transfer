from scp import SCPClient, SCPException
import os
import json
import tqdm
from msvcrt import getch


def receive_file(chan, server=False):
    if server:
        chan.send('ready')
    else:
        msg = chan.blocking_recv()
        if msg != b'ready':
            print(msg)
            return False

    msg = chan.blocking_recv()
    msg = json.loads(msg)
    filename = msg['filename']
    path = msg['remote_path']
    if path[-1] != '\\':
        path += '\\'
    local_path = path + filename
    filesize = int(msg['filesize'])
    progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024,
                         leave=True)
    with open(local_path, "wb") as f:
        while True:
            bytes_read = chan.recv()
            if bytes_read == b'stop':
                break
            # if not bytes_read:
            #     break
            if bytes_read:
                f.write(bytes_read)
                progress.update(len(bytes_read))
    print('\nFile received!')


def send_file(chan, local_path, remote_path, server=False):
    filesize = os.path.getsize(local_path)
    filename = local_path.split('\\')[-1]

    if server:
        chan.send('ready')
    else:
        msg = chan.blocking_recv()
        if msg != b'ready':
            print(msg)
            return False

    msg = {'filename': filename, 'remote_path': remote_path, 'filesize': filesize}
    chan.send(json.dumps(msg))

    progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024,
                         leave=True)
    with open(local_path, 'rb') as f:
        for _ in progress:
            bytes_read = f.read(4096)
            if not bytes_read:
                break
            chan.sendall_bytes(bytes_read)
            progress.update(len(bytes_read))
    chan.send('stop')
    print('\nFile uploaded!')
    return True


def preview_upload(chan, file):
    lines = file.split('\n')
    running = True

    num_lines = 10
    first_line = 1
    total_lines = len(lines)

    while running:
        if first_line + num_lines < total_lines:
            send_cmd = {'type': 'preview',
                        'num_lines': num_lines,
                        'first_line': first_line,
                        'data': lines[(first_line - 1): (first_line + num_lines - 1)],
                        'eof': False}
        else:
            send_cmd = {'type': 'preview',
                        'num_lines': num_lines - first_line - 1,
                        'first_line': first_line,
                        'data': lines[(first_line - 1):],
                        'eof': True}

        chan.send(json.dumps(send_cmd))

        cmd = json.loads(chan.blocking_recv())
        if cmd['action'] == 'stop':
            running = False
        elif cmd['action'] == 'continue':
            running = True
            first_line = cmd['first_line']
        elif cmd['action'] == 'search':
            running = True
            first_line = cmd['first_line']
            if first_line > total_lines:
                first_line = total_lines - 9


def preview_download(chan):
    running = True
    clear = lambda: os.system('cls')
    possible_actions = 'n: Next section\t\tb: Previous section\tg: Search line\tq: Quit'

    while running:
        msg = chan.blocking_recv()
        msg = json.loads(msg)
        num_lines = msg['num_lines']
        first_line = msg['first_line']
        lines = msg['data']

        i = 0

        clear()
        print(possible_actions)
        for line in lines:
            print(i + first_line, end=' ')
            print(line)
            i = i + 1
        if msg['eof']:
            print('EOF')

        print(':', end='')
        while True:
            user_input = getch()
            if user_input == b'n':
                msg = {'action': 'continue',
                       'first_line': first_line + i if not msg['eof'] else first_line,
                       }
                chan.send(json.dumps(msg))
                break
            elif user_input == b'b':
                msg = {'action': 'continue',
                       'first_line': first_line - 10 if first_line > 10 else 1
                       }
                chan.send(json.dumps(msg))
                break
            elif user_input == b'g':
                search_line = ''
                while search_line == '':
                    try:
                        search_line = int(input('Search For Line: '))
                    except ValueError:
                        search_line = ''
                        print('Invalid input - integer only')
                msg = {'action': 'search',
                       'first_line': search_line
                       }
                chan.send(json.dumps(msg))
                break
            elif user_input == b'q':
                msg = {'action': 'stop',
                       'first_line': None
                       }
                chan.send(json.dumps(msg))
                running = False
                break
    clear()
