# coding: UTF-8

"""
Rough API for controlling virtual machines by calling vmrun.

Methods that could be rewritten to use a smarter strategy are underscored.
For example, instead of retrieving stdout and stderr files individually,
they could be written to a single directory and then the directory could be
copied over in one shot.

It is too slow because for every single request it forks a new process,
connects to the VM server, and authenticates the user.

It should be rewritten to use VIX, which is all in-process:
<http://www.vmware.com/support/developer/vix-api/vix112_reference/>
"""

import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import namedtuple

from path import path

_VMRUN = os.getenv(
    'VMRUN', '/Applications/VMware Fusion.app/Contents/Library/vmrun')

def _vmx_path(vm_name):
    """Return the path to the .vmx file corresponding to vm_name.

    vm_name may be the name of a virtual machine, or the path to a virtual
    machine folder or .vmx file.
    """
    if vm_name.lower().endswith('.vmx') and os.path.isfile(vm_name):
        return path(vm_name)
    likely = (path("~/Virtual Machines.localized/").expanduser()
                .joinpath('%s.vmwarevm/%s.vmx' % (vm_name, vm_name)))
    if likely.isfile():
        return likely
    basename = path(vm_name).basename().namebase
    for suffix_glob in ['/%s.vmx' % basename,
                        '.vmwarevm/%s.vmx' % basename,
                        '/*.vmx',
                        '.vmwarevm/*.vmx',
                       ]:
        possible_vmxes = glob.glob(vm_name + suffix_glob)
        if len(possible_vmxes) == 1:
            return path(possible_vmxes[0])
    raise Exception("No .vmx file associated with %s was found"
                    % vm_name)

class VmException(Exception):
    """
    Raised when an operation on a virtual machine fails.

    The returncode attribute contains the return code from vmrun.

    """

    def __init__(self, returncode, msg):
        super(Exception, self).__init__(msg)
        self.returncode = returncode

GuestProcess = namedtuple('GuestProcess', 'pid owner cmd')

_re_processes = re.compile(r'^pid=(\d+), owner=(.*), cmd=(.*)$')

class VM(object):
    def __init__(self, vm_name, username, password):
        self.vmx = _vmx_path(vm_name)
        self.username = username
        self.password = password

    def vmrun(self, cmd_args, *args, **kwargs):
        vmrun_cmd = os.getenv(
            'VMRUN',
            '/Applications/VMware Fusion.app/Contents/Library/vmrun')

        cmdlist = ([vmrun_cmd, '-gu', self.username, '-gp', self.password]
                   + list(cmd_args))
        return subprocess.Popen(cmdlist, *args, **kwargs)

    def vmrun_check_output(self, cmd_args):
        proc = self.vmrun(cmd_args, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
        (stdout, stderr) = proc.communicate()
        stdout = (stdout or '').strip()
        stderr = (stderr or '').strip()
        if proc.returncode:
            e = VmException(proc.returncode,
                'vmrun %s failed, returned %d\n\targs were: %s\n%s\n%s'
                % (cmd_args[0], proc.returncode, cmd_args[1:],
                   stdout, stderr))
            raise e
        return (stdout, stderr)

    def _create_temp_file(self):
        """Create a temporary file in the guest and return the filename."""
        (stdout, stderr) = self.vmrun_check_output(
            ['CreateTempfileInGuest', self.vmx])
        return stdout

    def _vmrun(self, *args):
        """Call vmrun_check_output and print output. For command-line use."""
        stdout, stderr = self.vmrun_check_output(
            [args[0], self.vmx] + list(args[1:]))
        if stdout:
            print stdout
        if stderr:
            print >> sys.stderr, stderr

    def delete_file(self, filename):
        """Delete filename in guest."""
        self.vmrun_check_output(['deleteFileInGuest',
                                 self.vmx, filename])

    def delete_directory(self, directoryname):
        """Delete directory in guest."""
        self.vmrun_check_output(['deleteDirectoryInGuest',
                                 self.vmx, directoryname])

    def copy_file_from_guest(self, guest_path, host_path):
        self.vmrun_check_output(['CopyFileFromGuestToHost',
                                 self.vmx,
                                 guest_path, host_path])

    def copy_file_to_guest(self, host_path, guest_path):
        self.vmrun_check_output(['CopyFileFromHostToGuest',
                                 self.vmx,
                                 host_path, guest_path])

    def _run_command(self, command):
        """Run command in CMD and return the output of its last line.

        To collect the output, the command is run at the command prompt
        with output redirected to a temporary file, then the temporary
        is copied over.

        As such, Windows CMD’s quoting rules apply.
        """
        guest_stdout_filename = self._create_temp_file()
        guest_stderr_filename = self._create_temp_file()
        run_exception = None
        try:
            fd, host_temp_filename = tempfile.mkstemp(prefix='vmreflect')
            os.close(fd)
            try:
                try:
                    self.vmrun_check_output(
                        ['runScriptInGuest', self.vmx,
                        '', command + '>' + guest_stdout_filename
                        + ' 2>' + guest_stderr_filename])
                except VmException, e:
                    run_exception = e

                self.copy_file_from_guest(guest_stdout_filename,
                                          host_temp_filename)
                with open(host_temp_filename, 'r') as f:
                    stdout = f.read()

                self.copy_file_from_guest(guest_stderr_filename,
                                          host_temp_filename)
                with open(host_temp_filename, 'r') as f:
                    stderr = f.read()
            finally:
                os.unlink(host_temp_filename)
        finally:
            self.delete_file(guest_stderr_filename)
            self.delete_file(guest_stdout_filename)

        if run_exception:
            raise VmException(run_exception.returncode,
                              run_exception.message
                              + 'stdout:\n' + stdout + '\n'
                              + 'stderr:\n' + stderr)
        return (stdout, stderr)

    def _run_command_no_output(self, command):
        """Run command in CMD, return None, but check the return code."""
        self.vmrun_check_output(['runScriptInGuest', self.vmx, '', command])

    def list_processes(self):
        stdout, stderr = self.vmrun_check_output(
            ['listProcessesInGuest', self.vmx])
        process_list = self._parse_process_list(stdout)
        return process_list

    def kill_process(self, pid):
        self.vmrun_check_output(
            ['killProcessInGuest', self.vmx, str(pid)])

    def _parse_process_list(self, text):
        ret = []
        for line in text.strip().split('\n'):
            if line.startswith('Process list:'):
                continue

            match = _re_processes.match(line)
            if not match:
                raise Exception('no match for', repr(line))
            groups = list(match.groups())
            groups[0] = int(groups[0])
            ret.append(GuestProcess(*groups))
        return ret

def _vmrun(*args, **kwargs):
    cmd = [_VMRUN] + list(args)
    print ' '.join(x.replace(' ', r'\ ') for x in cmd)
    return subprocess.check_call(cmd, **kwargs)

def main():
    from vmreflect.tests import test_config
    parser = argparse.ArgumentParser()
    parser.add_argument('--vm-name', default=test_config.vm_name)
    parser.add_argument('--vm-username', default=test_config.vm_username)
    parser.add_argument('--vm-password', default=test_config.vm_password)
    parser.add_argument('command')
    parser.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    vm = VM(vm_name=args.vm_name, username=args.vm_username,
            password=args.vm_password)
    ret = getattr(vm, args.command)(*args.args)
    if ret:
        print ret

if __name__ == '__main__':
    sys.exit(main())
