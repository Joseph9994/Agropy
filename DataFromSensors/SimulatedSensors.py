# Simulating some sensors and sending them to the broker 

from cherrypy import url
import paho.mqtt.client as PahoMQTT
import time
import random
from MyMQTT import *
from wetBulb import *
from registration import *
from pprint import pprint

class SensorSimulator():
    def __init__(self,clientID, broker, port, topic,service):
        self.pubClient = MyMQTT(clientID,broker,port,self)
        self.broker = broker
        self.port = port
        self.topic = topic
        self.service = service
        self.__message={'client': clientID,'n':'temperature','value':None, 'timestamp':'','unit':"Celcius"}
    def start(self):
        self.pubClient.start()
    def stop(self):
        self.pubClient.stop()
    def publish(self):
        payload = {                                                 # randomly generate data to publish
                'data':
                    {
                        'wetTemperature':random.uniform(-1,10),     # y axis of pagoscope graph
                        #'wetTemperature':wetBulb(dryTemperature, humidity) We can calculate wetTemp like this too
                        'dryTemperature':random.uniform(-1,15),     # x axis of the pagoscope graph
                        'humidity': random.randint(50,90),          # originally used to calculate wet bulb temperature
                        'received_at': time.time()                  # time in which the data is received
                    }
            }
        
        self.pubClient.myPublish(self.topic,payload)
        pprint(payload)
        print("published")
        self.service.update()

if __name__=='__main__':

    # 1. SERVICE REGISTRATION to catalog 
    conf = json.load(open('Settings.json'))
    sensor = next(x for x in conf['sensors'] if x["sensorName"] == 'SimulatedSensor')
    catalog_URL=conf["catalogURL"]  
    service = registration(catalog_URL, sensor)
    service.register()

    publishTopic =  sensor["MQTT_Topic"]

    info=(requests.get(catalog_URL+"/broker")).json()
    s = SensorSimulator('SimulatedAgrion',info['broker']["url"],info['broker']["port"],publishTopic,service)
    s.start()

    while True:
        s.publish()
        time.sleep(180)
    

    
    


