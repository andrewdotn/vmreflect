#!/usr/bin/env python2.7

import os.path

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from distutils.core import Command

class test_cmd(Command):
    description = 'run unit tests'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import unittest
        unittest.main(argv=['-v', 'discover'])

class readme_cmd(Command):
    description = 'generate HTML readme from README.rst'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import os.path
        from docutils.core import publish_file
        basedir = os.path.dirname(__file__)
        with open(os.path.join(basedir, 'README.rst'), 'r') as src:
            with open(os.path.join(basedir, 'README.html'), 'w') as dst:
                publish_file(source=src, destination=dst, writer_name='html')
        try:
            import subprocess
            reload_tab_cmd = 'reload-tab'
            subprocess.check_call(
                [reload_tab_cmd,
                 os.path.abspath(os.path.join(basedir, 'README.html'))])
        except OSError, e:
            print 'Error calling %s: %s' % (reload_tab_cmd, e)


with open(os.path.join(os.path.dirname(__file__), 'README.rst'),
          'r') as readme:
    long_description = readme.read()

setup(cmdclass= {'test': test_cmd, 'readme': readme_cmd},

      name='vmreflect',
      version=__import__('vmreflect').__version__,

      author='Andrew Neitsch',
      author_email='andrew@neitsch.ca',
      url='https://www.github.com/andrewdotn/vmreflect',

      # max 200 characters
      description="automatically tunnel localhost servers on your mac into VMware fusion Windows guests",
      keywords=['proxy', 'reflector', 'virtual machine', 'firewall',
                'port forwarding'],

      # PyPI home page content in reStructuredText format
      long_description=long_description,

      classifiers = [
          # https://pypi.python.org/pypi?:action=list_classifiers
          'Development Status :: 2 - Pre-Alpha',
          'License :: OSI Approved :: BSD License',
          'Environment :: Console',
          'Environment :: MacOS X',
          'Intended Audience :: Developers',
          'Programming Language :: Python :: 2.7',
          'Topic :: System :: Networking',
      ],

      install_requires = [
          'TcpProxyReflector >=0.1.3',
          'path.py >=3.0.1',
      ],

      packages=[
          'vmreflect',
          'vmreflect.tests',
      ],
      scripts=['scripts/vmreflect'],
      package_data={
          'vmreflect': [
              'lib-win32/*.zip',
              'lib-win32/socketclient/socketclient.exe',
          ],
      },
     )
