import json 
import math

def wetBulb(temperature, humidity):
    
    #costanti
    P=1000              #pressione atmosferica in hPa
    previous_sign=1     #valore di addizione/sottrazione nel while
    incr=10             #valore di incremento/decremento per Tw

    #l'umidità deve essere data in range 0-1
    if humidity>1:  #vuol dire che è in %
        humidity_dec=humidity/100
    else:           #vuol dire che era già in range 0-1
        humidity_dec=humidity
    

    # Magnus-teten's Dew Point approximation
    a=17.27
    b=237.7
    alpha= ((a*temperature)/(b+temperature))+math.log(humidity_dec)
    Tdew= (b*alpha)/(a-alpha)                                                           

    # There are no exact methods, but only trial and error or approximation methods, 
    # like the one of Newton (tangent method)
    # we use the trial and error method
    e_diff=1       # it is the difference of vapor pressure between mixed air and saturated air
                   # we need it to enter the while cycle
    E = 6.112*math.exp(17.67*Tdew/(Tdew+243.5))
    Tw_guess=Tdew
    while (e_diff>0.05):
        # relation between temperature and vapor pressure: 
        # vapor pressure(E):=6.112*e^(17.67*T/243.5*T) # inside the formula e=nepero
        ew_guess=6.112*math.exp(17.67*Tw_guess/(Tw_guess+243.5))
        e_guess=ew_guess - P*(temperature-Tw_guess)*0.00066*(1+(0.00115*Tw_guess))

        Tw=Tw_guess

        e_diff= E - e_guess
        if e_diff > 0:
            sign = 1
        else:
            sign = -1

        # it is a trial and error method, we add or subtract a certain quantity (less and less) 
        if (previous_sign != sign):
                incr = incr/10
        
        Tw_guess=Tw_guess+incr*sign #increase for the temperature

        previous_sign=sign          #change for the following cycle
    print(f"The wet bulb temperature is: {Tw}")
    return Tw


#https://www.weather.gov/media/epz/wxcalc/rhTdFromWetBulb.pdf

    