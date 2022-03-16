import RPi.GPIO as GPIO
import dht11
from datetime import datetime
from time import sleep
from picamera import PiCamera
import ssl
import pymongo
import certifi
import uuid
import requests as requests
import os
import matplotlib.pyplot as plt
import pandas as pandas

# initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()
ca= certifi.where()
url="https://www.orf.at"
timeout=5
sensorId=hex(uuid.getnode())

camera = PiCamera()
#camera.start_preview()

attempt = 1
imageId = 0
while True:
        
        #Captuares jpgs depending on the number of attempts e.g. "1.jpg"
        camera.capture("/home/pi/Pictures/%s.jpg" % attempt)

        today = datetime.today()
        current_time = now.strftime("%H:%M")

        #read data using pin 4
        instance = dht11.DHT11(pin = 4)
        result = instance.read()
        #while result is not valid
        while not result.is_valid():
            instance = dht11.DHT11(pin = 4)
            result = instance.read()

        #creates a .txt file that will send a single line of data for long-term storage"
        with open("/home/pi/data/%s.txt" % attempt, "w") as file_object:
            file_object.write(str(today))
            file_object.write(";")
            file_object.write(str(current_time))
            file_object.write(";")
            file_object.write(str(result.temperature))
            file_object.write(";")
            file_object.write(str(result.humidity))
            file_object.write("\n")

        #Check if internet connection        
        try:
            request = requests.get(url, timeout=timeout)
            print("Connected to the Internet.")
            client = pymongo.MongoClient(
                "mongodb+srv://username:password@cluster0.nrs4u.mongodb.net/Cluster0?retryWrites=true&w=majority",
                tlsCAFile=ca)
            db = client.get_database('PJTwo')

            sensorId = hex(uuid.getnode())

            # If there were more attempts because no internet
            while(attempt>=1):
                p1 = open("/home/pi/Pictures/%s.jpg" % attempt, "rb")
                binary = bytes(p1.read())
                p1.close()

                if(os.path.exists("/home/pi/Pictures/visualisation.jpg")): #when the diagramm exists
                    p2 = open("/home/pi/Pictures/visualisation.jpg", "rb")
                    binary = bytes(p2.read())
                    os.remove("/home/pi/Pictures/visualisation.jpg") # remove the diagramm

                # Input data, date|temperature|humidity
                with open('/home/pi/data/%s.txt' % attempt, "r") as f1:
                    time = f1.read(19)
                    temp = f1.read(14)
                    temperatureData = f1.read(4)
                    temp2 = f1.read(1)
                    humidityData = f1.read(4)
                f1.close()
                imageId+=1
                # Combine data into one string
                collection = db.Data
                datafull = {"timestamp": time, "humidity": humidityData, "temperature": temperatureData,
                        "imageId": imageId, "sensorId": sensorId}
                # Insert data into collection
                collection.insert_one(datafull)
                collection = db.Images
                imagefull = {"imageId": imageId, "image": binary}
                collection.insert_one(imagefull)
                print("Data transfer complete.")
                attempt -= 1
            attempt = 1

        except (requests.ConnectionError, requests.Timeout) as exception:
            print("No internet connection.")
            attempt +=1
        sleep(3600)
