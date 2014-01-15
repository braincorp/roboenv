# =============================================================================
# COPYRIGHT 2013 Brain Corporation.
# License under MIT license (see LICENSE file)
# =============================================================================

import logging
import os
from requirement import RequirementException
import shutil
import sys
from utility import run_shell, add_source_ref, check_module_available
import os


def _make_overlay_folder(robustus, requirement_specifier):
    overlay_folder = os.path.join(robustus.cache,
                                  requirement_specifier.rob_filename()[0:-3])
    if not os.path.isdir(overlay_folder):
        os.mkdir(overlay_folder)
    return overlay_folder


def _get_source(package):
    """Download source code for package."""
    logging.info('Obtaining ROS package %s' % package)
    # Break the git spec into components
    if '#' in package:
        origin, branch = package.split('#')
        branch_str = '--branch ' + branch
    else:
        origin = package
        branch = None
        branch_str = ''

    run_shell('git clone "%s" %s' % (origin, branch_str))


def _get_sources(packages):
    os.chdir('src')
    for p in packages:
        _get_source(p)
    os.chdir('..')


def _opencv_cmake_path(robustus):
    """Determine the path to the OpenCV cmake file (or None if
    OpenCV is not installed)."""

    found = None
    for p in robustus.cached_packages:
        if p.name == 'opencv':
            if found is not None:
                raise RequirementException('multiple opencv versions found')
            found = p

    if found is None:
        logging.info('No OpenCV found - ROS overlay will build without OpenCV')
        return None

    cmake_path = os.path.join(robustus.cache, 'OpenCV-%s' % found.version,
                              'share', 'OpenCV')
    logging.info('OpenCV Cmake path is %s' % cmake_path)
    return cmake_path


def _ros_dep(env_source, robustus):
    """Run rosdep to install any dependencies (or error)."""

    logging.info('Running rosdep to install dependencies')
    rosdep = os.path.join(robustus.env, 'bin/rosdep')
    retcode = run_shell(rosdep +
                        ' install -r --from-paths src --ignore-src -y',
                        verbose=robustus.settings['verbosity'] >= 1)
    if retcode != 0:
        raise RequirementException('Failed to update ROS dependencies')


def install(robustus, requirement_specifier, rob_file, ignore_index):
    assert requirement_specifier.name == 'ros_overlay'
    package_desc = requirement_specifier.version
    packages = package_desc.split(',')

    if not check_module_available(robustus.env, 'rospy'):
        raise RequirementException('ROS must be installed prior to any ros nodes')

    try:
        cwd = os.getcwd()
        overlay_folder = _make_overlay_folder(robustus, requirement_specifier)
        os.chdir(overlay_folder)

        logging.info('Building ros overlay in %s with versions %s' % (overlay_folder,
                                                                      str(packages)))

        os.mkdir(os.path.join(overlay_folder, 'src'))
        _get_sources(packages)

        env_source = os.path.join(robustus.env, 'bin/activate')
        _ros_dep(env_source, robustus)

        opencv_cmake_dir = _opencv_cmake_path(robustus)
        ret_code = run_shell('. "%s" && export OpenCV_DIR="%s" && catkin_make_isolated' %
                             (env_source, opencv_cmake_dir) +
                             ' --force-cmake --cmake-args -DCATKIN_ENABLE_TESTING=1',
                                verbose=robustus.settings['verbosity'] >= 1)
        if ret_code != 0:
            raise RequirementException('Error during catkin_make')



    finally:
        os.chdir(cwd)
        if robustus.settings['debug']:
            logging.info('Not removing folder %s due to debug flag.' % overlay_folder)
        else:
            shutil.rmtree(overlay_folder)
