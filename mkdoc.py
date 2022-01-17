#!/usr/bin/env python3

import os

for service_name in os.listdir("services"):
    if service_name in ["__pycache__", "__init__.py", "README.md"]:
        continue

    _module = __import__("services." + service_name, globals(), locals(), ["Service"])
    Service = _module.Service
    print(Service.__doc__)
