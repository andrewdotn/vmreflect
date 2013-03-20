# coding: UTF-8

"""
Configuration values for running unit tests.

If the default testing configuration doesn’t match your setup,
you can customize it by setting these environment variables:

    VMREFLECT_TEST_VM_NAME
    VMREFLECT_TEST_USERNAME
    VMREFLECT_TEST_PASSWORD
    VMREFLECT_TEST_VM_DIR

Note that VM_NAME can also be the absolute path to a .vmx file.
"""

import os

__all__ = ['test_config']

class _TestConfig(object):
    """
    """
    pass


test_config = _TestConfig()
test_config.vm_name = os.getenv('VMREFLECT_TEST_VM_NAME', 'ie6')
test_config.vm_username = os.getenv('VMREFLECT_TEST_USERNAME', 'Administrator')
test_config.vm_password = os.getenv('VMREFLECT_TEST_PASSWORD', 'test')
test_config.vm_dir = os.getenv(
    'VMREFLECT_TEST_VM_DIR',
    os.path.expanduser('~/Virtual Machines.localized'))
