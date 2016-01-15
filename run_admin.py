#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import time

##
# Env setup
##

if sys.version_info[:2] < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf-8')

nebula_root = os.path.abspath(os.path.split(sys.argv[0])[0])

##
# Vendor imports
##

vendor_dir = os.path.join(nebula_root, "vendor")
if os.path.exists(vendor_dir):
    for pname in os.listdir(vendor_dir):
        pname = os.path.join(vendor_dir, pname)
        pname = os.path.abspath(pname)
        if not pname in sys.path:
            sys.path.insert(0, pname)

from nx import *

config["nebula_root"] = nebula_root
config["user"] = "Admin"

from admin import Admin

if __name__ == "__main__":
    admin = Admin(blocking=True)
