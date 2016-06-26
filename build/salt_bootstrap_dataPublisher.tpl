#!/bin/bash

# Use the following line if you booted the machine with a static IP
hostname ${hostname}
echo "${hostname}" >/etc/hostname
echo "127.0.0.1 ${hostname}" >>/etc/hosts
echo "${local_ip} ${hostname}" >>/etc/hosts
apt-get upgrade -y 
apt-get install -y wget
wget -O install_salt.sh https://bootstrap.saltstack.com
sh install_salt.sh
echo "file_client: local" >>/etc/salt/minion
echo "local: True" >>/etc/salt/minion
service salt-minion stop
apt-get install -y git
mkdir /srv/salt
cp -R /home/ubuntu/createData/build/salt/* /srv/salt
salt-call --local state.highstate --state-verbose=False
