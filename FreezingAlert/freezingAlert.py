import time
import json
from datetime import datetime
import requests
from registration import *
from MyMQTT import *
from pagoscope import *
import threading
from pprint import pprint

#This service acts as a subscriber with the purpose of receiving all the data (dry and wet temperature and humidity, previously sent 
# by AgrionSensor.py). It calculates, through the pagoscope function, the freezing status. Farmers use a pagoscope graph to predict 
# a freezing manually. To recreate this graph, three polygons were built according to the temperature values from a real graph.
 
# MQTT methods:
#   subscriber to retrieve data from the sensors
#   publisher to send an alert message of the freezing to the broker 
# HTTP methods:
#   get/post/put request to the catalog

class Freezing_alert():
    def __init__(self,broker,port,topicSub):
        self.client = MyMQTT('Freezing_Alert',broker,port,self)
        self.topicSub = topicSub
        self.client.start()
        self.client.mySubscribe(self.topicSub)

    def stop(self):
        self.client.stop()    
    def notify(self,topic,payload): 
        d=json.loads(payload)  
        pprint(d)
        dryTemperature = d['data']['dryTemperature']
        wetTemperature = d['data']['wetTemperature']
        
        alert_msg = pagoscope(dryTemperature,wetTemperature) #return 1-2-3 for freezing for sure, possible freezing, no freezing
        publishTopic = f'{topic}/StatusFreezing'

        try:   
            with open("output.jpg", "rb") as image:  #If there is an image saved in the folder it means 
                f = image.read()
            base64_bytes = base64.b64encode(f)
            base64_message = base64_bytes.decode('ascii')
            alert_msg['graph'] = base64_message
            self.client.myPublish(publishTopic,alert_msg) #we published a json with two keys: 'result' with the number regarding the status of the freezing and 'graph' with the ASCII code of the image
            print('published alert with image')
        except:
            self.client.myPublish(publishTopic,alert_msg) 
            print('published alert')
        
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
    # Service registration to catalog 
    conf = json.load(open('settings.json')) 
    payload = conf["ServiceData"]  #retrieving service information
    catalog_URL=conf["catalogURL"]  #retriving the URL of the catalog 
    service = registration(catalog_URL, payload) #registration class for registering the service and updating the timestamp of the service 
    try: 
        service.register() #call the register function in order to register the service to the
    except:
        print('Catalog not connected!')
        raise SystemExit
    
    info=(requests.get(catalog_URL+"/broker")).json() #retrieving the broker info from the catalog 
    topicSubscribe = conf["ServiceData"]["MQTT_Topic"] 
    fa=Freezing_alert(info['broker']["url"],info['broker']["port"],topicSubscribe)  

    t1 = Update(1,conf['timeforupdate'],service) #updating the timestamp of the service 
    t1.start()
    t1.join()
