from logging import raiseExceptions
import time
import json
import requests
from registration import *
import telepot
from telepot.loop import MessageLoop 
from telepot.namedtuple import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from MyMQTT import *
from datetime import datetime
import re
import threading
import base64

# The BOT script allows the user to interface with our services, letting them choose from the different functionalities. 
# MQTT methods:
#   subscriber to retrieve info on the  freezing status, the inactive sensors and the statistics. 
#   publisher to send the user-selected date over which the statistics will be calculated. 
# HTTP methods:
#   get request to ThinkSpeak to receive the latest data of the sensors 
#   get request to nodeRed to retrieve the data trends
#   get/post/put request to the catalog


class MQTTbot:
    exposed=True
    def __init__(self, token, broker, port, FreezeSubTopic,DatePubTopic,StatTopic,brokenNodeSubTopic):
        self.tokenBot = token
        self.bot = telepot.Bot(self.tokenBot)

        self.chatIDs=[]
        self.client = MyMQTT("telegramBotIoT", broker, port, self)
        self.client.start()
        self.FreezeSubTopic = FreezeSubTopic
        self.DatePubTopic = DatePubTopic
        self.brokenNodeSubTopic = brokenNodeSubTopic
        self.StatTopic = StatTopic
        self.client.mySubscribe(FreezeSubTopic)
        self.client.mySubscribe(brokenNodeSubTopic)
        self.client.mySubscribe(StatTopic)
        self.client.mySubscribe("/pagoGraph")

        MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()

    def on_chat_message(self, msg):
        content_type, chat_type, chat_ID = telepot.glance(msg)
        command = msg['text']
        self.chat_IDcurrUser = chat_ID
        
        # Keyboards: 
        homeKeyboard = ReplyKeyboardMarkup(keyboard=[
                        ['Data trends'], 
                        ['Statistics'], 
                        ['Latest Data'],
                        ['Add Sensor']
                    ])
        sensors=(requests.get(catalog_URL+"/sensors")).json()                                                          # Retrieving all the sensors from the catalog 
        sensorKeyboard = []
        TSchannelID = {}
        sensorCommand = []
        for element in sensors['sensors']:
            sensorKeyboard.append([element["sensorName"]])                                                             # Adding all sensors as command keyboard
            sensorCommand.append(element["sensorName"])                                                                # Adding all sensors name in sensorCommand list
            TSchannelID[f'{element["sensorName"]}'] = element["TSchannelID"]                                           # Creating the dictiolary linking each sensor name with its thinkspeak channel ID
 
        sensorKeyboard.append(["back"])                                                                                # Adding the command keayboard "back" to come bask to the previously choices
        # sensorKeyboard.remove(['SimulatedSensor'])

        # Handling commands: 
        if command == '/start':
            self.chatIDs.append(chat_ID)
            self.bot.sendMessage(chat_ID, 'How can I help you? ', reply_markup=homeKeyboard)  
        if command ==  'back':    
            self.bot.sendMessage(chat_ID, 'How can I help you? ', reply_markup=homeKeyboard)  

        #Latest Data 
        elif command == 'Latest Data':                                                                                # If the comman selected by the user is this one, he wants to receive the latest temperature and humidity
            nodesKeyboard = ReplyKeyboardMarkup(keyboard=sensorKeyboard)                                               # Showing in the telegram bot all the possible sensor commands
            self.bot.sendMessage(chat_ID, 'Which node data do you want to see?', reply_markup=nodesKeyboard)           # Choise from which one of the sensor you want the latest data 
        
        elif command in sensorCommand:                                                                                 # If the press botton is one of the working sensor, perform the lines below
            self.bot.sendMessage(chat_ID, 'Retrieving latest data...')                                                # Sendind a feedback message of retrieving latest data from the selected sensor command
            node = TSchannelID[msg['text']]                                                                            # Take the name of the selected sensor
            try: 
                r = requests.get(f'https://api.thingspeak.com/channels/{node}/feeds/last.json')                        # Retriving all the last data of the selected sensor from thinkspeak
                data = json.loads(r.text)

                dryTemp = data['field1']                                                                               # Retrieving just the last dry temperature
                # wetTemp = round(data['field2'],2)   
                wetTemp = round(float(data['field2']),2)  
                                                                                  # Retrieving just the last wet temperature
                hum = data['field3']                                                                                   # Retrieving just the last humidity
                time = datetime.fromtimestamp(float(data['field4']))                                                   # Retrieving the timestamp of the selected sensor
            
                tosend = f'Dry temperature: {dryTemp}\nWet temperature: {wetTemp}\nHumidity: {hum}\nData from {time}'  # making the message with the latest data to send to the bot
                self.bot.sendMessage(chat_ID, tosend)
            except:
                self.bot.sendMessage(chat_ID, 'an error occured with this node')
        #Data trends
        elif command == 'Data trends':                                                              # If the comman selected by the user is this one, he wants to receive the data trends
            try: 
                r= requests.get('http://localhost:4040/api/tunnels/nodered')                        # Retrieving from nodered the data trends
                publicURL=r.json()["public_url"]+'/ui'
                self.bot.sendMessage(chat_ID, f'You can find the trends at this URL:\n{publicURL}') # Sending to the telegram bot the public URL of nodered where there are the data trends
            except: 
                self.bot.sendMessage(chat_ID, 'Error: cannor retrieve link. Node-red or ngrok may not be working')

        #Statistics
        elif command == 'Statistics':                                                               # If the comman selected by the user is this one, he wants to receive statistics from the storage data. The user can choose one data on two data as a range over he want the statistics data.
            
            #Telling to the user how to specify the data format for one or multiple days
            self.bot.sendMessage(chat_ID, 'Tell me a date with the following formats: \n\n ▪️ *aaaa-mm-dd* if you want statistics over a day \n\n ▪️ *aaaa-mm-gg aaaa-mm-gg* if you want statistics over a range of days',parse_mode= 'Markdown', reply_markup=ReplyKeyboardRemove()) 
        
        elif bool(re.match("\d\d\d\d-\d\d-\d\d",command)) or bool(re.match("\d\d\d\d-\d\d-\d\d \d\d\d\d-\d\d-\d\d",command)):
            dateString=command
            if len(dateString)==10:                                                                 # If the length of the recieved string is 10, we are in the first case and the used chose just one day
                payload= {"start": dateString}
            else: #Otherwise he chose  two days 
                startEnd=dateString.split(" ")                                                      # Deviding the stard and the end day, splitting them with the - character
                start=startEnd[0]              
                end=startEnd[1]
                print(f"start:{start}, end:{end}")  
                #Creating the paylod with the two date to send to the broker           
                payload= {
                    "start": start,
                    "end": end
                }
            self.client.myPublish(self.DatePubTopic,payload) 
            print("published")

            try:
                startDate= command
                print(type(startDate))
            except:
                self.bot.sendMessage(chat_ID, 'Error in date input, retry', reply_markup=ReplyKeyboardRemove()) 
                print("nulla")
        
        elif command == 'Add Sensor':
            self.bot.sendMessage(chat_ID, 'To add a new sensor fill out this form: \n https://sites.google.com/view/agropy-addsensor/home-page', reply_markup=homeKeyboard)

    def notify(self,topic,message): 
        if topic.find('StatusFreezing') != -1:                                                          # If there is an incoming message under StatusFreezing topic, we want to analyze the result in order to send the alert message to the BOT
            msg =json.loads(message)
            FreezingStatus = msg['result']
            if FreezingStatus == 1:                                                                     # If the status is equal to 1 it means there will be freezing for sure
                tosend=f"Freezing"
            elif FreezingStatus == 2:                                                                   # If the status is equal to 2 it means there will be a possible freezing 
                tosend=f"Possible freezing"
            elif FreezingStatus == 3:                                                                   # If the status is equal to 3 it means there will be no freezing, so no message will be send to the telegram bot
                print('No freezing')
                return None
            else:
                raise Exception('There was an error in the package that arrived')
            for chat_ID in self.chatIDs: 
                self.bot.sendMessage(chat_ID, text=tosend)
            if 'graph' in msg.keys():                                                                   # If there is the key 'graph' in the payload perforfe the lines below
                img = json.loads(message)['graph']
                img = img.encode('ascii')
                final_img = base64.b64decode(img)                                                       # decode the encode ascii to base 64
                open('receivedImg.jpg','wb').write(final_img)                                           # save the base 64 image in a new file.jpg
                # bot.sendPhoto(chat_ID,Buffer.from(final_img,'base64'))
                print(self.chatIDs)
                for chat_ID in self.chatIDs: 
                    self.bot.sendPhoto(chat_ID, photo=open('receivedImg.jpg', 'rb'))                    # send the image to the bot
            else: 
                self.bot.sendMessage(chat_ID, text='Pagoscope graph is not applicable to these values') # There is no image to send to the bot because one or both the incoming values are negative 
        elif topic.find('status') != -1:   
            info = json.loads(message)
            status = info['status']           
            if status == 0:                                                                             # One sensors is not working anyomore, we retrieve the latitude and longitude in order to send the location to the bot
                latitude = info['latitude']
                longitude = info['longitude']
                node = info['sensorName']
                tosend = f"{node} is no longer working! Here's its locations:"
                for chat_ID in self.chatIDs: 
                    self.bot.sendMessage(chat_ID, text=tosend)                                          # send the message of nonworking sensor to the bot
                    self.bot.sendLocation(chat_ID, latitude, longitude)                                 # send the location of the nonworking sensor to the bot
        elif topic.find('Statistic') != -1:                                                             # If the topic is this one it means that Statistics service published statistics 
            message = json.loads(message)
            tosend = json.dumps(message)
            tosend = tosend[1:-2]
            #The lines below have be done just to have a nice indentation of the message to send to the bot
            tosend = tosend.replace('"','')
            tosend = tosend.replace('{',' \n\t')
            tosend = tosend.replace('},','\n\n')
            tosend = tosend.replace('[','')
            tosend = tosend.replace('], ','\n\t')
            tosend = tosend.replace('wet','*Wet temperature*')
            tosend = tosend.replace('dry','*Dry temperature*')
            tosend = tosend.replace('humidity','*Humidity*')

            self.bot.sendMessage(self.chat_IDcurrUser, tosend,parse_mode= 'Markdown')                             # Sending the message with the statistics data to the telegram bot user
        

