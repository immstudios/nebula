#!/bin/bash
BASEDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )


chmod 755 services

find $BASEDIR/services -type d -exec chmod 775 {} +
find $BASEDIR/services -type f -exec chmod 664 {} +

find $BASEDIR/admin -type d -exec chmod 775 {} +
find $BASEDIR/admin -type f -exec chmod 664 {} +

find $BASEDIR/nx -type d -exec chmod 775 {} +
find $BASEDIR/nx -type f -exec chmod 664 {} +


chmod 755 vendor.sh
chmod 644 vendor.lst

chmod 755 nebula.py
chmod 755 adduser.py
chmod 755 fix_permissions.sh
chmod 755 killtree.sh
chmod 755 run_admin.py
chmod 755 run_service.py

chmod 644 .gitignore
chmod 644 LICENSE
chmod 644 README.md
chmod 644 local_settings.json
