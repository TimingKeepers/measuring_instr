#!/usr/bin/env bash
# Script to install the dependencies of the repo

rule_file=/etc/udev/rules.d/usbtmc.rules

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

# Python 2.7 could be used with a few changes in code...
p3=`which python3`
if [ "x$p3" == "x" ]; then
    echo -e "\e[1;31mPython3 not found\033[0m"
    echo -e "\e[31mPlease install Python3 and run again this script.\033[0m"
    exit 1
fi


# Check if vxi11 is already installed system-wide
pyver=$(ls /usr/bin | grep -o "python3.[0-9]" | head -n 1)
ls /usr/local/lib/$pyver/dist-packages | grep vxi11
if [ $? -eq 1 ]
then

    echo -e "\e[1mInstalling VXI11 Python Lib...\033[0m"
    # Python dependencies
    wget https://github.com/python-ivi/python-vxi11/archive/master.zip
    unzip master.zip
    cd python-vxi11-master
    sudo python3 setup.py install
    cd ..
    rm -rf python-vxi11-master
    rm master.zip
else
    echo -e "\e[1mVXI11 Python Lib already installed\033[0m"
fi

echo -e "\e[1mAll dependencies installed!\033[0m"

# Installation of the Tektronix FCA3103 USBTMC support
read -p "Do you want to add Tektronix FCA3103 USBTMC support? y/n " -n 1 -r
echo 
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo -e "\e[1mAdding rule for Tektronix FCA3103 in udev...\033[0m"
    grep "SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="0957", ATTRS{idProduct}=="1755", GROUP="usbtmc", MODE="0660"" $rule_file
    if [ $? != 0 ]; then
        echo -e "# USBTMC instruments\n" >> $rule_file
        echo -e "# Tektronix FCA3103" >> $rule_file
        echo -e "SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="0957", ATTRS{idProduct}=="1755", GROUP="usbtmc", MODE="0660"" >> $rule_file
    else
        echo -e "\e[1mUdev rule already added in $rule_file\033[0m"
    fi
    echo -e "\e[1mChecking groups and user permissions for USBTMC driver\033[0m"
    cut -d: -f1 /etc/group | grep usbtmc
    if [ $? != 0 ]; then
        echo -e "\e[1mAdding the user to the new group usbtmc\033[0m"
        groupadd usbtmc
        usermod -aG usbtmc $SUDO_USER
    else
        groups | grep usbtmc
        if [ $? != 0 ]; then
            usermod -aG usbtmc $SUDO_USER
        fi
    fi
fi
echo -e "\e[102mSystem ready. Have fun with your equipment!!\033[0m"