class Update(threading.Thread):                                                                           # Multithreading for doing the update (the timestamp of the service is continuosly updated)
    def __init__(self, threadID,time_update,sr):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.time_update=time_update
        self.sr=sr
    def run(self):
        while True:
            self.sr.update()
            time.sleep(self.time_update)                                                                   # Updating each time_update seconds (it is specified in settings)                   

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

    token = conf['telegramToken']                                                                         # Taking the telegram token from the settings file
    info=(requests.get(catalog_URL+"/broker")).json()                                                     # Retrieving the broker information from the catalog
    FreezeSubTopic = conf["ServiceData"]["MQTT_Topic"]["FreezeSubTopic"]                                  # Retrieving the topic of the status freezing 
    DatePubTopic = conf["ServiceData"]["MQTT_Topic"]["DatePubTopic"]                                      # The topic to which we publish the start and the end date over the statistics will be calculated 
    brokenNodeSubTopic = conf["ServiceData"]["MQTT_Topic"]["brokenNodeSubTopic"]                          # Retrieving the topic of the status of the inactive sensors
    statTopic = conf["ServiceData"]["MQTT_Topic"]["statTopic"]                                            # Retrieving statistic topic
    sb=MQTTbot(token,info['broker']["url"],info['broker']["port"],FreezeSubTopic,DatePubTopic,statTopic,brokenNodeSubTopic)

    t1 = Update(1,conf['timeforupdate'],service)
    t1.start()
    t1.join()

    while True:
        time.sleep(1)

