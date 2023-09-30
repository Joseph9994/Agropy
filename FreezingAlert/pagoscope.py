from matplotlib.patches import Polygon, Patch
import matplotlib.pyplot as plt
from os.path import exists
import os
from pagoscope import *

#We create this function in order to predict freezing from the incoming data of temperature and humidity. In particular we built a graph with three 
#areas (no freezing, possible freezing and freezing for sure) throw the use of different polygons. Depending on where the incoming two points of dry and wet temperature
#are on the graph we can decide the type of alert to send.

#Conditions:
#1) if we are in polygon1 ==> freezing for sure
#2) if we are in polygon2 ==> possible freezing (In this case: a future work is to analyse a lumen sensor in order to understand, based on the light on the sensor, if the freezing is more probable or not)


def pagoscope(dryBulb,wetBulb):
    if exists("output.jpg"):
        os.remove("output.jpg")

    if dryBulb <0 or (dryBulb >0 and wetBulb <0): #The dry temperature is always bigger than the dry one, so if the dry temperature is negative, the wet one will be negative as well. 
                                                  #in this case we will have freezing for sure and we ar enot gonna have a point on the graph because it is done just for positive numbers.  
                                                  # we are gonna send to the BOT just the message of freezing without the graph.                                         
        output = {"result" : 1} 
        print("Freezing for sure")
        return output

    if dryBulb > 16 or wetBulb > 20: 
        output = {"result" : 3} 
        print("No freezing")
        return output

    polygon1 = Polygon([(16,0), (0,0), (0,1), 
                        (1,1.6), (2,2.1), (3,2.5), 
                        (4,3), (5,3.6), (6,4), 
                        (7,4.45), (8,5), (9,5.4), 
                        (10,6), (11,6.45), (12,6.97), 
                        (13,7.3), (14,7.97), (15, 8.45), (16, 8.97)])

    polygon2 = Polygon([(16,0), (0,0), (0,2.3),
                        (1,3.2), (2,4), (3,4.7), 
                        (4,5), (5,5.7), (6,6), 
                        (7,6.65), (8,7), (9,7.6), 
                        (10,8), (11, 8.5), (12,9), 
                        (13, 9.3), (14,10), (15, 10.45), (16,11)])
    point = (dryBulb, wetBulb)

    condition1 = polygon1.contains_point(point) 
    condition2 = polygon2.contains_point(point)

    if condition1 == True:
        output = {"result" : 1} 
        print("Freezing for sure")
        #message = {"Freezing for sure"}
        plotPagoscope(dryBulb,wetBulb)
        return output
        
        
    elif condition2 == True:
        output = {"result" : 2}  
        print("Possible freezing")
        #message = {"Possible freezing"}
        plotPagoscope(dryBulb,wetBulb)
        return output

    else:
        output = {"result" : 3}
        print("No freezing")
        #message = {"No freezing"}
        plotPagoscope(dryBulb,wetBulb)
        return output

#We the below part we want to create the graph with the specific latest point of data and we save it in order to send to the BOT      
def plotPagoscope(dryBulb,wetBulb):
    polygon1 = Polygon([(16,0), (0,0), (0,1), 
                        (1,1.6), (2,2.1), (3,2.5), 
                        (4,3), (5,3.6), (6,4), 
                        (7,4.45), (8,5), (9,5.4), 
                        (10,6), (11,6.45), (12,6.97), 
                        (13,7.3), (14,7.97), (15, 8.45), (16, 8.97)])

    polygon2 = Polygon([(16,0), (0,0), (0,2.3),
                        (1,3.2), (2,4), (3,4.7), 
                        (4,5), (5,5.7), (6,6), 
                        (7,6.65), (8,7), (9,7.6), 
                        (10,8), (11, 8.5), (12,9), 
                        (13, 9.3), (14,10), (15, 10.45), (16,11)])
    point = (dryBulb, wetBulb)
    f2 = plt.figure(figsize=(10, 5))                            
    ax2 = plt.subplot(1, 2, 1)                                  
    ax2.set_title("Pagoscope")        

    ax2.add_patch(polygon2)
    polygon2.set_facecolor("yellow")
    polygon2.set_label("Possible Freezing")

    ax2.add_patch(polygon1)
    polygon1.set_facecolor("red")
    polygon1.set_label("Freezing for sure")

    plt.ylim(0,20)
    plt.xlim(0,16)

    x, y = point
    p= ax2.plot(x, y, marker="o", markersize=5, markeredgecolor="black", markerfacecolor="black")

    white_patch = Patch(color='white', label='No freezing')
    red_patch = Patch(color='red', label='Freezing for sure')
    yellow_patch = Patch(color='yellow', label='Possible freezing')
    plt.legend(handles=[white_patch, yellow_patch, red_patch], facecolor='#ECECEC')
    plt.xlabel("Dry Temperature [°C]")
    plt.ylabel("Wet Temperature [°C]")
    plt.grid()
    plt.savefig("output.jpg", bbox_inches='tight')
    # plt.show()
