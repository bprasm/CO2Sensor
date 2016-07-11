#!/usr/bin/env python
########################################################################                                                                  
# Calibration and read of the CO2 sensor MH-Z16
# according to the datasheet : http://www.seeedstudio.com/wiki/images/c/ca/MH-Z16_CO2_datasheet_EN.pdf
# output value directly in ppm
# 			                                                         
# These files have been made available online through a Creative Commons Attribution-ShareAlike 3.0  license.
# (http://creativecommons.org/licenses/by-sa/3.0/)           
########################################################################
#In order to get /dev/ttys0 to open, you need to run the following commands
#sudo chown <to-myself> /dev/ttyS0
#sudo chgrp <to-myself> /dev/ttyS0
#sudo chmod 666 OR 777 /dev/ttyS0
import os
import serial, time
import math
import RPi.GPIO as GPIO
import struct
import sys
import datetime
import struct
import smbus


#co2 sensor
#use an external usb to serial adapter
ser = serial.Serial('/dev/ttyS0',  9600, timeout = 1)	#Open the serial port at 9600 baud

#init serial
ser.flush()


############# carbon dioxid CO2 #####################
class CO2:
#inspired from c code of http://www.seeedstudio.com/wiki/Grove_-_CO2_Sensor
#Gas concentration= high level *256+low level
    inp =[]
    cmd_zero_sensor = "\xff\x87\x87\x00\x00\x00\x00\x00\xf2"
    cmd_span_sensor = "\xff\x87\x87\x00\x00\x00\x00\x00\xf2"
    cmd_get_sensor = "\xff\x01\x86\x00\x00\x00\x00\x00\x79"
    def read(self):
        try:
          while True:
                ser.write(CO2.cmd_get_sensor)
                CO2.inp = ser.read(9)
                high_level = struct.unpack('B',CO2.inp[2])[0]
                low_level = struct.unpack('B',CO2.inp[3])[0]
                temp_co2  =  struct.unpack('B',CO2.inp[4])[0] - 40

                #output in ppm
                conc = high_level*256+low_level
                return [conc,temp_co2]

        except IOError:
                return [-1,-1]

    def calibrateZero(self):
        try:
             ser.write(CO2.cmd_zero_sensor)
             

        except IOError:
                print "CO2 sensor calibration error"

    def calibrateSpan(self):
        try:
          while True:
                #ser.write(CO2.cmd_zero_sensor)
                print "CO2 sensor span calibrated"
                break

        except IOError:
                print "CO2 sensor calibration error"

########################################################################################################
#############   MAIN
########################################################################################################
# following the specs of the sensor :
# read the sensor, wait 3 minutes, set the zero, read the sensor
c = CO2()

while True:
    try:
        #CO2 sensor calib
    
        time.sleep(2)
        co2 = c.calibrateZero()
        time.sleep(2)

        print "[ppm, C]:",c.read()
        localtime = time.asctime( time.localtime(time.time()) )
        per = open("co2", "a")
        per.write(str(localtime))
        per.write("||")
        per.write("ppm, C] ")
        per.write(str(c.read()))
        per.write("\n")
        per.close()


    except IndexError:
        print "Unable to read"
    except KeyboardInterrupt:
        print "Exiting"
        sys.exit(0)
