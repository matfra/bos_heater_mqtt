#!/bin/sh -ex
INSTALL_DIR="/root"
INITD_FILE="/etc/init.d/mqttbos"

echo "Installing Python"
opkg update
opkg install python3 python3-pip

echo "Installing dependencies"
pip3 install -r https://raw.githubusercontent.com/matfra/bos_heater_mqtt/main/requirements.txt

echo "Downloading/Updating the bos_miner_mqtt"
wget https://raw.githubusercontent.com/matfra/bos_heater_mqtt/main/bos_heater_mqtt.py -O $INSTALL_DIR/bos_heater_mqtt.py
chmod +x bos_heater_mqtt.py

echo "Creating a daemon"
wget https://raw.githubusercontent.com/matfra/bos_heater_mqtt/main/mqttbos -O $INITD_FILE
chmod +x $INITD_FILE
ln -s $INITD_FILE /etc/rc.d/S99mqttbos

echo "Install sucessful
"
/root/bos_heater_mqtt.py --help

echo "
Now try it in CLI and verify it works properly. 
Tune your frequencies voltage so that it's safe. 
Once you found all the correct arguments,
write it down (space of new line separated) in the file:

/root/bos_heater_mqtt.txt

Then you can start the daemon with service mqttbos start"