import time
from umqttsimple import MQTTClient
import ubinascii
import machine, neopixel
import micropython
import uos
import esp
esp.osdebug(None)
import gc
gc.collect()
from payload import device_payload
import json
from WIFI_CONFIG import MQTT_SERVER, MQTT_USER, MQTT_PASS

device_name = "relay"

print(uos.uname())
machine_name = uos.uname().machine
if 'C3' in machine_name:
    machine_id = 'C3'
elif 'S3' in machine_name:
    machine_id = 'S3'
else:
    machine_id = 'unknown'
    
print('Machine ID:', machine_id)    

client_id = ubinascii.hexlify(machine.unique_id())
uid_str = ubinascii.hexlify(machine.unique_id()).decode()

print('-----------------------------------')
device_payload["dev"]["name"] = device_name + '(' + uid_str + ')'
device_payload["o"]["name"] = device_name + '(' + uid_str + ')'
device_payload["dev"]["ids"] = uid_str

entity_count = 0

for entity in device_payload["cmps"]:
    entity_name = device_payload["cmps"][entity]["name"].replace(" ", "_").lower()
    try:
        device_payload["cmps"][entity]["state_topic"] = device_name + '/' + uid_str + '/' + entity_name + '/state'
    except:
        print('no state topic')
        
    try:    
        device_payload["cmps"][entity]["command_topic"] = device_name + '/' + uid_str + '/' + entity_name + '/cmd'
    except:
        print('no command topic')
        
    device_payload["cmps"][entity]["unique_id"] = uid_str + str(entity_count)
    print (device_payload["cmps"][entity])
    
    entity_count += 1
        
print('-----------------------------------')


device_payload_dump = json.dumps(device_payload)
print('this is the payload')
print(device_payload_dump)
topic_sub_string = device_name + '/' + uid_str + '/#'
topic_sub = bytearray()
topic_sub.extend(topic_sub_string)
print('topic_sub ',topic_sub)


last_message = 0
message_interval = 300
counter = 0

device_topic = "homeassistant/device/" + uid_str + "/config"

#**************************************
#    Return Topics as string
#    takes: entity as string
#    returns: topic as string
#**************************************

def state_topic(entity):
    return device_payload["cmps"][entity]["state_topic"]


def cmd_topic(entity):
    return device_payload["cmps"][entity]["command_topic"]

#**************************************
#    Handle incoming messages
#**************************************

def sub_cb(topic, msg):
  print('received: ',topic, msg)
  global relay_cmd
  str_topic = topic.decode('utf-8')
  # relay on / off message
  if str_topic == cmd_topic('switch1'):
    print('relay on/off message received')
    if msg == b'ON':
      relay_cmd = 'ON'
    else:
      relay_cmd = 'OFF'

#**************************************
#   MQTT
#**************************************
        
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

#**************************************
#   Manage relay based on received command
#**************************************
def update_relay_state():
    print("relay cmd", relay_cmd)
    if relay_cmd == 'ON':
      relay.on()
      led_on()
      msg = 'ON'
    else:
      relay.off()
      led_off()
      msg = 'OFF'
      
    print("about to publish relay state")
    client.publish(state_topic('switch1'), msg)
    
#**************************************
#   LED Management
#**************************************    

def led_off():
    global machine_id
    global np
    if machine_id == 'C3':
        led.value(1)
    elif machine_id == 'S3':
        np[0] = (255,0,0)	#red
        np.write()

def led_on():
    global machine_id
    global np
    if machine_id == 'C3':
        led.value(0)
    elif machine_id == 'S3':
        np[0] = (0,255,0)	#red
        np.write()
    
        
    
#**************************************
#    Setup
#**************************************

try:
  client = connect_and_subscribe()
except OSError as e:
  restart_and_reconnect()
  
client.publish(device_topic, device_payload_dump)

relay = machine.Pin(4, machine.Pin.OUT)
relay.off()

# simple led on GPIO4
if machine_id == 'C3':
    led = machine.Pin(8, machine.Pin.OUT)
# neopixel on GPIO48
elif machine_id == 'S3':
    n = 1
    p = 48
    np = neopixel.NeoPixel(machine.Pin(p), n)


for i in range (10):
    led_on()
    time.sleep_ms(500)
    led_off()
    time.sleep_ms(500)


# Send the latest software version
# get the current version (stored in version.json)
if 'version.json' in uos.listdir():    
    with open('version.json') as f:
        current_version = int(json.load(f)['version'])
    print(f"Current device firmware version is '{current_version}'")
    client.publish(state_topic('version'), str(current_version))
    
client.publish(state_topic('ssid'), SSID)
    
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
        
      print('sending device info')
      client.publish(device_topic, device_payload_dump)
      
      print('sending wifi strength')
      strength = wlan.status('rssi')
      client.publish(state_topic('strength'), str(strength))
      
      client.publish(state_topic('ssid'), SSID)


      last_message = time.time()
      counter += 1
  except OSError as e:
    print("OS error:", e)
    restart_and_reconnect()

  if relay_cmd != last_relay_cmd:
      print("relay command", relay_cmd)
      last_relay_cmd = relay_cmd
      update_relay_state()
      
