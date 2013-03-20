"""
Unit tests for the virtual machine API
"""

import unittest

from path import path

from vmreflect.tests import test_config
from vmreflect.utils import get_random_string
from vmreflect import vmapi

class TestVmApi(unittest.TestCase):

    def setUp(self):
        self.vm = vmapi.VM(vm_name=test_config.vm_name,
                           username=test_config.vm_username,
                           password=test_config.vm_password)

    def test_run_script(self):
        (out, err) = self.vm._run_command('echo hi')
        self.assertEquals('hi\r\n', out)

    def test_parse_processes(self):
        ret = self.vm._parse_process_list(_SAMPLE_PROCESSES)
        self.assertEquals(len(ret), 4)
        self.assertEquals(ret[0].pid, 1624)
        self.assertIn('wuauc', ret[0].cmd)
        self.assertIn('Admin', ret[3].owner)

        ret = self.vm._parse_process_list(_SAMPLE_PROCESSES_2)
        self.assertEquals(len(ret), 2)

_SAMPLE_PROCESSES = r"""
pid=1624, owner=ADMIN\Administrator, cmd="C:\WINDOWS\system32\wuauclt.exe"
pid=1232, owner=ADMIN\Administrator, cmd="C:\WINDOWS\system32\notepad.exe" 
pid=1420, owner=ADMIN\Administrator, cmd="C:\WINDOWS\system32\cmd.exe" 
pid=312, owner=ADMIN\Administrator, cmd=C:\DOCUME~1\ADMINI~1\LOCALS~1\Temp\vmware147.d\tcpr.exe  C:\DOCUME~1\ADMINI~1\LOCALS~1\Temp\vmware147.d\tcpr.ini -s
"""

_SAMPLE_PROCESSES_2 = r"""
Process list: 12
pid=1624, owner=ADMIN\Administrator, cmd="C:\WINDOWS\system32\wuauclt.exe"
pid=1232, owner=ADMIN\Administrator, cmd="C:\WINDOWS\system32\notepad.exe" 
"""

class TestVmApiFailures(unittest.TestCase):

    def test_exception_on_bad_username_password(self):
        self.vm = vmapi.VM(vm_name=test_config.vm_name,
            username=get_random_string(), password=get_random_string())
        self.assertRaises(Exception, lambda: self.vm._create_temp_file())

class TestVmxPath(unittest.TestCase):

    def setUp(self):
        self.vmx_path = vmapi._vmx_path(test_config.vm_name)
        self.assertTrue(self.vmx_path.isfile())

    def test_bare_vm_name(self):
        """Tests _vmx_path('ie6')"""
        self.assertEquals(self.vmx_path,
                          vmapi._vmx_path(test_config.vm_name))

    def test_full_vmx_path(self):
        """Tests _vmx_path('/Users/.../ie6.vmwarevm/ie6.vmx')"""
        self.assertEquals(self.vmx_path, vmapi._vmx_path(self.vmx_path))

    def test_vm_folder(self):
        """Tests _vmx_path('/Users/.../ie6.vmwarevm')"""
        self.assertEquals(self.vmx_path,
                          vmapi._vmx_path(
                              path(test_config.vm_dir)
                              .joinpath(test_config.vm_name + '.vmwarevm')))

    def test_vm_bare_folder(self):
        """Tests _vmx_path('/Users/.../ie6')"""
        self.assertEquals(self.vmx_path,
                          vmapi._vmx_path(
                              path(test_config.vm_dir)
                              .joinpath(test_config.vm_name)))
