#!/usr/bin/env python

# Written by Limor "Ladyada" Fried for Adafruit Industries, (c) 2015
# This code is released into the public domain

import time
import os
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

while True:
        # read the analog pin
        read_gas = readadc(gas_sensor, SPICLK, SPIMOSI, SPIMISO, SPICS)
        read_o2 = readadc(o2_sensor, SPICLK, SPIMOSI, SPIMISO, SPICS)
        measuredVout_o2 = read_o2*(3.3/1023)
        measuredVout_gas = read_gas*(3.3/1023)
        o2_conc = measuredVout_o2*0.1348
        o2_percent_conc = o2_conc*100

        if DEBUG:
                print "Reading Gas:", measuredVout_gas
                localtime = time.asctime( time.localtime(time.time()) )
                g = open("gas", "a")
                g.write(str(localtime))
                g.write("||")
                g.write("Gas Presence (V): ")
                g.write(str(measuredVout_gas))
                g.write("\n")
                g.close()
                print "Reading % O2:", o2_percent_conc
                o = open("oxygen", "a")
                o.write(str(localtime))
                o.write("||")
                o.write("Oxygen Concentration (%): ")
                o.write(str(o2_percent_conc))
                o.write("\n")
                o.close()
                 

        # hang out and do nothing for a half second
        time.sleep(30)
