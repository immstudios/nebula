#!/bin/bash

BASEDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
VENDORDIR=$BASEDIR"/vendor"
VENDORLST=$BASEDIR"/vendor.lst"

if [ ! -f $VENDORLST ]; then
    echo "Vendor modules list (vendor.lst) not found"
    exit 1
fi

if [ ! -d $VENDORDIR ]; then
    mkdir $VENDORDIR
fi


while read repo; do

    if [ -z "$repo" ]; then
        continue 
    fi

    RNAME=`basename $repo`
    DNAME=$VENDORDIR"/"$RNAME

    if [ -d $DNAME ] && [ -d $DNAME"/.git" ]; then
        echo ""
        echo "Updating module $RNAME"
        cd $DNAME
        git pull
    elif [ ! -d $DNAME ]; then
        echo ""
        echo "Downloading module $RNAME"
        cd $VENDORDIR
        git clone $repo
    fi

done < $VENDORLST

