# =============================================================================
# COPYRIGHT 2013 Brain Corporation.
# License under MIT license (see LICENSE file)
# =============================================================================

import logging
import os
from requirement import RequirementException
from utility import cp, write_file
import shutil
import subprocess
import sys


def install(robustus, requirement_specifier, rob_file):
    if requirement_specifier.version != '1.8.1':
        raise RequirementException('can only install panda3d 1.8.1')

    panda_install_dir = os.path.join(robustus.cache, 'panda3d-%s' % requirement_specifier.version)
    if not os.path.isfile(os.path.join(panda_install_dir, 'lib/panda3d.py')):
        logging.info('Downloading panda3d')
        panda3d_archive_name = 'panda3d-1.8.1'
        panda3d_tgz = panda3d_archive_name + '.tar.gz'
        url = 'https://www.panda3d.org/download/panda3d-1.8.1/' + panda3d_tgz
        subprocess.call(['wget', '-c', url, '-O', panda3d_tgz])

        logging.info('Unpacking panda3d')
        subprocess.call(['tar', 'xvzf', panda3d_tgz])

        logging.info('Builduing panda3d')
        cwd = os.getcwd()
        os.chdir(panda3d_archive_name)

        make_panda_options = ['--nothing',
                              '--use-python',
                              '--use-direct',
                              '--use-bullet',
                              '--use-zlib',
                              '--use-png',
                              '--use-jpeg',
                              '--use-tiff',
                              '--use-freetype',
                              '--use-x11',
                              '--use-gl',
                              '--use-nvidiacg',
                              '--use-pandatool',
                              '--use-tinydisplay',
                              '--threads', '4']
        if sys.platform.startswith('darwin'):
            make_panda_options += ' --use-cocoa'
            os.environ['CC'] = 'gcc'
            os.environ['CXX'] = 'g++'

        subprocess.call([robustus.python_executable, 'makepanda/makepanda.py'] + make_panda_options)

        # copy panda3d files to cache
        shutil.rmtree(panda_install_dir, ignore_errors=True)
        os.mkdir(panda_install_dir)
        subprocess.call('cp -R built/lib %s' % panda_install_dir, shell=True)
        subprocess.call('cp -R built/bin %s' % panda_install_dir, shell=True)
        subprocess.call('cp -R built/include %s' % panda_install_dir, shell=True)
        subprocess.call('cp -R built/direct %s' % panda_install_dir, shell=True)
        subprocess.call('cp -R built/pandac %s' % panda_install_dir, shell=True)
        subprocess.call('cp -R built/models %s' % panda_install_dir, shell=True)
        subprocess.call('cp -R built/etc %s' % panda_install_dir, shell=True)

        os.chdir(os.path.pardir)
        shutil.rmtree(panda3d_archive_name)
        os.remove(panda3d_tgz)

    # install panda3d to virtualenv
    subprocess.call('cp %s/bin/* %s/bin' % (panda_install_dir, robustus.env), shell=True)
    incdir = os.path.join(robustus.env, 'include/panda3d')
    shutil.rmtree(incdir, ignore_errors=True)
    os.mkdir(incdir)
    subprocess.call('cp -r -u -p %s/include/* %s/' % (panda_install_dir, incdir), shell=True)
    libdir = os.path.join(robustus.env, 'lib/panda3d')
    shutil.rmtree(libdir, ignore_errors=True)
    os.mkdir(libdir)
    subprocess.call('cp -r -u -p %s/lib/* %s/' % (panda_install_dir, libdir), shell=True)
    env_sharedir = os.path.join(robustus.env, 'share')
    if not os.path.isdir(env_sharedir):
        os.mkdir(env_sharedir)
    sharedir = os.path.join(env_sharedir, 'panda3d')
    shutil.rmtree(sharedir, ignore_errors=True)
    os.mkdir(sharedir)
    subprocess.call('cp -r -u -p %s/direct/* %s/' % (panda_install_dir, sharedir), shell=True)
    subprocess.call('cp -r -u -p %s/models/* %s/' % (panda_install_dir, sharedir), shell=True)
    subprocess.call('cp -r -u -p %s/pandac/* %s/' % (panda_install_dir, sharedir), shell=True)
    subprocess.call('cp -u %s/lib/panda3d.py %s/' % (panda_install_dir, sharedir), shell=True)
    env_etcdir = os.path.join(robustus.env, 'etc')
    if not os.path.isdir(env_etcdir):
        os.mkdir(env_etcdir)
    etcdir = os.path.join(env_etcdir, 'panda3d')
    shutil.rmtree(etcdir, ignore_errors=True)
    os.mkdir(etcdir)
    subprocess.call('cp -r -u -p %s/etc/* %s/' % (panda_install_dir, etcdir), shell=True)

    write_file(os.path.join(robustus.env, 'lib/python2.7/site-packages/panda3d.pth'),
               'w',
               '%s/share/panda3d\n%s/share/lib/panda3d' % (robustus.env, robustus.env))

    if sys.platform.startswith('darwin'):
        os.environ['DYLD_LIBRARY_PATH'] += ':' + libdir
    else:
        os.environ['LD_LIBRARY_PATH'] += ':' + libdir
    os.environ['PANDA_PRC_DIR'] = etcdir