#!/bin/bash

#
# Download file from give address and do md5sum
# $1 Downloaded file name 
# $2 Download URL
# $3 md5sum
#
download_file() {
    need_download=1
    if [ -f $1 ]; then
        MD5SUM=$(md5sum "$1" | grep --only-matching -m 1 '^[0-9a-f]*')
        if [ "${MD5SUM}" == "$3" ]; then
            need_download=0
        else
            rm $1
        fi
    fi

    if ((need_download)); then
        wget -O $1 --show-progress $2
        echo "Success download $1"
    fi
    echo "$1 already exists."
}