# =============================================================================
# COPYRIGHT 2014 Brain Corporation.
# License under MIT license (see LICENSE file)
# =============================================================================

import logging
import os
from utility import unpack, safe_remove, run_shell, fix_rpath, ln, cp
from requirement import RequirementException


def install(robustus, requirement_specifier, rob_file, ignore_index):
    # check if already installed
    sphinxbase = os.path.join(robustus.env, 'lib/python2.7/site-packages/sphinxbase.so')
    if os.path.isfile(sphinxbase):
        return

    cwd = os.getcwd()
    archive = None
    try:
        # build in cache
        os.chdir(robustus.cache)
        build_dir = os.path.join(robustus.cache, 'sphinxbase-%s' % requirement_specifier.version)
        if not os.path.isfile(os.path.join(build_dir, 'configure')):
            archive = robustus.download('sphinxbase', requirement_specifier.version)
            unpack(archive)

        # unfortunately we can't cache sphinxbase, it has to be rebuild after reconfigure
        logging.info('Building sphinxbase')
        os.chdir(build_dir)

        # link python-config from system-wide installation, sphinxbase configure requires it
        python_config = os.path.join(robustus.env, 'bin/python-config')
        if not os.path.isfile(python_config):
            ln('/usr/bin/python-config', python_config)

        retcode = run_shell('./configure'
                            + (' --prefix=%s' % robustus.env)
                            + (' --with-python=%s' % os.path.join(robustus.env, 'bin/python')),
                            shell=True,
                            verbose=robustus.settings['verbosity'] >= 1)
        if retcode != 0:
            raise RequirementException('sphinxbase configure failed')

        retcode = run_shell('make clean && make', shell=True, verbose=robustus.settings['verbosity'] >= 1)
        if retcode != 0:
            raise RequirementException('sphinxbase build failed')

        logging.info('Installing sphinxbase into virtualenv')
        retcode = run_shell('make install', shell=True, verbose=robustus.settings['verbosity'] >= 1)
        if retcode != 0:
            raise RequirementException('sphinxbase install failed')

        fix_rpath(robustus, robustus.env, sphinxbase, os.path.join(robustus.env, 'lib'))
    except RequirementException:
        safe_remove(build_dir)
    finally:
        if archive is not None:
            safe_remove(archive)
        os.chdir(cwd)
