# coding: UTF-8

"""
Full end-to-end test: start a server, tunnel, and connect from the VM
"""

import argparse
import SocketServer
import contextlib
import os
import pkg_resources
import socket
import string
import tempfile
import threading
import time
import unittest

from path import path

from vmreflect import Tunnel
from vmreflect.tests import test_config
from vmreflect.utils import get_random_string
from vmreflect.vmapi import VM

class DataReversingTCPRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024)
        response = ''.join(reversed(data))
        self.request.sendall(response)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True

def client(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    try:
        sock.sendall(message)
        response = sock.recv(1024)
        return response
    finally:
        sock.close()

class Server(object):
    """
    A simple TCP server that echoes whatever is sent to it, in reverse.
    """

    def __init__(self, verbose=False, port=0):
        # Port 0 means to select an arbitrary unused port
        HOST, PORT = "localhost", port

        self.server = ThreadedTCPServer((HOST, PORT),
                                        DataReversingTCPRequestHandler)
        self.ip, self.port = self.server.server_address

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=self.server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()
        if verbose:
            print "Server running at %s:%s" % (self.ip, self.port)

    def close(self):
        self.server.shutdown()

class TestEndToEnd(unittest.TestCase):
    """
    This is the real test of the package: start a server on the host
    on a random port, set up the tunnel, then connect to the server
    from the guest and verify that it works.
    """

    def test_reversing_server(self):
        random_string = get_random_string()
        with contextlib.closing(Server()) as server:
            result = client(server.ip, server.port, random_string)
            self.assertEquals(result, ''.join(reversed(random_string)))

    def test_end_to_end(self):
        random_string = get_random_string()
        with contextlib.closing(Server()) as server:

            # Create a tunnel and wait for it to start.

            tunnel = Tunnel(port=server.port,
                            vm_name=test_config.vm_name,
                            username=test_config.vm_username,
                            password=test_config.vm_password)

            started = threading.Event()
            done = threading.Event()

            def tunnel_thread():
                tunnel.start(started_event=started, done_event=done)

            tunnel_thread = threading.Thread(target=tunnel_thread)
            tunnel_thread.start()

            started.wait()

            try:

                tunnel_vmapi = VM(vm_name=test_config.vm_name,
                                username=test_config.vm_username,
                                password=test_config.vm_password)

                # get temp dir
                tmpdir, _ = tunnel_vmapi._run_command('echo %TEMP%')
                tmpdir = tmpdir.strip()

                # copy socketclient.exe to temporary filename
                target_filename = (tmpdir + r'\socketclient-' +
                                get_random_string() + '.exe')
                fd, local_temp = tempfile.mkstemp(prefix='vmreflect')
                os.close(fd)
                try:
                    socketclient_bin = pkg_resources.resource_stream(
                        'vmreflect', 'lib-win32/socketclient/socketclient.exe')
                    with open(local_temp, 'wb') as out:
                        out.write(socketclient_bin.read())
                    os.chmod(local_temp, 0700)
                    tunnel_vmapi.copy_file_to_guest(
                        local_temp, target_filename)
                    try:
                        output, _ = tunnel_vmapi._run_command(
                            '%s %s %d %s' % (target_filename,
                                            'localhost', server.port,
                                            repr(random_string)))

                    finally:
                        tunnel_vmapi.delete_file(target_filename)

                    self.assertIn(''.join(reversed(random_string)),
                                output)
                finally:
                    os.unlink(local_temp)

            finally:
                done.set()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--keep-alive', action='store_true')
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    server = Server(verbose=True, port=args.port)
    print client(server.ip, server.port, "Hello World 1")
    try:
        if args.keep_alive:
            while 1:
                time.sleep(60)
    finally:
        server.close()

if __name__ == '__main__':
    main()
