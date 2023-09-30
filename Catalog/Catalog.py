import json
import requests 
import cherrypy
import time
import threading
import uuid

# The catalog acts as a registry system for all the devices, resources and services in the platform and it is managed through HTTP methods.
# This registry system provides information about end-points (i.e. REST Web Services and MQTT topics) of all the involved actors, 
# as well as additional characteristic information. 
# Thus, actor A that need information from actor B should retrieve it through the catalog's REST Web Services.
# For this to occur correctly, all the devices, resources and services in the platform must register to the catalog
# upon startup, and their correct functioning must be checked periodically. If a service were to ceace to function
# it will be removed from the catalog. 
# HTTP methods:
#   post request to ThinkSpeak to create a TS channel in case sensor is added
#   manages get/post/put/delete request to the catalog


def loadCatalog():                                                                         
    # Open an existing Catalog or create a new one if it doesn't exit
    try:
        catalog = json.load(open("catalog.json"))                  
    except:
        catalog = {
            "broker":dict,
            "services":[],                
            "sensors":[],
            "microcontrollers":[],
            "Last_catalog_update":time.time()
        }
        # Add broker information (stored in broker.json) to the Catalog. This info must be known prior to catalog creation
        with open("broker.json") as Broker:
            s = json.load(Broker)
            catalog["broker"]=dict(s["broker"])                                             
        json.dump(catalog,open("catalog.json","w"),indent=4)
    return catalog

class catalogManager(): 
    # This class includes all functions required for modifying the catalog, adding, updating and deleting services.
    def __init__(self):
        # Calling the 
        cat = loadCatalog()                                                                 
        self.broker = cat["broker"]
        self.services = cat["services"]
        self.sensors = cat["sensors"]
        self.microcontrollers = cat['microcontrollers']

    #Adding new service
    def addItem(self,body,type):
        if type == 'services':
            self.services.append(body) 
        elif type == 'sensors':
            self.sensors.append(body) 
        elif type == 'microcontrollers':
            self.microcontrollers.append(body) 
        else:
            raise cherrypy.HTTPError(status=400, message='UNABLE APPEND THIS ITEM. Must be one of the following: /all, /services, /microcontrollers')
        #print(self.services) 

    #Detele service
    def deleteService(self,serviceID):
        if not self.services ==[]:
            for n in range(len(self.services)):
                if self.services[n]["serviceID"]==serviceID:
                    self.services.pop(n)
                    break                                                                    #Break the loop after the service is found 
    #Detele sensor
    def deleteSensor(self,sensorID):
        if not self.sensors == []:
            for n in range(len(self.sensors)):
                if self.sensors[n]["sensorID"] == sensorID:
                    self.sensors.pop(n)
                    break
    #Update service
    def updateService(self, serviceID, body):
        if not self.services ==[]:
            for n in range(len(self.services)):
                if self.services[n]["serviceID"]==serviceID:
                    self.services[n].update(body)
                    break
    #Update sensor
    def updateSensor(self, sensorID, body):
        if not self.sensors ==[]:
            for n in range(len(self.sensors)):
                if self.sensors[n]["sensorID"]==sensorID:
                    self.sensors[n].update(body)
                    break

    #Update microcontroller (RPi)
    def updateMicro(self, microID, body):
        if not self.sensors ==[]:
            for n in range(len(self.sensors)):
                if self.microcontrollers[n]["microID"]==microID:
                    self.microcontrollers[n].update(body)
                    break
                    

