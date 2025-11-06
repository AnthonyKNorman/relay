import time
from umqttsimple import MQTTClient
import ubinascii
import machine
import micropython
import esp
esp.osdebug(None)
import gc
gc.collect()
from payload import device_payload
import json
from WIFI_CONFIG import MQTT_SERVER, MQTT_USER, MQTT_PASS


client_id = ubinascii.hexlify(machine.unique_id())
uid_str = ubinascii.hexlify(machine.unique_id()).decode()

device_payload["dev"]["name"] = "Relay " + uid_str
device_payload["o"]["name"] = "Relay " + uid_str
device_payload["dev"]["ids"] = uid_str

device_payload["cmps"]["switch1"]["unique_id"] = uid_str + "aa"
cmd_topic = "relay/" + uid_str + "/switch/cmd"
state_topic = "relay/" + uid_str + "/switch/state"
device_payload["cmps"]["switch1"]["state_topic"] = state_topic
device_payload["cmps"]["switch1"]["command_topic"] = cmd_topic

device_payload_dump = json.dumps(device_payload)

print(device_payload_dump)

topic_sub = b'relay/#'

last_message = 0
message_interval = 5
counter = 0

device_topic = "homeassistant/device/" + uid_str + "/config"

#**************************************
#    Handle incoming messages
#*************************************
    
def sub_cb(topic, msg):
  print((topic, msg))
  global relay_cmd
  
  # relay on / off message
  byte_cmd_topic = bytearray()
  byte_cmd_topic.extend(cmd_topic)
  
  if topic == byte_cmd_topic:
    print('relay on/off message received')
    if msg == b'ON':
      relay_cmd = 'ON'
    else:
      relay_cmd = 'OFF'

        
def connect_and_subscribe():
  global client_id, MQTT_SERVER, topic_sub
  client = MQTTClient(client_id, MQTT_SERVER, user=MQTT_USER, password=MQTT_PASS)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(topic_sub)
  print('Connected to %s MQTT broker, subscribed to %s topic' % (MQTT_SERVER, topic_sub))
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()
    
def update_relay_state():
    print("relay cmd", relay_cmd)
    if relay_cmd == 'ON':
      relay.on()
      led.off()
      msg = 'ON'
    else:
      relay.off()
      led.on()
      msg = 'OFF'
      
    print("about to publish relay state")
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

relay = machine.Pin(4, machine.Pin.OUT)
led = machine.Pin(8, machine.Pin.OUT)
relay.off()
led.off()

# set the two flags different to force relay off to start
relay_cmd = 'OFF'
last_relay_cmd = 'ON'

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

  if relay_cmd != last_relay_cmd:
      print("relay command", relay_cmd)
      last_relay_cmd = relay_cmd
      update_relay_state()

