#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys

if sys.version_info[:2] < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf-8')

#
# vendor imports
#

for pname in os.listdir("vendor"):
    pname = os.path.join("vendor", pname)
    pname = os.path.abspath(pname)
    if not pname in sys.path:
        sys.path.append(pname)  

from nxtools import *
from mam import *

logging.user = "Nebula"


#
# Nebula dispatch
#


def start_nebula():
    logging.user = "Dispatch"
    logging.info("Starting nebula")

#
# Start dispatch only if this script is executed (not imported)
#


if __name__ == "__main__":
    start_nebula()
