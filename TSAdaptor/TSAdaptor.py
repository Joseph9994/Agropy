import time
import json
import requests
from registration import *
from MyMQTT import *
import threading
from pprint import pprint

# This script sends sensor data to the ThingSpeak database 
# MQTT methods:
#   subscriber to receive wet/dry bulb temperature and humidity data
# HTTP methods:
#   get request to ThinkSpeak to send the all the sensor data
#   get/post/put request to the catalog

class Thingspeak_Adaptor():
    def __init__(self,broker,port,topic):
        #self.baseurl="https://api.thingspeak.com/update?api_key="
        # self.catalog_url=catalog_url
        self.client=MyMQTT('TS_adaptor',broker,port,self)
        self.topic=topic
        self.client.start()
        self.client.mySubscribe(topic)
    def stop(self):
        self.client.stop()    
    def notify(self,topic,payload):                                # payload must be a file json with a key temperature 
        # Retrieve API key to send info to         
        sensors=(requests.get(catalog_URL+"/sensors")).json()      # retrieving all the sensors from the catalog
        for element in sensors['sensors']: 
            if element["MQTT_Topic"] == topic:
                deviceName = element['sensorName']
                print(f'Received payload from {deviceName}')
                apiKey = element["thingspeakAPIkey"]               # retrieving the API key of the sensor

        # Send data to ThingSpeak:
        d=json.loads(payload)
        dryTemperature = d['data']['dryTemperature']
        wetTemperature = d['data']['wetTemperature']
        humidity = d['data']['humidity']
        time = d['data']['received_at']

        request_to_TS = f'https://api.thingspeak.com/update?api_key={apiKey}&field1={dryTemperature}&field2={wetTemperature}&field3={humidity}&field4={time}'
        requests.get(request_to_TS)
        print('The data was sent to Thingspeak')
        

class Update(threading.Thread):                                    # Multithreading for doing the update of the timestamp of the service
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
    conf = json.load(open('settings.json'))
    payload = conf["ServiceData"]
    catalog_URL=conf["catalogURL"]  
    service = registration(catalog_URL, payload)
    try: 
        service.register()
    except:
        print('Catalog not connected!')
        raise SystemExit

    subscribeTopic = conf["ServiceData"]['MQTT_Topic']
    info=(requests.get(catalog_URL+"/broker")).json()
    tsa=Thingspeak_Adaptor(info['broker']["url"],info['broker']["port"],subscribeTopic) 

    t1 = Update(1,conf['timeforupdate'],service)
    t1.start()
    t1.join()
    
    #probably the last two lines dont work
    while True:
        time.sleep(60)