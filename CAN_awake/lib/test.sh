# usr/bin/env bash

if [[ $# -lt 1 || $# -gt 1 ]];then
    echo "usage:" $0 "local user password"
    exit

fi

password=$1

echo $password | sudo -S apt-get install libusb-1.0-0

if [ $? -eq 0 ];then
    bus=$(lsusb | grep '3068:0009' |grep -v grep |awk '{print$2}')
    dev=$(lsusb | grep '3068:0009' |grep -v grep |awk '{print$4}')

echo $bus
echo $dev