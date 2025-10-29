# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()
# Complete project details at https://RandomNerdTutorials.com/micropython-programming-with-esp32-and-esp8266/

import time
from umqttsimple import MQTTClient
import ubinascii
import machine
import micropython
import network
import esp
esp.osdebug(None)
import gc
gc.collect()
from payload import device_payload
import json


ssid = 'FARLEIGH-MESH'
password = 'Julie1801!'
mqtt_server = '192.168.68.51'
mqtt_user = 'beantree'
mqtt_pass = 's2sfilwY'

#EXAMPLE IP ADDRESS
#mqtt_server = '192.168.1.144'
client_id = ubinascii.hexlify(machine.unique_id())
uid_str = ubinascii.hexlify(machine.unique_id()).decode()

device_payload["dev"]["name"] = "Chamber Heater " + uid_str
device_payload["o"]["name"] = "Chamber Heater " + uid_str
device_payload["dev"]["ids"] = uid_str

device_payload["cmps"]["switch1"]["unique_id"] = uid_str + "aa"
cmd_topic = "heater/" + uid_str + "/switch/cmd"
state_topic = "heater/" + uid_str + "/switch/state"
device_payload["cmps"]["switch1"]["state_topic"] = state_topic
device_payload["cmps"]["switch1"]["command_topic"] = cmd_topic

device_payload_dump = json.dumps(device_payload)

print(device_payload_dump)

topic_sub = b'heater/#'

last_message = 0
message_interval = 5
counter = 0

station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(ssid, password)

while station.isconnected() == False:
  pass

print('Connected to:', ssid)
print(station.ifconfig())

device_topic = "homeassistant/device/" + uid_str + "/config"

#**************************************
#    Handle incoming messages
#*************************************
    
def sub_cb(topic, msg):
  print((topic, msg))
  global heater_cmd
  
  # heater on / off message
  byte_cmd_topic = bytearray()
  byte_cmd_topic.extend(cmd_topic)
  
  if topic == byte_cmd_topic:
    print('heater on/off message received')
    if msg == b'ON':
      heater_cmd = 'ON'
    else:
      heater_cmd = 'OFF'

        
def connect_and_subscribe():
  global client_id, mqtt_server, topic_sub
  client = MQTTClient(client_id, mqtt_server, user=mqtt_user, password=mqtt_pass)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(topic_sub)
  print('Connected to %s MQTT broker, subscribed to %s topic' % (mqtt_server, topic_sub))
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()
    
def update_heater_state():
    print("heater cmd", heater_cmd)
    if heater_cmd == 'ON':
      heater.on()
      fan.on()
      led.off()
      msg = 'ON'
    else:
      heater.off()
      fan.off()
      led.on()
      msg = 'OFF'
      
    print("about to publish heater state")
    byte_state_topic = bytearray()
    byte_state_topic.extend(state_topic)

    client.publish(byte_state_topic, msg)    

    
#**************************************
#    Setup
#**************************************    

try:
  client = connect_and_subscribe()
except OSError as e:
  restart_and_reconnect()
  
client.publish(device_topic, device_payload_dump)

heater = machine.Pin(4, machine.Pin.OUT)
fan = machine.Pin(9, machine.Pin.OUT)
led = machine.Pin(8, machine.Pin.OUT)
heater.off()
fan.off()
led.off()

# set the two flags different to force heater off to start
heater_cmd = 'OFF'
last_heater_cmd = 'ON'

#**************************************
#    Loop
#**************************************

while True:
  try:
    client.check_msg()
    
    if (time.time() - last_message) > message_interval:

      last_message = time.time()
      counter += 1
  except OSError as e:
    print("OS error:", e)
    restart_and_reconnect()

  if heater_cmd != last_heater_cmd:
      print("heater command", heater_cmd)
      last_heater_cmd = heater_cmd
      update_heater_state()

