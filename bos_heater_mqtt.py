#!/usr/bin/env python3
"""
Expose a Braiins OS miner as a heater in Home-Assistant using hvac MQTT
Warning: You will need to have an independent/third paty temperature sensor
as there are no temperature sensor reflecting room temperature inside the AntMiner


To install, on the antminer, after installing bosminer:
# Install Python
opkg update ; opkg install python3 python3-pip
pip3 install paho-mqtt
# Download this file
wget <this file>
# Make this file executable
chmod +x <this file>
# Auto start bosminer_mqtt_controller
ln -s $(pwd)/thisfile /etc/rc.d/S99bosminer_mqtt_controller


Exampe configuration in home-assistant:
First, we will need to make sure you have temperature data from a third party sensor available on MQTT
You can use home assistant automations to publish existing sensor data to MQTT
Example of automation.yaml file:
- alias: publish_ble_temperature_livingroom
  trigger:
    - platform: time_pattern
      seconds: "/20"
  action:
    service: mqtt.publish
    data: {"payload": "{{ states('sensor.ble_temperature_livingroom') }}", "topic": "sensors/ble_temperature_livingroom", "qos": 0, "retain": 0}


climate:
  - platform: mqtt
    name: miner
    modes:
      - "idle"
      - "heat"
    fan_modes:
      - "high"
      - "medium"
      - "low"
    mode_command_topic: "bosminer_mqtt/ant-sofa-window/mode/set"
    temperature_command_topic: "bosminer_mqtt/ant-sofa-window/temperature/set"
    fan_mode_command_topic: "bosminer_mqtt/ant-sofa-window/fan/set"
"""

__author__ = "Mathieu Frappier"
__version__ = "0.1.0"
__license__ = "MIT"

import argparse
import paho.mqtt.client as mqtt
import time
import telnetlib
import subprocess
import socket
import json
from logzero import logger
import toml
import shutil

def call_bos_api(request_dict, hostname="127.0.0.1", port=4028):
    """
    Talk to bosminer API and returns a dict of the response
    """
    logger.debug("bos_api: connecting")
    tn = telnetlib.Telnet(hostname, port)
    request=json.dumps(request_dict) + '\n'
    logger.debug("bos_api: sending " + request)
    tn.write(request.encode('utf-8'))
    json_response=tn.read_until(b'\x00', timeout=3).decode('utf-8')
    logger.debug("bos_api: connection closed.")
    try:
        return json.loads(json_response)
    except json.decoder.JSONDecodeError:
        logger.warning("Invalid response received from bosminer: " + str(json_response))
        return {}

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc, topic):
    logger.info("Connected to MQTT server with result code "+str(rc))
    client.subscribe(topic)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    logger.debug(msg.payload)
    try: 
        dict_payload=json.loads(msg.payload)
    except json.decoder.JSONDecodeError:
        logger.warning("Invalid MQTT message received: " + str(msg.payload))
        return
    logger.debug(call_bos_api(dict_payload))

def get_bos_temps(hostname="127.0.0.1", port=4028):
    """ Returns highest values for board and chip temps """
    temps = call_bos_api({"command": "temps"})
    max_board_temp = 0
    max_chip_temp = 0
    for board in temps['TEMPS']:
        board_temp=board.get("Board", 0)
        chip_temp=board.get("Chip", 0)
        if board_temp > max_board_temp:
            max_board_temp = board_temp
        if chip_temp > max_chip_temp:
            max_chip_temp = chip_temp
    return max_board_temp, max_chip_temp

