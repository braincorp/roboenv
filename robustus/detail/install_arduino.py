

# =============================================================================
# COPYRIGHT 2014 Brain Corporation.
# License under MIT license (see LICENSE file)
# =============================================================================

import logging
import os
import sys
from utility import ln
from requirement import RequirementException


def install(robustus, requirement_specifier, rob_file, ignore_index):
    if sys.platform.startswith('darwin'):
        if os.path.isfile('somewhere')
            logging.info('Linking arduino on macos')
            ln('something')
        else:
        logging.info('Skipping installation of arduino on mac. look here:  http://arduino.cc/en/guide/macOSX ')
        # https://groups.google.com/forum/#!topic/drones-discuss/x41j32MM4Ck
    else:
        if os.path.isfile('somewhere')
            logging.info('Linking arduino on linux')
            ln('something')
        else:
            raise RequirementException('System-wide Arduino is missing, run: sudo apt-get update && sudo apt-get install arduino arduino-core')