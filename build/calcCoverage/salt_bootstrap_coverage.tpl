#!/bin/bash

# Use the following line if you booted the machine with a static IP
hostname ${hostname}
echo "${hostname}" >/etc/hostname
echo "127.0.0.1 ${hostname}" >>/etc/hosts
echo "${local_ip} ${hostname}" >>/etc/hosts
sudo apt-get upgrade -y 
sudo apt-get install -y wget
wget -O install_salt.sh https://bootstrap.saltstack.com
sudo sh install_salt.sh
sudo echo "file_client: local" >>/etc/salt/minion
sudo echo "local: True" >>/etc/salt/minion
sudo service salt-minion stop
sudo apt-get install -y git
sudo mkdir /srv/salt
git clone https://github.com/jolson7168/createData.git /home/ubuntu/createData
sed -i "0,/<numInstances>/s//${numInstances}/" /home/ubuntu/createData/build/calcCoverage/salt/coverageData.sls
sed -i "0,/<haproxy ip>/s//${haProxyIP}/" /home/ubuntu/createData/build/calcCoverage/salt/configCoverage.sh
sed -i "0,/<quidID>/s//${quidID}/" /home/ubuntu/createData/build/calcCoverage/salt/configCoverage.sh
sed -i "0,/<tableName>/s//${tableName}/" /home/ubuntu/createData/build/calcCoverage/salt/configCoverage.sh
sed -i "0,/<startTime1>/s//${startTime}/" /home/ubuntu/createData/build/calcCoverage/salt/configCoverage.sh
sed -i "0,/<numberOfDays>/s//${numDays}/" /home/ubuntu/createData/build/calcCoverage/salt/configCoverage.sh
sed -i "0,/<numberOfIDs>/s//${numIDs}/" /home/ubuntu/createData/build/calcCoverage/salt/configCoverage.sh
sed -i "0,/<startOnID>/s//${startID}/" /home/ubuntu/createData/build/calcCoverage/salt/configCoverage.sh
sudo cp -R /home/ubuntu/createData/build/calcCoverage/salt/* /srv/salt
sudo salt-call --local state.highstate --state-verbose=False
