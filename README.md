# bos_heater_mqtt
Expose a Braiins OS miner as a heater in Home-Assistant using hvac MQTT

# This is still WIP. Not ready for use

Warning: You will need to have an independent/third paty temperature sensor
as there are no temperature sensor reflecting room temperature inside the AntMiner

## Installation
To install, on the antminer, after installing BraiinsOS

# Run the installer
```
# sh -c "$(wget https://raw.githubusercontent.com/matfra/bos_heater_mqtt/main/install.sh -O -)"
```

# Home-assistant configuration
First, we will need to make sure that you have a temperature sensor that is published on your MQTT server. There is a trick, you can publish any already existing temperature sensor to MQTT using home assistant itself.

Example of automation.yaml file to do just that:
```
- alias: publish_ble_temperature_livingroom
  trigger:
    - platform: time_pattern
      seconds: "/20"
  action:
    service: mqtt.publish
    data: {"payload": "{{ states('sensor.ble_temperature_livingroom') }}", "topic": "sensors/ble_temperature_livingroom", "qos": 0, "retain": 0}
```

# configuration.yaml
```
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
```

