#!/bin/bash
BASEDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )


chmod 755 services

find $BASEDIR/services -type d -exec chmod 775 {} +
find $BASEDIR/services -type f -exec chmod 664 {} +

find $BASEDIR/admin -type d -exec chmod 775 {} +
find $BASEDIR/admin -type f -exec chmod 664 {} +

find $BASEDIR/nx -type d -exec chmod 775 {} +
find $BASEDIR/nx -type f -exec chmod 664 {} +

chmod 755 nebula.py
chmod 755 service.py

chmod 755 vendor/
chmod 755 vendor.sh
chmod 644 vendor.lst

chmod 644 .gitignore
chmod 644 LICENSE
chmod 644 README.md
