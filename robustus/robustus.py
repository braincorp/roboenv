# =============================================================================
# COPYRIGHT 2013 Brain Corporation.
# License under MIT license (see LICENSE file)
# =============================================================================

import argparse
import importlib
import logging
import os
import subprocess
import sys
from detail import RobustusException, parse_requirement, read_requirement_file, package_str
# for doctests
import detail


class Robustus(object):
    settings_file_path = '.robustus'
    cached_requirements_file_path = 'cached_requirements.txt'
    default_settings = {
        'cache': 'wheelhouse'
    }

    def __init__(self, args):
        """
        Initialize robustus tool. Should be called if sys.executable is in robustus environment
        @param: args - command line arguments
        """
        self.env = os.path.abspath(os.path.join(sys.executable, os.pardir, os.pardir))

        # check if we are in robustus environment
        self.settings_file_path = os.path.join(self.env, Robustus.settings_file_path)
        if not os.path.isfile(self.settings_file_path):
            raise RobustusException('bad robustus environment ' + self.env + ': .robustus settings file not found')
        settings = eval(open(self.settings_file_path).read())
        self.settings = Robustus._override_settings(settings, args)

        self.pip_executable = os.path.join(self.env, 'bin/pip')
        if not os.path.isfile(self.pip_executable):
            raise RobustusException('bad robustus environment ' + self.env + ': pip not found')

        self.easy_install_executable = os.path.join(self.env, 'bin/easy_install')
        if not os.path.isfile(self.easy_install_executable):
            raise RobustusException('bad robustus environment ' + self.env + ': easy_install not found')

        # make cached packages directory if necessary
        self.cache = os.path.join(self.env, self.settings['cache'])
        if not os.path.isdir(self.cache):
            os.mkdir(self.cache)

        # read cached packages
        self.cached_requirements_file_path = os.path.join(self.cache, Robustus.cached_requirements_file_path)
        if os.path.isfile(self.cached_requirements_file_path):
            self.cached_packages = read_requirement_file(self.cached_requirements_file_path)
        else:
            self.cached_packages = []

    @staticmethod
    def _override_settings(settings, args):
        # override settings with command line arguments
        if args.cache is not None:
            settings['cache'] = args.cache
        return settings

    @staticmethod
    def env(args):
        """
        Create robustus environment.
        @param args: command line arguments
        """
        # create virtualenv
        env = args.init_args[-1]
        logging.info('Creating virtualenv')
        subprocess.call(['virtualenv'] + args.init_args)

        python_executable = os.path.abspath(os.path.join(env, 'bin/python'))
        pip_executable = os.path.abspath(os.path.join(env, 'bin/pip'))
        easy_install_executable = os.path.abspath(os.path.join(env, 'bin/easy_install'))

        # check for katipo assembly file
        katipo_assembly = '.katipo/assembly'
        if os.path.isfile(katipo_assembly):
            assembly_opts = eval(open(katipo_assembly).read())
            # add search path for katipo repos
            with open('%s/lib/python2.7/site-packages/katipo_repos.pth' % env, 'w') as f:
                for repo in assembly_opts.repos:
                    f.write('%s/%s' % (os.getcwd(), repo['path']))

        # http://wheel.readthedocs.org/en/latest/
        # wheel is binary packager for python/pip
        # we store all packages in binary wheel somewhere on the PC to avoid recompilation of packages

        # wheel needs pip 1.4, at the moment of writing it was development version
        # and we can't reinstall pip after virtualenv activation
        subprocess.call([pip_executable,
                         'install',
                         '-e',
                         'git+https://github.com/pypa/pip.git@978662b08b118bbeaae5aba57c823090b1c3b3ee#egg=pip'])

        # install requirements for wheel
        # need to uninstall distribute, because they conflict with setuptools
        subprocess.call([pip_executable, 'uninstall', 'distribute'])
        subprocess.call([pip_executable, 'install', 'https://bitbucket.org/pypa/setuptools/downloads/setuptools-0.8b3.tar.gz'])
        subprocess.call([pip_executable, 'install', 'wheel==0.16.0'])

        # adding BLAS and LAPACK libraries for CentOS installation
        if os.path.isfile('/usr/lib64/libblas.so.3'):
            logging.info('Linking libblas to venv')
            blas_so = os.path.join(env, 'lib64/libblas.so')
            os.symlink('/usr/lib64/libblas.so.3', blas_so)
            os.environ['BLAS'] = blas_so

        if os.path.isfile('/usr/lib64/liblapack.so.3'):
            logging.info('Linking liblapack to venv')
            lapack_so = os.path.join(env, 'lib64/liblapack.so')
            os.symlink('/usr/lib64/liblapack.so.3', lapack_so)
            os.environ['LAPACK'] = blas_so

        # linking PyQt for CentOS installation
        if os.path.isfile('/usr/lib64/python2.7/site-packages/PyQt4/QtCore.so'):
            logging.info('Linking qt for centos matplotlib backend')
            os.symlink('/usr/lib64/python2.7/site-packages/sip.so', os.path.join(env, 'lib/python2.7/site-packages/sip.so'))
            os.symlink('/usr/lib64/python2.7/site-packages/PyQt4', os.path.join(env, 'lib/python2.7/site-packages/PyQt4'))

        # readline must be come before everything else
        subprocess.call([easy_install_executable, '-q', 'readline==6.2.2'])

        # compose settings file
        settings = Robustus._override_settings(Robustus.default_settings, args)
        with open(os.path.join(env, Robustus.settings_file_path), 'w') as file:
            file.write(str(settings))

        # install robustus
        cwd = os.getcwd()
        script_dir = os.path.dirname(os.path.realpath(__file__))
        setup_dir = os.path.abspath(os.path.join(script_dir, os.path.pardir))
        os.chdir(setup_dir)
        subprocess.call([python_executable, 'setup.py', 'install'])
        os.chdir(cwd)

    def install_through_wheeling(self, package, version):
        """
        Check if package cache already contains package of specified version, if so install it.
        Otherwise make a wheel and put it into cache.
        Hope manual check for requirements file won't be necessary, waiting for pip 1.5 https://github.com/pypa/pip/issues/855
        :param package: package name
        :param version: package version string
        :return: None
        """
        pstr = package_str(package, version)

        # if wheelhouse doesn't contain necessary requirement - make a wheel
        if (package, version) not in self.cached_packages:
            logging.info('Wheel not found, downloading package')
            subprocess.call([self.pip_executable,
                             'install',
                             '--download',
                             self.cache,
                             pstr])
            logging.info('Building wheel')
            subprocess.call([self.pip_executable,
                             'wheel',
                             '--no-index',
                             '--find-links=%s' % self.cache,
                             '--wheel-dir=%s' % self.cache,
                             pstr])
            logging.info('Done')

        # install from prebuilt wheel
        logging.info('Installing package from wheel')
        subprocess.call([self.pip_executable,
                         'install',
                         '--no-index',
                         '--use-wheel',
                         '--find-links=%s' % self.cache,
                         pstr])

        return True

    def _flush_cached_packages(self):
        # write cached packages list to cache requirements file
        f = open(self.cached_requirements_file_path, 'w')
        for package, version in self.cached_packages:
            f.write('%s\n' % package_str(package, version))

    def install_package(self, package, version):
        pstr = package_str(package, version)
        logging.info('Installing ' + pstr)
        try:
            # try to use specific install script
            install_module = importlib.import_module('robustus.detail.install_%s' % package)
            package_installed = install_module.install(self, version)
        except ImportError:
            package_installed = self.install_through_wheeling(package, version)

        if package_installed:
            self.cached_packages.append((package, version))
            self._flush_cached_packages()  # make sure requirements are saved in case of crash
            logging.info('Done')
        else:
            logging.error('Failed to install ' + pstr)

    def install(self, args):
        # construct requirements list
        requirements = []
        for requirement in args.packages:
            requirements.append(parse_requirement(requirement))
        if args.requirement:
            for requirement_file in args.requirement:
                requirements += read_requirement_file(requirement_file)
        if len(requirements) == 0:
            raise RobustusException('You must give at least one requirement to install (see "robustus install -h")')

        # install
        for package, version in requirements:
            self.install_package(package, version)

    def freeze(self, args):
        for package, version in self.cached_packages:
            print package_str(package, version)

    def download_cache(self, args):
        """
        Download wheels (binary package archives) from wheelhouse_url and unzip them in wheelhouse
        @param wheelhouse: directory to store wheels
        @param wheelhouse_url: url where to grap wheels archive
        @return: None
        """
        cwd = os.getcwd()
        os.chdir(wheelhouse)
        try:
            wheelhouse_archive = wheelhouse_url.split('/')[-1]
            logging.info('Downloading ' + wheelhouse_url)
            # with -c option wget won't download file if it has been already downloaded
            # and continue if it was partially downloaded
            subprocess.call(['wget', '-c', wheelhouse_url])
            logging.info('Unzipping')
            subprocess.call(['tar', 'xjvf', wheelhouse_archive])
            logging.info('Done')
        except Exception as exc:
            logging.error(exc.message)
        os.chdir(cwd)

    def upload_cache(self, args):
        self._read_settings()
        pass


