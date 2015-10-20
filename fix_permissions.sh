#!/bin/bash
BASEDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

chmod 755 mam 
chmod 644 mam/*.py

chmod 755 nebula.py
chmod 755 run_service.py

chmod 755 vendor/
chmod 755 vendor.sh
chmod 644 vendor.lst

chmod 644 .gitignore
chmod 644 LICENSE
chmod 644 README.md
