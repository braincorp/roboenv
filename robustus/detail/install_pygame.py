# =============================================================================
# COPYRIGHT 2013 Brain Corporation.
# License under MIT license (see LICENSE file)
# =============================================================================

import glob
import logging
import os
from requirement import RequirementException
from utility import unpack, run_shell, safe_remove
import shutil
import subprocess
import sys


def install(robustus, requirement_specifier, rob_file, ignore_index):
    if requirement_specifier.version != '1.9.1' and requirement_specifier.version != 'bc1':
        raise RequirementException('can only install pygame 1.9.1/bc1')

    if sys.platform.startswith('darwin'):
        subprocess.call([robustus.pip_executable, 'install', '-U', 'pyobjc-core'])
        subprocess.call([robustus.pip_executable, 'install', '-U', 'pyobjc'])

        print "#####################"
        print "You are on OSX"
        print "Make sure you have SDL installed"
        print "The easiest way to achieve this is using brew:"
        print "   brew install sdl sdl_image sdl_mixer sdl_ttf portmidi"
        print "#####################"

    pygame_cache_dir = os.path.join(robustus.cache, 'pygame-%s' % requirement_specifier.version)

    def in_cache():
        return os.path.isfile(os.path.join(pygame_cache_dir, 'pygame/__init__.py'))

    if not in_cache() and not ignore_index:
        cwd = os.getcwd()
        pygame_archive = None
        pygame_archive_name = None
        try:
            pygame_archive = robustus.download('pygame', requirement_specifier.version)
            pygame_archive_name = unpack(pygame_archive)

            # Pygame asks to proceed without smpeg,
            # megahack to avoid asking to continue
            logging.info('Builduing pygame')
            os.chdir(pygame_archive_name)
            config_unix_py = 'config_unix.py'
            config_unix_py_source = open(config_unix_py).read()
            with open(config_unix_py, 'w') as f:
                f.write(config_unix_py_source.replace('def confirm(message):',
                                                      'def confirm(message):\n'
                                                      '    return 1\n'))

            # one more megahack to avoid problem with linux/videodev.h
            # http://stackoverflow.com/questions/5842235/linux-videodev-h-no-such-file-or-directory-opencv-on-ubuntu-11-04
            camera_h = 'src/camera.h'
            camera_h_source = open(camera_h).read()
            with open(camera_h, 'w') as f:
                f.write(camera_h_source.replace('linux/videodev.h',
                                                'libv4l1-videodev.h'))

            run_shell([robustus.python_executable, 'setup.py', 'build'],
                      verbose=robustus.settings['verbosity'] >= 1)

            # under build there will be platform specific dir, e.g. lib.linux-x86_64-2.7
            # inside pygame will reside, copy it to robustus cache
            glob_res = glob.glob('build/lib*')
            if len(glob_res) == 0:
                raise RequirementException('failed to build pygame-%s' % requirement_specifier.version)
            pygame_dir = os.path.join(os.getcwd(), glob_res[0], 'pygame')
            if os.path.isdir(pygame_cache_dir):
                shutil.rmtree(pygame_cache_dir)
            os.mkdir(pygame_cache_dir)
            shutil.copytree(pygame_dir, os.path.join(pygame_cache_dir, 'pygame'))
        finally:
            safe_remove(pygame_archive)
            safe_remove(pygame_archive_name)
            os.chdir(cwd)

    if in_cache():
        # install pygame to virtualenv
        pygame_install_dir = os.path.join(robustus.env, 'lib/python2.7/site-packages')
        installation_path = os.path.join(pygame_install_dir, 'pygame')
        if os.path.exists(installation_path):
            shutil.rmtree(installation_path)
        shutil.copytree(os.path.join(pygame_cache_dir, 'pygame'),
                        installation_path)
    else:
        raise RequirementException('can\'t find pygame-%s in robustus cache' % requirement_specifier.version)
