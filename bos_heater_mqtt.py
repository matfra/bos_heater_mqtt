
#!/usr/bin/env python3
"""
Expose a Braiins OS miner as a heater in Home-Assistant via MQTT
"""

__author__ = "Mathieu Frappier"
__version__ = "0.1.0"
__license__ = "MIT"

import argparse
import paho.mqtt.client as mqtt
from logzero import logger
import socket
import json
import time

def call_bos_api(hostname, port, request_dict):
    logger.debug("bos_api: connecting")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((hostname, port))
        request=json.dumps(request_dict)
        logger.debug("bos_api: sending " + request)
        s.sendall(request.encode('utf-8'))    
        BUFF_SIZE = 128 # 1 KiB
        data = b''
        while True:
            part = s.recv(BUFF_SIZE)
            print("part")
            print(part)
            data += part
            if len(part) < BUFF_SIZE:
                print(len(part))
                break
        #print(data)
    json_response=data.decode('utf-8').rstrip('\x00')
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
def on_message(client, userdata, msg, bos_host, bos_api_port):
    logger.debug(msg.payload)
    try: 
        dict_payload=json.loads(msg.payload)
    except json.decoder.JSONDecodeError:
        logger.warning("Invalid MQTT message received: " + str(msg.payload))
        return
    logger.debug(call_bos_api(bos_host, bos_api_port, dict_payload))


def main(args):
    """ Main entry point of the app """
    logger.info("hello world")
    logger.info(args)
    client = mqtt.Client()
    def on_connect_with_args(*on_connect_args):
        on_connect(*on_connect_args, args.mqtt_topic)
        
    def on_message_with_args(*on_message_args):
        on_message(*on_message_args, args.bosminer_ip, args.bosminer_api_port)

    client.on_connect = on_connect_with_args
    client.on_message = on_message_with_args

    client.connect(args.mqtt_broker_host, args.mqtt_broker_port, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
    client.loop_forever()




if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mqtt-broker-host", required=True, type=str)
    parser.add_argument("-p", "--mqtt-broker-port", default=1883, type=int)
    parser.add_argument("-t", "--mqtt-topic", default="bosminer", type=str)
    parser.add_argument("-b", "--bosminer-ip", required=True, type=str)
    parser.add_argument("-a", "--bosminer-api-port", default=4028, type=int)

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