#!/bin/bash

MATERIALIZE_VERSION="0.97.5"


BASEDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TEMPDIR=/tmp/$(basename "${BASH_SOURCE[0]}")
MATERIALIZE_URL="http://materializecss.com/bin/materialize-src-v${MATERIALIZE_VERSION}.zip"
ZIP_PATH="${BASEDIR}/materialize.zip"

function error_exit {
    printf "\n\033[0;31mInstallation failed\033[0m\n"
    cd $BASEDIR
    exit 1
}

function finished {
    printf "\n\033[0;92mInstallation completed\033[0m\n"
    cd $BASEDIR
    exit 0
}



wget $MATERIALIZE_URL -O $ZIP_PATH  || exit 1
unzip $ZIP_PATH