class requestManager():  
    #This class manages the HTTP requests that allow all actors communicate with the catalog.   
    exposed = True
    def __init__(self):
        self.c = catalogManager()

    def GET(self, *uri): 
        if len(uri)==0:# An error will be raised in case there is no uri 
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL. THE ONLY ENTRIES ALLOWED ARE: /all, /services, /microcontrollers')        
       
        #Return all of the catalog
        if uri[0]=="all" and len(uri)==1:
            result = {
            "broker":self.c.broker,
            "services":self.c.services,
            "sensors":self.c.sensors,
            "microcontrollers":self.c.microcontrollers,
            "Last_catalog_update":time.time()
            }
            return json.dumps(result,indent=4)
        #Return the broker in the catalog
        elif uri[0]=="broker" and len(uri)==1:
            result = {
            "broker":self.c.broker
            }
            return json.dumps(result,indent=4)
        #Return the services in the catalog
        elif uri[0]=="services" and len(uri)==1:
            result = {
            "broker":self.c.services
            }
            return json.dumps(result,indent=4)
        #Return the sensors in the catalog
        elif uri[0]=="sensors" and len(uri)==1:
            result = {
            "sensors":self.c.sensors
            }
            return json.dumps(result,indent=4)
        #Return the microcontrollers in the catalog
        elif uri[0]=="microcontrollers" and len(uri)==1:
            result = {
            "microcontrollers":self.c.microcontrollers
            }
        else:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL. THE ONLY ENTRIES ALLOWED ARE: /all, /sensors, /services, /broker /microcontroller')
 
    def POST(self, *uri, **params):
        #Adding new Service 
        if uri[0]=="services":
            body = cherrypy.request.body.read()
            jsonBody=json.loads(body.decode('utf-8')) #since web pages use utf-8
            if "serviceID" in jsonBody:
                if not any(i['serviceID'] == jsonBody['serviceID'] for i in self.c.services):
                    jsonBody["timestamp"]=time.time()
                    type = 'services'
                    self.c.addItem(jsonBody,type)
                    result = f"Service with ID {jsonBody['serviceID']} is added"
                    print(result)
                    return result
        #Adding new Sensor 
        elif uri[0]=="sensors":
            body = cherrypy.request.body.read()
            jsonBody=json.loads(body.decode('utf-8')) #since web pages use utf-8
            if "sensorID" in jsonBody:
                if not any(i['sensorID'] == jsonBody['sensorID'] for i in self.c.sensors):
                    jsonBody["timestamp"]=time.time()
                    type = 'sensors'
                    self.c.addItem(jsonBody,type)
                    result = f"Sensor with ID {jsonBody['sensorID']} is added"
                    print(result)
                    return result
        #Adding new microcontroller 
        elif uri[0]=="microcontrollers":
            print("in micro")
            body = cherrypy.request.body.read()
            jsonBody=json.loads(body.decode('utf-8')) #since web pages use utf-8
            if "microID" in jsonBody:
                if not any(i['microID'] == jsonBody['microID'] for i in self.c.microcontrollers):
                    jsonBody["timestamp"]=time.time()
                    type = 'microcontrollers'
                    self.c.addItem(jsonBody,type)
                    result = f"microcontroller with ID {jsonBody['microID']} is added"
                    print(result)
                    return result
        #Adding new Sensor 
        if uri[0]=="addSensorsHTML":    #Adding a new sensor through the HTML page
            # Info from webpage: 
            sensorName = params['sensorName']
            MQTT_Topic = params['subscriptionTopic']
            companyName = params['company']

            # Creating a new TS channel for the new sensor:
            userAPI = ''
            field1 = 'dry temperature'
            field2 = 'wet temperature'
            field3 = 'humidity'
            field4 = 'timestamp'
            data = requests.post(f'https://api.thingspeak.com/channels.json?api_key={userAPI}&name={sensorName}&field1={field1}&field2={field2}&field3={field3}&field4={field4}&public_flag=true&latitude=44.76&longitude=7.5')
            data = json.loads(data.text)

            for key in data['api_keys']:
                if key['write_flag'] == True:
                    api_key = key['api_key']

            newSensor = {
                "sensorName": sensorName,
                "sensorID": str(uuid.uuid4()),
                "MQTT_Topic":f"{companyName}/Data/{sensorName}",
                "companyName": companyName,
                "sensor_type": "",
                "thingspeakAPIkey": api_key,
                "TSchannelID": data['id'],
                "timestamp": time.time()
            }
            # Update AgrionData.json
            with open('../DataFromSensors/AgrionData.json') as f:
                file_data = json.load(f)
                file_data["topic"][sensorName] = MQTT_Topic
            with open('../DataFromSensors/AgrionData.json','w') as f:
                json.dump(file_data, f, indent=4)
            f.close()
            #Update sensor Setting.json 
            with open('../DataFromSensors/Settings.json') as f:
                file_data = json.load(f)
                file_data["sensors"].append(newSensor)
            with open('../DataFromSensors/Settings.json','w') as f:
                json.dump(file_data, f, indent=4)
            self.c.addItem(newSensor,'sensors')
            raise cherrypy.HTTPRedirect('https://sites.google.com/view/added-sensor/home-page')
            
    def PUT(self,*uri): # for update 
        body = cherrypy.request.body.read()
        jsonBody=json.loads(body.decode('utf-8')) #since web pages use utf-8
        if uri[0]=="services":
            self.c.updateService(jsonBody['serviceID'],jsonBody)
        if uri[0]=="sensors":
            self.c.updateSensor(jsonBody['sensorID'],jsonBody)
        if uri[0]=="microcontrollers":
            self.c.updateMicro(jsonBody['microID'],jsonBody)

    def DELETE(self,*uri):
        if uri[0]=="services":
            self.c.deleteService(uri[1])
        if uri[0]=="sensors":
            self.c.deleteSensor(uri[1])
    
# Thread to delete inactive services
class deleteThread(threading.Thread):
    def __init__(self, thread_ID):
        threading.Thread.__init__(self)
        self.thread_ID = thread_ID
    def run(self):
        time.sleep(3)
        while True:
            try:
                conf = json.load(open("config.json"))  
                catalog = requests.get(conf["url"]+":"+conf["port"]+"/"+"all").json()
                if  catalog =={}:                                                                           
                    pass
                else:                                                                                       
                    for n in catalog["services"]:                                                           # check for each service in the catalog
                        if time.time()-float(n["timestamp"])>float(conf["delete_time"]):                    # if too much time from the last update has passed (5 min)
                            requests.delete(conf["url"]+":"+conf["port"]+"/"+"services"+"/"+n["serviceID"]) # then delete the service from the catalog
                            print(f"deleting the service with the ID:{n['serviceID']}")
                time.sleep(15)                
            except KeyboardInterrupt:
                break

# Thread for starting the server
class initiationThread(threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
    def run(self):
        conf={
            '/':{
                    'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                    'tool.session.on':True
            }
        }

        cherrypy.quickstart(requestManager(),'/',conf)

# Thread for backing up the catalog
class catalogBackup(threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
    def run(self):
        while True:
            try:
                time.sleep(5)
                f = json.load(open("config.json"))
                r = requests.get(f["url"]+":"+f["port"]+"/"+"all").json()
                if  r == {}:
                    pass
                else:
                    json.dump(r,open("catalog.json","w"),indent=4)
                    print("Catalog is saved into a json file")
            except KeyboardInterrupt:
                break



if __name__ == '__main__':
    t1 =  initiationThread(1)
    t2 = catalogBackup(2)
    t3 = deleteThread(3)  
    t1.start()
    t2.start()
    t3.start()
    t1.join()
    t2.join()
    t3.join()

