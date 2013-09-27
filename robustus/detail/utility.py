# =============================================================================
# COPYRIGHT 2013 Brain Corporation.
# License under MIT license (see LICENSE file)
# =============================================================================

import glob
import os
import robustus
import shutil
import subprocess
import logging


def write_file(filename, mode, data):
    """
    write or append string to a file
    :param filename: name of a file to write into
    :param mode: 'w', 'a' or other file open mode
    :param data: string or data to write
    :return: None
    """
    f = open(filename, mode)
    f.write(data)


def cp(mask, dest_dir):
    """
    copy files satisfying mask as unix cp
    :param mask: mask as in unix shell e.g. '*.txt', 'config.ini'
    :param dest_dir: destination directory
    :return: None
    """
    for file in glob.iglob(mask):
        if os.path.isfile(file):
            shutil.copy2(file, dest_dir)


def ln(src, dst, force=False):
    """
    make symlink as unix ln
    :param src: source file
    :param dst: destination file
    :param force: remove destination file
    :return: None
    """
    if force and os.path.exists(dst):
        os.remove(dst)
    os.symlink(src, dst)


def run_shell(command):
    logging.info('Running shell command: %s' % command)
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    output = p.communicate()[0]
    if p.returncode != 0:
        raise Exception('Error running %s, code=%s' % (command, p.returncode))
    return output


def execute_python_expr(env, expr):
    """
    Execute expression using env python interpreter.
    :param env: path to python environment
    :param expr: python expression
    :return: return code
    """
    python_executable = os.path.join(env, 'bin/python')
    if not os.path.isfile(python_executable):
        python_executable = os.path.join(env, 'bin/python27')
    if not os.path.isfile(python_executable):
        raise RuntimeError('can\'t find python executable in %s' % env)
    return subprocess.call([python_executable, '-c', expr])


def check_module_available(env, module):
    """
    check if speicified module is available to specified python environment.
    :param env: path to python environment
    :param module: module name
    :return: True if module available, False otherwise
    """
    return execute_python_expr(env, 'import %s' % module) == 0


def perform_standard_test(package,
                          python_imports=[],
                          package_files=[],
                          dependencies=[],
                          test_env='test_env',
                          test_cache='test_wheelhouse'):
    """
    create env, install package, check package is available,
    remove env, install package without index, check package is available
    :return: None
    """
    # create env and install bullet into it
    test_env = os.path.abspath(test_env)
    test_cache = os.path.abspath(test_cache)

    def check_module():
        for imp in python_imports:
            assert execute_python_expr(test_env, imp) == 0
        for file in package_files:
            assert os.path.isfile(os.path.join(test_env, file))

    def install_dependencies():
        for dep in dependencies:
            robustus.execute(['--env', test_env, 'install', dep])

    robustus.execute(['--cache', test_cache, 'env', test_env])
    install_dependencies()
    robustus.execute(['--env', test_env, 'install', package])
    check_module()
    shutil.rmtree(test_env)

    # install again, but using only cache
    robustus.execute(['--cache', test_cache, 'env', test_env])
    install_dependencies()
    robustus.execute(['--env', test_env, 'install', package, '--no-index'])
    check_module()
    shutil.rmtree(test_env)
    shutil.rmtree(test_cache)
