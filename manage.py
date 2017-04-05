#!/usr/bin/env python
#
#    This file is part of Nebula media asset management.
#
#    Nebula is` free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Nebula is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Nebula. If not, see <http://www.gnu.org/licenses/>.
#

import sys

from nebula import *
from cli import *

logging.user = "Manager"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        critical_error("This command takes at least one argument")
    module = sys.argv[1]
    args = sys.argv[2:]
    if not module in modules:
        critical_error("Unknown module '{}'".format(module))
    modules[module](*args)
