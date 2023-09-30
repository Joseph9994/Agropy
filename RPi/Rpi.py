import time
import json
from datetime import datetime
import requests
import threading
import random
import RPi.GPIO as GPIO
from registration import *
from MyMQTT import *

# The RPi controls a LED which is activated based on the freezing status
# MQTT methods:
#   subscriber to retrieve info on the  freezing status 

class RPi():
    def __init__(self,broker,port,topic, LED_red, LED_green, LED_white):
        self.client=MyMQTT('RPI',broker,port,self)
        self.topic=topic
        self.LED_red = LED_red
        self.LED_green = LED_green
        self.LED_white = LED_white
        self.client.start()
        self.client.mySubscribe(self.topic)
    def stop(self):
        self.client.stop()    
    def notify(self,payload): 
        alert = json.loads(payload)
        dataIncoming = alert['result'] 
        # format message: 1 for freezing for sure, 2 for possible freezing, 3 no freezing 
    
        # Initialitation - switch off all the leds
        GPIO.output(LED_red, GPIO.LOW)
        GPIO.output(LED_white, GPIO.LOW)
        GPIO.output(LED_green, GPIO.LOW)  

        if dataIncoming == 1:                                    
            # 1 = freezing for sure
            print('Freezing for sure')
            start = time.time()                                          
            end = time.time()                                         
            # blinks for 5 seconds
            while end - start < 5:
                GPIO.output(self.LED_red, GPIO.HIGH)                   # led is switched on
                time.sleep(1)                                          # wait for 1 second
                GPIO.output(self.LED_red, GPIO.LOW)                    # led is switched off
                time.sleep(1)                                          # wait for 1 second
                GPIO.output(self.LED_red, GPIO.HIGH)                   # led is switched on 
                end = time.time()                                         
                
            GPIO.output(self.LED_red, GPIO.HIGH)                       # red led is switched on, because the user can be absent or not notice it -> more awarness

        elif dataIncoming == 2:                                    
            # 2 = possible freezing
            print('Possible freezing')
            start = time.time()                                            
            end = time.time()   
            # blinks for 5 seconds                                           
            while end - start < 5:
                GPIO.output(self.LED_white, GPIO.HIGH)                 # led is switched on
                time.sleep(1)                                          # wait for 1 second
                GPIO.output(self.LED_white, GPIO.LOW)                  # led is switched off
                time.sleep(1)                                          # wait for 1 second
                GPIO.output(self.LED_white, GPIO.HIGH)                 # led is switched on 
                end = time.time()                                          
                
            GPIO.output(self.LED_red, GPIO.HIGH)                       # red led is switched on, because the user can be absent or not notice it -> more awarness
        
        else:
            print('No freezing')
            GPIO.output(self.LED_green, GPIO.HIGH)                     # green led is switched on in order to 


class Update(threading.Thread): # Multithreading for doing the update
    def __init__(self, threadID,time_update,sr):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.time_update=time_update
        self.sr=sr
    def run(self):
        while True:
            self.sr.update()
            time.sleep(self.time_update)


if __name__=='__main__':
    # 1. SERVICE REGISTRATION to catalog 
    conf = json.load(open('settings.json'))                             # read data from settings.json
    payload = conf["ServiceData"]                                       # retrieve service data
    catalog_URL=conf["catalogURL"]                                      # retrieve catalog url
    service = registration(catalog_URL, payload)
    try: 
        service.register()
    except:
        print('Catalog not connected!')
        raise SystemExit

    subscribeTopic =  conf["ServiceData"]["MQTT_Topic"]
    info=(requests.get(catalog_URL+"/broker")).json()

    # Set up the Raspberry pi
    # set up pin numbering
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    # Assign a pin number to every led corresponding to the raspberry pi header
    LED_red = 7     #GPIO4
    LED_green = 11  #GPIO17
    LED_white = 13  #GPIO27

    # Set the output to the correct pin
    GPIO.setup(LED_red, GPIO.OUT)
    GPIO.setup(LED_green, GPIO.OUT)
    GPIO.setup(LED_white, GPIO.OUT)

    # Initialitation - switch off all the leds
    GPIO.output(LED_red, GPIO.LOW)
    GPIO.output(LED_white, GPIO.LOW)
    GPIO.output(LED_green, GPIO.LOW)

    rpi=RPi(info['broker']["url"],info['broker']["port"],subscribeTopic, LED_red, LED_green, LED_white) 
    t1 = Update(1,conf['timeforupdate'],service) #updating the timestamp of the service 
    t1.start()
    t1.join()

    while True:
        time.sleep(10)
