import paramiko
import base64
from binascii import hexlify
import getpass
import os

def agent_auth(transport, username):
    """
    Attempt to authenticate to the given transport using any of the private
    keys available from an SSH agent.
    """

    agent = paramiko.Agent()
    agent_keys = agent.get_keys()
    if len(agent_keys) == 0:
        return

    for key in agent_keys:
        print("Trying ssh-agent key %s" % hexlify(key.get_fingerprint()))
        try:
            transport.auth_publickey(username, key)
            print("... success!")
            return
        except paramiko.SSHException:
            print("... nope.")


def manual_auth(username, hostname, t):
    default_auth = "p"
    auth = input(
        "Auth by (p)assword or (r)sa key? [%s] " % default_auth
    )
    if len(auth) == 0:
        auth = default_auth

    if auth == "r":
        default_path = os.path.join(os.environ["HOME"], ".ssh", "id_rsa")
        path = input("RSA key [%s]: " % default_path)
        if len(path) == 0:
            path = default_path
        try:
            key = paramiko.RSAKey.from_private_key_file(path)
        except paramiko.PasswordRequiredException:
            password = getpass.getpass("RSA key password: ")
            key = paramiko.RSAKey.from_private_key_file(path, password)
        t.auth_publickey(username, key)
    else:
        pw = getpass.getpass("Password for %s@%s: " % (username, hostname))
        t.auth_password(username, pw)
