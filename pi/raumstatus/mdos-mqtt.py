#!/usr/bin/python

import paho.mqtt.client as mqtt
import requests
import daemon

def on_message(mosq, obj, msg):
    requests.post("https://tuer.maschinendeck.org/setroomstate", data = {'state': msg.payload})

def main():
    mqttc = mqtt.Client()
    mqttc.on_message = on_message
    mqttc.connect("mqtt.starletp9.de", 1883, 60)
    mqttc.subscribe("/maschinendeck/raum/status")
    mqttc.loop_forever(retry_first_connection=True)

with daemon.DaemonContext():
    main()
