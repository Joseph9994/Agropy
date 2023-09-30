from sqlite3 import Time
import paho.mqtt.subscribe as subscribe
import time
import json
import os
import re
from MyMQTT import *
from wetBulb import *
from datetime import datetime
from registration import *
import cherrypy
from pprint import pprint

# MQTT methods:
#   subscribe: to The Things Network Cloud to receive data from the Agrion sensors
#   publish:  extracted important data from the previous subscription, with the wet bulb temperature calcualted 
#             through the dry bulb temperature and humidity          
# HTTP methods:
#   get/post/put request to the catalog

class packageManager(object):
    def __init__(self, mqtt_payload):
        self.m=mqtt_payload

    def savePayload(self):
        #data from Agrion
        data=self.m.payload
        
        #save the payload into a json file
        with open('temp_data.json', 'w') as f:
            f.write(data.decode("utf-8"))                                        # data.decode to convert from byte obj to str
        f.close()

    def dataExtraction(self): 
        with open('temp_data.json') as j_f:
            file = json.load(j_f)                                                # extract data about
            dryTemp = file['uplink_message']['decoded_payload']['temp']          # dry bulb temperature
            hum = file['uplink_message']['decoded_payload']['hum']               # humidity
            wetTemp = wetBulb(dryTemp,hum)                                       # wet bulb temperature
            time = file['received_at'].split('.')                                # extract the time: it is a timestamp in format 123456.789 -> we don't need microsecond precision
            print(time)
            date_time_obj = datetime.strptime(time[0], '20%y-%m-%dT%H:%M:%S')    # convert in a human readable format year-month-day hour:minutes:seconds
            deviceName = file['end_device_ids']['device_id']
            # wetTemp = wet_bulb_temp.formula() 
            payload = {                                                          # store all the data needed
                'data':
                    {   
                        'deviceName': deviceName,
                        'wetTemperature': wetTemp,
                        'dryTemperature': dryTemp,
                        'humidity': hum,
                        'received_at': date_time_obj.timestamp()
                    }
            }
        j_f.close()
        return payload 

class PackagePublisher():
    def __init__(self,clientID, broker, port, pubTopic,catalog_URL):
        self.service = service
        self.pubClient = MyMQTT(clientID,broker,port,self)
        self.broker = broker
        self.port = port
        self.pubTopic = pubTopic
        self.catalogURL = catalog_URL
        self.__message={'client': clientID,'n':'temperature','value':None, 'timestamp':'','unit':"Celcius"}
    def start(self):
        self.pubClient.start()
    def stop(self):
        self.pubClient.stop()
    def publish(self,payload):
        #Publish data of sensor
        deviceName = payload['data']['deviceName'] 
        print(f"Received a payload from {deviceName}")  
        pubTopic = self.pubTopic+deviceName          # topic should be of time /companyName/Data/sensorName
        
        self.pubClient.myPublish(pubTopic,payload) 
        print(f"Published the following data to {pubTopic}")
        pprint(payload)
        
        #Update catalog
        conf = json.load(open('Settings.json')) 
        catalog_URL=conf["catalogURL"] 
        sensorList=(requests.get(catalog_URL+"/sensors")).json()
        sensor = next(x for x in sensorList['sensors'] if x["MQTT_Topic"] == pubTopic)
        service = registration(catalog_URL, sensor)
        service.update()
        print("Updated the sensor timestamp in the catalog")

if __name__=='__main__':
    # Service registration to catalog 
    conf = json.load(open('Settings.json'))
    payload = conf["sensors"]  
    catalog_URL=conf["catalogURL"]  
    for x in range(len(payload)-1):
        service = registration(catalog_URL, payload[x])
        try: 
            service.register()
        except:
            print('Catalog not connected!')
            raise SystemExit

    # Loading the data to subscribe to the Agrion broker: 
    file = json.load(open('AgrionData.json'))
    subscribeTopic='___/devices/+/up'        ## <<<<<< 
    server=file["server"]
    user=file["user"]
    password=file["password"]

    publishTopic =  '/'+payload[0]['companyName']+'/Data/'
    info=(requests.get(catalog_URL+"/broker")).json()
    p = PackagePublisher('AgrionData',info['broker']["url"],info['broker']["port"],publishTopic,catalog_URL)
    p.start()

    while True:
        print("Waiting for the data...")
        
        # subscribe to Agrion data
        m=subscribe.simple(topics=[subscribeTopic], hostname=server, port=1883, auth={'username':user, 'password':password}, msg_count=1)
        print(f'the result is {m}')


        # Process data
        PM=packageManager(m)
        print("new package incoming...:")
        PM.savePayload()
        payload = PM.dataExtraction()

        # Publish to our broker
        try:
            p.publish(payload)
            print("Finished publishing")
        except:
            print('Could not publish this payload')


                
                
                