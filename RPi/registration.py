import requests
import json
import time

class registration():
    def __init__(self, catalogURL, payload, url= None):
        self.servicesURL = catalogURL+"/microcontrollers"
        if url==None:
            self.conf=dict(payload) 
        else:
            self.conf=dict(payload) 
    def register(self):
        self.conf["timestamp"]=time.time()
        requests.post(self.servicesURL,json = self.conf)
        print('registration to the catalog completed!')
    def update(self):
        self.conf["timestamp"]=time.time()
        requests.put(self.servicesURL,json=self.conf)    


