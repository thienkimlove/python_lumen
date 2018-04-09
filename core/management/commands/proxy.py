import select
import socket
import sys
import threading

import paramiko as paramiko
import re
import time

import redis
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from gevent.pool import Pool
from strgen import StringGenerator
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from django.utils.crypto import get_random_string


from django.core.management.base import BaseCommand
from django.db import connection
from core.models import Log
from python_lumen.settings import LOG_FILE


def handler(chan, host, port):
    sock = socket.socket()
    try:
        sock.connect((host, port))
    except Exception as e:
        print('Forwarding request to %s:%d failed: %r' % (host, port, e))
        return  print('Connected! Tunnel open %r -&gt; %r -&gt; %r' % (chan.origin_addr, chan.getpeername(),(host, port)))

    while True:
        r, w, x = select.select([sock, chan], [], [])

        if sock in r:
            data = sock.recv(1024)
            if len(data) == 0:
                 break
            chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                sock.send(data)
                chan.close()
                sock.close()

    print('Tunnel closed from %r' % (chan.origin_addr,))

def reverse_forward_tunnel(server_port, remote_host, remote_port, transport):
    transport.request_port_forward('', server_port)
    while True:
        chan = transport.accept(1000)
        if chan is None:
            continue
        thr = threading.Thread(target=handler, args=(chan, remote_host, remote_port))
        thr.setDaemon(True)
        thr.start()

def transport(host, port, username, password, forward_port, remote_host, remote_port):
    client = paramiko.SSHClient()
    #client.load_system_host_keys()
    #client.set_missing_host_key_policy(paramiko.WarningPolicy())

    try:
        client.connect(
            host,
            port,
            username=username,
            pkey=False,
            key_filename='',
            look_for_keys=False,
            password=password,
        )

    except Exception as e:
        print('*** Failed to connect to %s:%d: %r' % (host, port, e))
        print('Now forwarding remote port %d to %s:%d ...' % (forward_port, remote_host, remote_port))

    try:
        reverse_forward_tunnel(forward_port, remote_host, remote_port, client.get_transport())

    except KeyboardInterrupt:
        print('C-c: Port forwarding stopped.')
        sys.exit(0)


def run_command_over_ssh(server , username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, username=username, password=password)

    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("mkdir -p ~/.ssh")
    debug(ssh_stdout)
    debug(ssh_stderr)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ssh-keygen -f ~/.ssh/id_rsa_new -t rsa -N ''")
    debug(ssh_stdout)
    debug(ssh_stderr)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("chmod 600 ~/.ssh/id_rsa_new")
    debug(ssh_stdout)
    debug(ssh_stderr)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("cat ~/.ssh/id_rsa_new.pub >> ~/.ssh/authorized_keys")
    debug(ssh_stdout)
    debug(ssh_stderr)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ssh -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa_new -f -N -D 0.0.0.0:1080 local")
    debug(ssh_stdout)
    debug(ssh_stderr)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iptables -I INPUT -p tcp -s 0.0.0.0 --dport 1080 -j ACCEPT")
    debug(ssh_stdout)
    debug(ssh_stderr)

def debug(msg):
    with open(LOG_FILE, 'r') as original: data = original.read()
    with open(LOG_FILE, 'w') as modified: modified.write(data + str(repr(msg)) + "\n")

def get_url(url, server, username, password):

    run_command_over_ssh(server , username, password)


    proxies = {
        "http":  "socks5://"+server+":1080",
        "https": "socks5://"+server+":1080"
    }
    session = requests.session()
    session.max_redirects = 10
    session.verify = False
    session.timeout = (60, 30)
    session.proxies.update(proxies)

    url = unquote(url)
    url = url.replace('&amp;', '&')


    g = session.get(url)

    print(g.content)


def wait_for_ssh_to_be_ready(host, port, timeout, retry_interval):
    client = paramiko.client.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    retry_interval = float(retry_interval)
    timeout = int(timeout)
    timeout_start = time.time()
    while time.time() < timeout_start + timeout:
        time.sleep(retry_interval)
        try:
            client.connect(host, int(port), allow_agent=False,
                           look_for_keys=False)
        except paramiko.ssh_exception.SSHException as e:
            # socket is open, but not SSH service responded
            if e.message == 'Error reading SSH protocol banner':
                print(e)
                continue
            print('SSH transport is available!')
            break
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            print('SSH transport is not ready...')
            continue

class Command(BaseCommand):
    help = 'Test through SSH'
    def handle(self, *args, **options):
        #port = 12345
        get_url('https://whatismyipaddress.com/ip-lookup', '74.42.183.74', 'support', 'support')
        #transport('viemgan.com.vn', 22, 'root', 'Tieungao12', 9160, 'viemgan.com.vn', 8888)




