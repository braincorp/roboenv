# =============================================================================
# COPYRIGHT 2013 Brain Corporation.
# License under MIT license (see LICENSE file)
# =============================================================================

import os
import pytest
import logging
from robustus.detail import perform_standard_test


@pytest.mark.skipif("'TRAVIS' in os.environ")
def test_ros_installation(tmpdir):
    """
    Install OpenCV and ROS. Check that OpenCV available after ROS activation.
    """
    logging.getLogger().setLevel(logging.INFO)
    tmpdir.chdir()

    imports = ['import rospy',
               'import boto']
    dependencies = ['rosinstall==0.6.30',
                    'rosdep==0.10.23',
                    'rosinstall_generator==0.1.4',
                    'wstool==0.0.4',
                    'patchelf==6fb4cdb',
                    'catkin_pkg',
                    'numpy==1.7.1',
                    'boto==2.19.0']  # boto is just to ensure that non-ROS requirements are also in venv
    
    perform_standard_test('ros==hydro',
                          imports,
                          [],
                          dependencies,
                          postinstall_script='source test_env/bin/activate && source test_env/ros/setup.sh')


if __name__ == '__main__':
    pytest.main('-s %s -n0' % __file__)
