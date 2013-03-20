"""
Main module that configures tcpr, copies all the files to the virtual
machines, runs all the different processes, and cleans up the temporary
files and processes afterwards.
"""

import argparse
import pkg_resources
import random
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

from path import path

from .vmapi import VM
from .utils import get_random_string

__version__ = '0.1'

_TCPR_INI_TEMPLATE = """
[server]

# server
listen=0.0.0.0:%(server_port)d

# admin console
listen_cmd=0.0.0.0:%(console_port)d

listen_http=

# The reflector will listen on the address and port range below
reflector=0.0.0.0:%(forward_port_minus_one)d-%(forward_port_minus_one)d-%(forward_port_plus_one)d

user_db=%(temp_dir)s\user_db

# Send keep alive packets to every connected client at regular intervals.
# Time is in seconds. 0 disables the sending of these packets.
alive_interval=120

# When no packets have been received for "alive_timeout" seconds, close
# the connection. Clients can try to reconnect afterwards.
# If set to 0 , the server will never close any connection.
alive_timeout=300

[client]
server=%(server_ip)s:%(server_port)d

clientname=%(client_name)s
password=%(client_password)s

classname=workstation

alive_interval=120
alive_timeout=300

forwards=forward%(forward_port)d:forward%(forward_port)d:127.0.0.1:%(forward_port)d
"""

class Tunnel(object):

    def __init__(self, vm_name, port, username, password):
        self.forward_port = port
        self.server_port = random.SystemRandom().randint(4000, 65000)
        self.console_port = self.server_port + 1
        self.vmapi = vmapi.VM(vm_name=vm_name,
                              username=username, password=password)
        self.manager_password = get_random_string()

    def start(self, started_event=None, done_event=None):
        """
        Set up the tunnel. Does not return until the tunnel is destroyed.

        started_event.set() is called when the tunnel is ready. Then,
        done_event.wait() is called, unless it is None, in which case the
        code waits until the spawned local client process terminates.
        """

        tcpr_zip = zipfile.ZipFile(pkg_resources.resource_stream(
            'vmreflect', 'lib-win32/TcpProxyReflector-0.1.3-win32.zip'))

        self.host_temp_dir = path(tempfile.mkdtemp(prefix='vmreflect'))
        try:
            local_tcpr_exe = self.host_temp_dir.joinpath('tcpr.exe')
            with open(local_tcpr_exe, 'w') as out:
                out.write(tcpr_zip.read('TcpProxyReflector-0.1.3/tcpr.exe'))
            local_tcpr_exe.chmod(0600)

            guest_temp_file_base = self.vmapi._create_temp_file()
            self.guest_temp_dir = guest_temp_file_base + '.d'

            # Step 1. Create the .ini file.
            self._create_ini_file()

            try:
                self.vmapi.copy_file_to_guest(self.host_temp_dir,
                                              self.guest_temp_dir)
                try:
                    killed = False
                    started = False

                    remote_tcpr_cmd = self.guest_temp_dir + '\\' + 'tcpr.exe'
                    remote_tcpr_ini = self.guest_temp_dir + '\\' + 'tcpr.ini'

                    # Step 2. Create a manager password.
                    self.vmapi._run_command('%s %s -m %s' % (
                        remote_tcpr_cmd, remote_tcpr_ini,
                        self.manager_password))

                    # Step 3. Start the server.
                    self.vmapi._run_command_no_output('start %s %s -s' % (
                        remote_tcpr_cmd, remote_tcpr_ini))
                    started = True

                    for p in self.vmapi.list_processes():
                        if remote_tcpr_cmd in p.cmd:
                            server_pid = p.pid
                            break
                    else:
                        raise Exception('server pid not found')

                    try:
                        # Step 4. Connect to the console
                        # Step 5. Add a client.
                        self._send_to_console(
                            'client add %s %s clients\n'
                            % (self.client_name, self.client_password),
                            'client %s added' % self.client_name)

                        # Step 6. Connect the client.
                        client_proc = subprocess.Popen(
                            ['tcpr', self.local_tcpr_ini, '-c'])

                        # FIXME!
                        time.sleep(0.2)

                        try:
                            # Step 7. Start forwarding.
                            self._send_to_console(
                                'list\nstart 0 * p=%d' % self.forward_port,
                                'forwarder listening on 0.0.0.0:%d'
                                % self.forward_port)

                            # Signal that the tunnel is open
                            if started_event:
                                started_event.set()

                            # Wait until the calling code is done with the
                            # tunnel, or the client process is killed.
                            if done_event:
                                done_event.wait()
                            else:
                                client_proc.wait()

                        finally:
                            if not client_proc.poll():
                                client_proc.terminate()
                    finally:
                        killed = True
                        self.vmapi.kill_process(server_pid)
                finally:
                    if killed or not started:
                        self.vmapi.delete_directory(self.guest_temp_dir)
                    else:
                        print 'started?', started, 'killed?', killed
            finally:
                self.vmapi.delete_file(guest_temp_file_base)
        finally:
            shutil.rmtree(self.host_temp_dir)

    def _send_to_console(self, command, expected_response):
        proc = subprocess.Popen(
            ['tcpr', '-o',
             '-u', 'manager',
             '-p', self.manager_password,
             self.server_ip,
             str(self.console_port)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        stdout, stderr = proc.communicate(command)
        proc.wait()
        if proc.returncode:
            raise Exception('console returned %d\n%s\n%s'
                            % (proc.returncode, stdout, stderr))
        if expected_response not in stdout:
            raise Exception('expected response %s not in output\n%s'
                            % (repr(expected_response), stdout))

    def _create_ini_file(self):
        stdout, stderr = self.vmapi._run_command(
            'ipconfig | find "IP Address"')
        self.server_ip = stdout.strip().split()[-1]

        self.client_name = 'tcprclient'
        self.client_password = get_random_string()

        self.local_tcpr_ini = self.host_temp_dir.joinpath('tcpr.ini')

        with open(self.local_tcpr_ini, 'w') as out:
            out.write(_TCPR_INI_TEMPLATE % {
                'server_port': self.server_port,
                'console_port': self.console_port,
                'forward_port_minus_one': self.forward_port - 1,
                'forward_port': self.forward_port,
                'forward_port_plus_one': self.forward_port + 1,
                'server_ip': self.server_ip,
                'client_name': self.client_name,
                'client_password': self.client_password,
                'temp_dir': self.guest_temp_dir,
            })

def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('vm_name', action='store',
                       help="""The name of the virtual machine in which to
                        set up the tunnel. Can also be the absolute path
                        to a .vmwarevm directory or .vmx file.""")
    parser.add_argument('--port', '-P', type=int, default=8000,
                       help='The port number to forward')
    parser.add_argument('--vm-username', '-u', default='Administrator')
    parser.add_argument('--vm-password', '-p', default='test',
                       help="""The Windows username and password of the guest
                        virtual machine. These are needed to access files
                        and run programs inside the virtual machine.""")
    args = parser.parse_args(args=args)
    tunnel = Tunnel(vm_name=args.vm_name,
                    port=args.port,
                    username=args.vm_username,
                    password=args.vm_password)
    tunnel.start()
