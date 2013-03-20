#!/usr/bin/env python2.7

import os.path
import subprocess

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from distutils.core import Command
from distutils.command.build import build as orig_build_cmd

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
        from path import path
        from docutils.core import publish_file

        basedir = path(__file__).dirname()
        rst_path = basedir.joinpath('README.rst')
        html_path = basedir.joinpath('README.html')
        if html_path.isfile() and html_path.mtime >= rst_path.mtime:
            return

        with open(rst_path, 'r') as src:
            with open(html_path, 'w') as dst:
                publish_file(source=src, destination=dst, writer_name='html')
        try:
            reload_tab_cmd = 'reload-tab'
            subprocess.check_call([reload_tab_cmd, html_path])
        except OSError, e:
            print 'Error calling %s: %s' % (reload_tab_cmd, e)

class build_aux_cmd(Command):
    description = 'call make in vmreflect/lib-win32/socketclient'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from path import path
        subprocess.check_call(
            ['make'], cwd=(path(__file__).dirname()
                           .joinpath('vmreflect/lib-win32/socketclient')))

class my_build_cmd(orig_build_cmd):
    pass
my_build_cmd.sub_commands.extend([
    ('build_aux', lambda x: True),
    ('readme', lambda x: True),
])


with open(os.path.join(os.path.dirname(__file__), 'README.rst'),
          'r') as readme:

    # The image in README.rst causes it to show up as plain text on pypi.
    # These magic comments omit that part of the long_description.
    src_lines = []
    copy = True
    for line in readme.readlines():
        if line.startswith(".. comment: begin omit from long_description"):
            copy=False

        if copy:
            src_lines.append(line)

        if line.startswith(".. comment: end omit from long_description"):
            copy=True
    long_description = ''.join(src_lines)

setup(cmdclass={'test': test_cmd,
                'readme': readme_cmd,
                'build': my_build_cmd,
                'build_aux': build_aux_cmd,
               },

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
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: BSD License',
          'Environment :: Console',
          'Environment :: MacOS X',
          'Operating System :: MacOS :: MacOS X',
          'Intended Audience :: Developers',
          'Programming Language :: Python :: 2.7',
          'Topic :: System :: Networking',
      ],

      install_requires = [
          'TcpProxyReflector >=0.1.3',
          'path.py >=3.0.1',
          'pefile >= 1.2.10',
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
