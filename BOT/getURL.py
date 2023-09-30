import requests

#This script should be implemented in the BOT, it gets the url that ngrok creates for nodered. Should all be running on the same computer.
# Type "ngrok start nodered" in terminal
# Question: should the installation of nodered, ngrok and telegram bot stuff be included in the dockerfile? 
#  
r= requests.get('http://localhost:4040/api/tunnels/nodered') 
publicUrl=r.json()["public_url"]+'/ui'
print(publicUrl)