#!/usr/bin/env python3

# ------------------------------------------------------------
# File:   window.py
# Author: Dan King
# Edited by Casey Brennan
#
# This script needs pigpiod to be running (http://abyz.co.uk/rpi/pigpio/)
# ------------------------------------------------------------


##### Configuration #####

# GPIO pin number
pin = 21

# Yahoo! woeid (location ID)
#For Orlando,Fl
woeid = "2466256"

# Brightness levels (percent)
cloudy = 30
mixed = 50
sunny = 90

# Config file, persistent configs
confFile = '/var/www/html/window.conf'

# Debug, show output
debug = True

##### End configuration #####


import requests,time,pigpio,json

# Load config file for cache/settings
f = open(confFile, 'r')
settings = json.loads(f.read())
f.close()

if not int(settings['auto']):
    if debug:
        print('Auto brightness disabled, exiting...')
    exit()
    
url = "https://query.yahooapis.com/v1/public/yql?q="
url = url + "select item.condition, astronomy.sunrise, astronomy.sunset "
url = url + "from weather.forecast where woeid=" + woeid + "&format=json"

# Refresh weather data every 15 minutes
if (settings['timestamp'] + 900) < time.time():
    try:
        if debug:
            print('Getting Yahoo! weather data...')
            
        data = requests.get(url, timeout=10).json()
    
        # Save/cache values
        settings['auto'] = 1
        settings['weather'] = int(data['query']['results']['channel']['item']['condition']['code'])
        settings['weatherText'] = data['query']['results']['channel']['item']['condition']['text']
        settings['sunrise'] = data['query']['results']['channel']['astronomy']['sunrise']
        settings['sunset'] = data['query']['results']['channel']['astronomy']['sunset']
        settings['timestamp'] = round(time.time())
        
        f = open(confFile, 'w')
        f.write(json.dumps(settings))
        f.close()
        
    except:
        print("Error: Unable to connect to Yahoo! API")


# Set max brightness based on weather
if settings['weather'] < 23 or settings['weather'] in [26,41,42,43]: 
    maxBright = cloudy
elif settings['weather'] >= 32 and settings['weather'] <= 36:
    maxBright = sunny
else:
    maxBright = mixed

if debug:
    print("Weather code: " + str(settings['weather']) + " (" + settings['weatherText'] + "), Sunrise: " + settings['sunrise'] + ", Sunset: " + settings['sunset'])
    print("Max brightness: " + str(maxBright))

# Current time
cTime = time.localtime()
now = time.time()


# Sunrise: start brightening 20 mins before, end 70 mins after
sunriseTime = str(cTime[0]) + '-' + str(cTime[1]) + '-' + str(cTime[2]) + ' ' + settings['sunrise']
sunriseStart = int(time.mktime(time.strptime(sunriseTime, "%Y-%m-%d %I:%M %p"))) - 1200
sunriseEnd = sunriseStart + 5400

# Sunset: start dimming 75 mins before, end 15 mins after
sunsetTime = str(cTime[0]) + '-' + str(cTime[1]) + '-' + str(cTime[2]) + ' ' + settings['sunset']
sunsetStart = int(time.mktime(time.strptime(sunsetTime, "%Y-%m-%d %I:%M %p"))) - 4500
sunsetEnd = sunsetStart + 5400


# Determine the current brightness
if now >= sunriseStart and now <= sunriseEnd:
    elapsed = now - sunriseStart
    percent = elapsed / 5400
    brightness = maxBright * percent
    timeOfDay = "Sunrise"
        
elif now > sunriseEnd and now < sunsetStart:
    brightness = maxBright
    timeOfDay = "Day"

elif now >= sunsetStart and now <= sunsetEnd:
    elapsed = sunsetEnd - now
    percent = elapsed / 5400
    brightness = maxBright * percent
    timeOfDay = "Sunset"
    
else:
    brightness = 0
    timeOfDay = "Night"

if debug:
    print(timeOfDay + ", Brightness: " + str(brightness * 2.55))

# Change the brightness quicker at the beginning of the
# transition, then slowing near the end
def getChangeAmt(current, target):
    return round(abs(current-target) / 10) + 1
    
    
# Set the brightness gradually
pi = pigpio.pi()
currentBrightness = pi.get_PWM_dutycycle(pin)
targetBrightness = brightness * 2.55

# Brightness increasing
if targetBrightness > currentBrightness:
    while currentBrightness <= targetBrightness:
        pi.set_PWM_dutycycle(pin, currentBrightness)
        
        amt = getChangeAmt(currentBrightness, targetBrightness)
            
        currentBrightness = currentBrightness + amt
        time.sleep(0.05)

# Brightness decreasing
elif targetBrightness < currentBrightness:
    while currentBrightness >= targetBrightness:
        pi.set_PWM_dutycycle(pin, currentBrightness)
        
        amt = getChangeAmt(currentBrightness, targetBrightness)
        
        currentBrightness = currentBrightness - amt
        time.sleep(0.05)
