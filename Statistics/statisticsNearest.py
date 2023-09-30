import time
import json
import requests
from registration import *
from MyMQTT import *
from pprint import pprint
import datetime
import time
import threading
import numpy as np 

# This service provides statistical information regarding sensor data from any timeframe requested from the user.
# MQTT methods:
#   subscriber to retrieve user-selected date over which the statistics will be calculated.
#   publisher to send the calculated statistics 
# HTTP methods:
#   get request to ThinkSpeak to receive the all the sensor data 
#   get/post/put request to the catalog

class Statistics:
    exposed=True
    def __init__(self, broker, port, topicS, topicP):
        self.client = MyMQTT("Statistics", broker, port, self)
        self.client.start()
        self.topicSub = topicS
        self.topicPub = topicP
        self.client.mySubscribe(topicS)

    def notify(self,topic,message):  

        Date=json.loads(message)                                            #from the bot we can choose one date or two dates that define the period over we want the statistics
        print("Received the following dates for the statistics: \n")
        print("Asking Thingspeak for the data...\n")
        data = requests.get('https://api.thingspeak.com/channels/123456/feeds.json')
        data = json.loads(data.text) 
        wetTemp = list(map(lambda n: float(n['field2']), data['feeds']))
        dryTemp = list(map(lambda n: float(n['field1']), data['feeds']))
        hum = list(map(lambda n: float(n['field3']), data['feeds']))
        created_at = list(map(lambda n:n['created_at'], data['feeds']))
        print(created_at)
        print(dryTemp)
        if 'end' in Date:                                                   #It means that there are two dates, so we want statistics over a period of time 
            start = Date["start"]
            end = Date["end"]
            start = time.mktime(datetime.datetime.strptime(start, "%Y-%m-%d").timetuple())
            print(start)
            end = time.mktime(datetime.datetime.strptime(end, "%Y-%m-%d").timetuple())
            #find closest start date and end date to the ones requested: 
            created_at = [i.split('T',1)[0] for i in created_at] 
            created_at_str = created_at
            created_at = [time.mktime(datetime.datetime.strptime(date, "%Y-%m-%d").timetuple()) for date in created_at]
            # dates_list = [datetime.datetime.strptime(date, '"%Y-%m-%d"').date() for date in dates]
            indStartDate = min(range(len(created_at)), key=lambda i: abs(created_at[i]- start))
            indEndDate = min(range(len(created_at)), key=lambda i: abs(created_at[i]- end))
            # end = created_at[idx]
            # indStartDate = [idx for idx, element in enumerate(created_at) if element == start]
            print("index of start date is: ")
            print(indStartDate)
            print("index of end date is: ")
            print(indEndDate)
            wetTemp = wetTemp[indStartDate:indEndDate]
            dryTemp = dryTemp[indStartDate:indEndDate]
            hum = hum[indStartDate:indEndDate]
            created_at = created_at[indStartDate:indEndDate]

            maxwet = max(wetTemp)
            maxdry = max(dryTemp)
            maxhum = max(hum)

            for element in wetTemp:
                if element == maxwet:
                    ind_maxwet = wetTemp.index(maxwet)
                    day_maxwet = created_at_str[ind_maxwet]
            for element in dryTemp:
                if element == maxdry:
                    ind_maxdry = dryTemp.index(maxdry)
                    print('ind_maxdry')
                    print(ind_maxdry)
                    day_maxdry = created_at_str[ind_maxdry]
                    print('day_maxdry')
                    print(day_maxdry)
            for element in hum:
                if element == maxhum:
                    ind_maxhum = hum.index(maxhum)
                    day_maxhum = created_at_str[ind_maxhum]

            minwet = min(wetTemp)
            mindry = min(dryTemp)
            minhum = min(hum)

            for element in wetTemp:
                if element == minwet:
                    ind_minwet = wetTemp.index(minwet)
                    day_minwet = created_at_str[ind_minwet]
            for element in dryTemp:
                if element == mindry:
                    ind_mindry = dryTemp.index(mindry)
                    day_mindry = created_at_str[ind_mindry]
            for element in hum:
                if element == minhum:
                    ind_minhum = hum.index(minhum)
                    day_minhum = created_at_str[ind_minhum]
            
            avg_wet = sum(dryTemp)/len(dryTemp)
            avg_dry = sum(wetTemp)/len(wetTemp)
            avg_hum = sum(hum)/len(hum)

            for element in wetTemp:
                if element == avg_wet:
                    ind_avg_wet = wetTemp.index(avg_wet)
                    day_avg_wet = created_at_str[ind_avg_wet]
            for element in dryTemp:
                if element == avg_dry:
                    ind_avg_dry = dryTemp.index(avg_dry)
                    day_avg_dry = created_at_str[ind_avg_dry]
            for element in hum:
                if element == avg_hum:
                    ind_avg_hum = hum.index(avg_hum)
                    day_avg_hum = created_at_str[ind_avg_hum]

            #Create the json file with the statistics to send to the bot
            statistics = {
                "wet":{"min":[round(minwet,2),str(day_minwet)],"max":[round(maxwet,2),str(day_maxwet)],"average":round(avg_wet,2)},
                "dry":{"min":[round(mindry,2),str(day_mindry)],"max":[round(maxdry,2),str(day_maxdry)],"average":round(avg_dry,2)},
                "humidity":{"min":[round(minhum,2),str(day_minhum)],"max":[round(maxhum,2),str(day_maxhum)],"average":round(avg_hum,2)},
            }

            pprint(statistics)

            print("Received data of the requested dates from Thingspeak\n")
        else: #we have just one day
            print("in in the if")
            start = Date["start"]
            #start = min(range(len(created_at)), key=lambda i: abs(created_at[i]- start))

            created_at = [i.split('T',1)[0] for i in created_at]

            indStartDate = [idx for idx, element in enumerate(created_at) if element == start]
            
            wetTemp = wetTemp[indStartDate[0]:indStartDate[-1]]
            dryTemp = dryTemp[indStartDate[0]:indStartDate[-1]]
            hum = hum[indStartDate[0]:indStartDate[-1]]
            created_at = created_at[indStartDate[0]:indStartDate[-1]]

            maxwet = max(wetTemp)
            maxdry = max(dryTemp)
            maxhum = max(hum)

            minwet = min(wetTemp)
            mindry = min(dryTemp)
            minhum = min(hum)

            
            avg_wet = sum(dryTemp)/len(dryTemp)
            avg_dry = sum(wetTemp)/len(wetTemp)
            avg_hum = sum(hum)/len(hum)

            #Create the json file with the statistics to send to the bot
            statistics = {
                "wet":{"min":round(minwet,2),"max":round(maxwet,2),"average":round(avg_wet,2)},
                "dry":{"min":round(mindry,2),"max":round(maxdry,2),"average":round(avg_dry,2)},
                "humidity":{"min":round(minhum,2),"max":round(maxhum,2),"average":round(avg_hum,2)},
            }

            pprint(statistics)
        self.client.myPublish(self.topicPub, statistics)
        print("Published statistics")

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
    conf = json.load(open('settings.json'))
    payload = conf["ServiceData"]
    catalog_URL=conf["catalogURL"]  
    service = registration(catalog_URL, payload)
    try: 
        service.register()
    except:
        print('Catalog not connected!')
        raise SystemExit

    subscribeTopic = conf["ServiceData"]['MQTT_Topic']["subscribeTopic"]
    publishTopic = conf["ServiceData"]['MQTT_Topic']["publishTopic"]
    info=(requests.get(catalog_URL+"/broker")).json()
    tsa=Statistics(info['broker']["url"],info['broker']["port"],subscribeTopic,publishTopic) 

    t1 = Update(1,conf['timeforupdate'],service)
    t1.start()
    t1.join()

    while True:
        time.sleep(60)

