def execute(argv):
    parser = argparse.ArgumentParser(description='Tool to make and configure python virtualenv,'
                                                 'setup necessary packages and cache them if necessary.',
                                     prog='robustus')
    parser.add_argument('--cache', default='wheelhouse', help='binary package cache directory')
    subparsers = parser.add_subparsers(help='robustus commands')

    env_parser = subparsers.add_parser('env', help='make robustus')
    env_parser.add_argument('init_args',
                             nargs='+',
                             default=['.env', '--prompt', 'robustus'],
                             help='virtualenv arguments')
    env_parser.set_defaults(func=Robustus.env)

    install_parser = subparsers.add_parser('install', help='install packages')
    install_parser.add_argument('-r', '--requirement',
                                action='append',
                                help='install all the packages listed in the given'
                                     'requirements file, this option can be used multiple times.')
    install_parser.add_argument('packages',
                                nargs='*',
                                help='packages to install in format <package name>==version')
    install_parser.set_defaults(func=Robustus.install)

    freeze_parser = subparsers.add_parser('freeze', help='list cached binary packages')
    freeze_parser.set_defaults(func=Robustus.freeze)

    download_cache_parser = subparsers.add_parser('download_cache', help='download cache from server or path')
    download_cache_parser.add_argument('url', help='cache url (directory, *.tar.gz, *.tar.bz or *.zip)')
    download_cache_parser.set_defaults(func=Robustus.download_cache)

    upload_cache_parser = subparsers.add_parser('upload_cache', help='upload cache to server or path')
    upload_cache_parser.add_argument('url', help='cache url (directory, *.tar.gz, *.tar.bz or *.zip)')
    upload_cache_parser.set_defaults(func=Robustus.upload_cache)

    args = parser.parse_args(argv)
    if args.func == Robustus.env:
        Robustus.env(args)
    else:
        try:
            robustus = Robustus(args)
            args.func(robustus, args)
        except RobustusException as exc:
            logging.critical(exc.message)
            exit(1)


if __name__ == '__main__':
    execute(sys.argv[1:])