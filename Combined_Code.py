#!/usr/bin/env python

# Written by Limor "Ladyada" Fried for Adafruit Industries, (c) 2015
# This code is released into the public domain
import os
import serial
import struct
import sys
import datetime
import struct
import smbus
import time
import os
import math
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
DEBUG = 1

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout

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
    cmd_zero_sensor = "\xff\x01\x87\x00\x00\x00\x00\x00\x78"
    cmd_span_sensor = "\xff\x01\x88\x07\xD0\x00\x00\x00\xA0"
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

# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25

# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

# 10k trim pot connected to adc #0
gas_sensor = 0;
o2_sensor = 1;
c = CO2()

while True:
        # read the analog pin
        read_gas = readadc(gas_sensor, SPICLK, SPIMOSI, SPIMISO, SPICS)
        read_o2 = readadc(o2_sensor, SPICLK, SPIMOSI, SPIMISO, SPICS)
        measuredVout_o2 = read_o2*(3.3/1023)
        measuredVout_gas = read_gas*(3.3/1023)
        o2_conc = measuredVout_o2*0.1348
        o2_percent_conc = o2_conc*100
     
       

        if DEBUG:
                print "Gas:", measuredVout_gas
                print "O2%:", o2_percent_conc, "%"
                 
        try:
            #CO2 sensor calib
            time.sleep(0.5)
            co2 = c.calibrateZero()
            time.sleep(0.5)
            print "CO2[ppm, C]:",c.read()


        except IndexError:
            print "Unable to read"
        except KeyboardInterrupt:
            print "Exiting"
            sys.exit(0)
        # hang out and do nothing for a half second
        time.sleep(3)
