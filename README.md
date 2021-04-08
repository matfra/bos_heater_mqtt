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
    name: ant-sofa-window
    modes:
      - off
      - heat
    fan_modes:
      - high
      - normal
      - low
      - auto
    mode_command_topic: "bos_heater/ant-sofa-window/mode/set"
    mode_state_topic: "bos_heater/ant-sofa-window/mode/state"
    fan_mode_command_topic: "bos_heater/ant-sofa-window/fan/set"
    fan_mode_state_topic: "bos_heater/ant-sofa-window/fan/state"

  - platform: generic_thermostat
    name: living room miner
    heater: climate.ant-sofa-window
    target_sensor: sensor.ble_temperature_livingroom
    min_temp: 16
    max_temp: 23
    target_temp: 20
    cold_tolerance: 0.5
    hot_tolerance: 0.5
    ac_mode: false
    min_cycle_duration:
      minutes: 15
    precision: 0.1
    away_temp: 12
```

## TODO
- Implement off
- Implement auto
- Catch reboot signal properly
- Better install for the service