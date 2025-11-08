device_payload = {
  "dev": {
    "ids": "",
    "name": ""
  },
  "o": {
    "name":""
  },
  "cmps": {
    "switch1": {
      "p": "switch",
      "unique_id": "",
      "name":"relay",
      "command_topic": "",
      "state_topic": "",
      "payload_on": "ON",
      "payload_off": "OFF",
      "state_on": "ON",
      "state_off": "OFF"
    },
    "strength": {
      "p": "sensor",
      "unique_id": "",
      "name":"WiFi Signal Strength",
      "device_class": "power",
      "state_topic": ""
    },
    "version": {
      "p": "sensor",
      "unique_id": "",
      "name":"OTA Version Number",
      "device_class": "power",
      "state_topic": ""
    },
    "ssid": {
      "p": "text",
      "unique_id": "",
      "name":"WiFi SSID",
      "device_class": "power",
      "state_topic": ""
    },
    "reset": {
      "p": "button",
      "unique_id": "",
      "name":"Reset",
      "command_topic": "",
      "payload_press": "RESET"
    }
  }
}
