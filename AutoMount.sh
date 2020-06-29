#!/bin/bash
export LC_ALL=en_US

URL="https://raw.githubusercontent.com/cgkings/automount/master/AutoMount.py"

function cleanup {
    rm -rf /root/AutoTools.sh
    rm -rf /root/AutoToolsWget.sh
    rm -rf /root/AutoMount.*
    rm -rf /etc/motd
}

function install_py2 {
    if [ -f "/etc/redhat-release" ]; then
        yum install python2 -y
    else
        apt update
        apt install python -y
    fi
}

function run_script {
    cd /root
    wget -O AutoMount.py ${URL}
    chmod 755 AutoMount.py
    ./AutoMount.py
    if [ "$?" != "0" ]; then
        exit -1
    fi
}

function root_check {
    # Check if user is root
    if [ $(id -u) != "0"  ]; then
        __echo "You must be root to run this script, use sudo $0"
        exit -1
    fi
}

root_check
install_py2
run_script
cleanup
