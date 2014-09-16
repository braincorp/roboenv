# =============================================================================
# COPYRIGHT 2013 Brain Corporation.
# License under MIT license (see LICENSE file)
# =============================================================================

import logging
import os
from requirement import RequirementException
from utility import unpack, safe_remove, run_shell, ln 
import shutil
import subprocess


def install(robustus, requirement_specifier, rob_file, ignore_index):
    cwd = os.getcwd()
    os.chdir(robustus.cache)

    install_dir = os.path.join(robustus.cache, 'protobuf-%s' % requirement_specifier.version)
    if not os.path.isdir(install_dir) and not ignore_index:
        archive_name = 'protobuf-%s.tar.gz' % requirement_specifier.version
        subprocess.call(['wget', '-c', 'https://protobuf.googlecode.com/svn/rc/%s' % (archive_name,)])
        subprocess.call(['tar', 'zxvf', archive_name])

        # move sources to a folder in order to use a clean name for installation
        src_dir = 'protobuf-%s' % requirement_specifier.version
        shutil.move(src_dir, src_dir+'_src')
        src_dir += '_src'

        os.chdir(src_dir)
        os.mkdir(install_dir)

        subprocess.call(['./configure', '--disable-shared', '--prefix', install_dir])
        subprocess.call('make', shell=True)
        subprocess.call('make install', shell=True)
        os.chdir(robustus.cache)
        shutil.rmtree(src_dir)

    venv_install_folder = os.path.join(robustus.env, 'protobuf')
    if os.path.exists(venv_install_folder):
        shutil.rmtree(venv_install_folder) 
    shutil.copytree(install_dir, venv_install_folder)
    executable_path = os.path.join(install_dir, 'bin', 'protoc')
    ln(executable_path, os.path.join(robustus.env, 'bin', 'protoc'), force=True)
    os.chdir(cwd)

    # now install python part
    robustus.install_through_wheeling(requirement_specifier, rob_file, ignore_index)
