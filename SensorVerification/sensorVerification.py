import requests
import json
import threading
import time
from MyMQTT import *
from registration import *

# This service checks to see if the sensor has published in the last day. In case it hasn't it deletes it from the catalog
# HTTP methods:
#   get request to ThinkSpeak to receive the sensor location
#   get/post/put/delete request to the catalog

class deleteThread(threading.Thread):  
    def __init__(self, thread_ID, checkTime,catalog_URL):
        threading.Thread.__init__(self)
        self.thread_ID = thread_ID
        self.checkTime = checkTime
        self.catalog_URL = catalog_URL
    def run(self):
        time.sleep(3)
        while True:
            try:
                catalog = requests.get(catalog_URL+'/sensors').json()
                if  catalog =={}:                                                            # If the catalog is empty, pass
                    pass
                else:                                                                        # If the catalog is not empty, perform the next lines of code.
                    for n in catalog['sensors']: 
                        if time.time()-float(n['timestamp'])>float(self.checkTime):          # checking of how many seconds have passed from the last work of the service, if it is more than one day it has to be deleted from the catalog
                            requests.delete(catalog_URL+'/sensors/'+n['sensorID'])           # delete sensor information from the gatalog service section   #<<<<<< this needs to be implemented in the catalog or it wont work
                            pubTopic = n["MQTT_Topic"]+"/status"                             # publish on this topic the status of the not-working sensor
                            info=(requests.get(catalog_URL+"/broker")).json()                # retrieve broker info from the catalog
                            pubClient = brokenSensorAlert('brokenSensorAlert',info['broker']["url"],info['broker']["port"],pubTopic)
                            
                            TSchannelID = n["TSchannelID"]
                            request_to_TS = f'https://api.thingspeak.com/channels/{TSchannelID}/feeds.json?location=true' #
                            g = requests.get(request_to_TS)                                  # request from thinkspeak the information about the location of this specific not-working sensor in order to send it to the telegram bot with the message
                            data = json.loads(g.text)
                            payload = {   
                                'status':0,                                                  # setting the status of the sensor to 0
                                'latitude':data['channel']['latitude'],                      # retrieving latitude of the sensor from thinkspeak
                                'longitude':data['channel']['longitude'],                     # retrieving longitude of the sensor from thinkspeak
                                'sensorName':n['sensorName']
                            }
                            pubClient.start()
                            pubClient.publish(payload)
                            pubClient.stop()
                time.sleep(1)                
            except KeyboardInterrupt:
                break

class brokenSensorAlert():
    def __init__(self,clientID, broker, port, topic):
        self.pubClient = MyMQTT(clientID,broker,port,self)
        self.broker = broker
        self.port = port
        self.topic = topic
    def start(self):
        self.pubClient.start()
    def stop(self):
        self.pubClient.stop()
    def publish(self,payload):
        self.pubClient.myPublish(self.topic,payload)
        print('published')

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

if __name__ == '__main__':
    conf = json.load(open('settings.json'))
    payload = conf["ServiceData"]
    catalog_URL=conf["catalogURL"]  
    service = registration(catalog_URL, payload)
    try: 
        service.register()
    except:
        print('Catalog not connected!')
        raise SystemExit

    conf = json.load(open('settings.json'))
    checkTime = conf['verCheckTime']              # Discriminant time variable, set to one day, for considering a service nonworking
    catalog_URL = conf['catalogURL']              # Retrieve the url of the catalog
  

    t2 = deleteThread(2,checkTime,catalog_URL)
    t1 = Update(1,conf['timeforupdate'],service)  # Updating od the service (timestamp is continuosly updating until the service is running)
    t2.start()
    t1.start()
    t2.join()
    t1.join()

