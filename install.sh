#!/bin/sh -ex
INSTALL_DIR="/root"

echo "Installing Python"
opkg update
opkg install python3 python3-pip

echo "Installing dependencies"
pip3 install -r https://raw.githubusercontent.com/matfra/bos_heater_mqtt/main/requirements.txt

echo "Downloading/Updating the bos_miner_mqtt"
wget https://raw.githubusercontent.com/matfra/bos_heater_mqtt/main/bos_heater_mqtt.py -O $INSTALL_DIR/bos_heater_mqtt.py
chmod +x bos_heater_mqtt.py

echo "Now try it in CLI and verify it works properly. Tune your frequencies voltage so that it's safe.when you are ready, just run this command to make it start automatically:\necho \"/root/bos_heater_mqtt.py ###ALL your args here###\" > /etc/rc.d/S99bos_heater_mqtt"

/root/bos_heater_mqtt.py