def run_bosminer_with_profile(profile):
    shutil.copy(f"/tmp/{profile}_profile.toml", "/etc/bosminer.toml"
    subprocess.run(['/etc/init.d/bosminer', 'restart'])

def main(args):
    """ Main entry point of the app """
    logger.info("Starting with following parameters")
    logger.info(args)
    hostname = socket.gethostname()
    logger.info("Parsing profiles")
    available_profiles = generate_all_conf(args)
    current_profile = "normal"
    mqtt_prefix = f"bosminer_mqtt/{hostname}"
    client = mqtt.Client()
    def on_connect_with_args(*on_connect_args):
        on_connect(*on_connect_args, args.mqtt_topic)
        
    def on_message_with_args(*on_message_args):
        on_message(*on_message_args)

    client.on_connect = on_connect_with_args
    client.on_message = on_message_with_args

    client.connect(args.mqtt_broker_host, args.mqtt_broker_port, 60)

    run_bosminer_with_profile(current_profile)


# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
    client.loop_start()
    while True:
        # Get the internal temps
        """     mode_command_topic: "bosminer_mqtt/ant-sofa-window/mode/set"
                fan_mode_command_topic: "bosminer_mqtt/ant-sofa-window/fan/set"
        """
        board_temp, chip_temp = get_bos_temps()
        if board_temp > 0 and chip_temp > 0:
            client.publish(f"{mqtt_prefix}/status", "heat")
            client.publish(f"{mqtt_prefix}/status/current_profile", current_profile)
            client.publish(f"{mqtt_prefix}/status/board_temperature", board_temp)
            client.publish(f"{mqtt_prefix}/status/chip_temperature", chip_temp)
        else:
            client.publish(f"{mqtt_prefix}/status", "idle")
        time.sleep(10)

def check_value(value, min, max, allow_zero=True):
    assert value >= min or value <= max or allow_zero == (value == 0 )

def parse_profile(profile=""):
    """ Takes csv strings and return dicts """
    fan_speed, f1, v1, f2, v2, f3, v3 = profile.split(",")
    check_value(int(f1), 170, 900, True)
    check_value(int(f2), 170, 900, True)
    check_value(int(f3), 170, 900, True)
    check_value(float(v1), 7.96, 9.1, True)
    check_value(float(v2), 7.96, 9.1, True)
    check_value(float(v3), 7.96, 9.1, True)
    check_value(int(fan_speed), 30, 100, False)

    return {
        "fan_speed": int(fan_speed),
        "board1": { "enabled": int(f1) != 0, "freq": int(f1), "voltage": float(v1)},
        "board2": { "enabled": int(f2) != 0, "freq": int(f2), "voltage": float(v2)},
        "board3": { "enabled": int(f3) != 0, "freq": int(f3), "voltage": float(v3)}
    }


def generate_bosminer_conf(pool_address, pool_username, profile_dict):
    config = {
        'format': {
            'version': '1.2+',
            'model': 'Antminer S9',
            'generator': f'bos_heater_mqtt {__version__}',
            'timestamp': int(time.time())
        },
        'hash_chain_global': {'asic_boost': True, 'frequency': 170.0, 'voltage': 7.9500000000000002},    
        'autotuning': {'enabled': False, 'psu_power_limit': 275},
        'temp_control': {'mode': 'manual'},
        'group': [
            {'name': 'Default', 'pool': [
                {'url': pool_address,
                'user': "{}.{}".format(pool_username, socket.gethostname()),
                'password': 'foo'}
                ]
            }
        ],
        'hash_chain': {
            '6': {'enabled': profile_dict["board1"]["enabled"], 'frequency': profile_dict["board1"]["freq"], 'voltage': profile_dict["board1"]["voltage"]},
            '7': {'enabled': profile_dict["board2"]["enabled"], 'frequency': profile_dict["board2"]["freq"], 'voltage': profile_dict["board2"]["voltage"]},
            '8': {'enabled': profile_dict["board3"]["enabled"], 'frequency': profile_dict["board3"]["freq"], 'voltage': profile_dict["board3"]["voltage"]}
        },
        'fan_control': {'speed': profile_dict["fan_speed"]}
    }
    toml_config=toml.dumps(config)
    return toml_config


def generate_all_conf(args):
    """
    Parses the args, generate the confs and returns a list of available profiles
    """
    pool_address = args.pool_address
    pool_username = args.pool_username
    available_profiles = []
    if args.low_profile:
        with open ("/tmp/low_profile.toml", "w") as f:
            low_config = generate_bosminer_conf(pool_address, pool_username, parse_profile(args.low_profile))
            logger.debug("Generated config for profile low:\n{}".format(low_config))
            f.write(low_config)
        available_profiles.append("low")
    if args.normal_profile:
        with open ("/tmp/normal_profile.toml", "w") as f:
            normal_config = generate_bosminer_conf(pool_address, pool_username, parse_profile(args.normal_profile))
            logger.debug("Generated config for profile normal:\n{}".format(normal_config))
            f.write(normal_config)
        available_profiles.append("normal")
    if args.high_profile:
        with open ("/tmp/high_profile.toml", "w") as f:
            high_config = generate_bosminer_conf(pool_address, pool_username, parse_profile(args.high_profile))
            logger.debug("Generated config for profile high:\n{}".format(high_config))
            f.write(high_config)
        available_profiles.append("high")
    return available_profiles




if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mqtt-broker-host", required=True, type=str)
    parser.add_argument("-p", "--mqtt-broker-port", default=1883, type=int)
    parser.add_argument("-t", "--mqtt-topic", default="bosminer_mqtt", type=str)
    parser.add_argument("-l", "--low-profile", required=False, help="fan_speed,freq1,volt1,freq2,volt2,freq3,volt3 Example: 45,170,7.91,0,0,170,7.91", type=str)
    parser.add_argument("-n", "--normal-profile", required=True, help="fan_speed,freq1,volt1,freq2,volt2,freq3,volt3 Example: 60,230,7.91,230,7.91,230,7.91", type=str)
    parser.add_argument("-c", "--high-profile", required=False, help="fan_speed,freq1,volt1,freq2,volt2,freq3,volt3 Example: 100,270,7.91,270,7.91,270,7.91", type=str)
    parser.add_argument("-a", "--pool-address", default="stratum+tcp://stratum.slushpool.com:3333", type=str)
    parser.add_argument("-u", "--pool-username", required=True, type=str)

    # Optional verbosity counter (eg. -v, -vv, -vvv, etc.)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Verbosity (-v, -vv, etc)")

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    args = parser.parse_args()
    main(args)