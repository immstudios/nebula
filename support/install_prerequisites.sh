#!/bin/bash

function install_node {
    echo "Installing Nebula node prerequisites"
    apt install -y libmemcached-dev python3-pip cifs-utils zlib1g-dev python3-dev build-essential
    pip3 install -r ../requirements.txt
}

install_node || exit 1
