import pigpio
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
from time import sleep

GPIO.setwarnings(False)


RX=16

INTERVAL=30000000

start_tick = None
last_tick = None
low_ticks = 0
high_ticks = 0

GPIO.setmode(GPIO.BCM)
DEBUG = 1

###DUST SENSOR CODE BEGIN###
def results(interval):
   global low_ticks, high_ticks
   if interval != 0:
      ratio = float(low_ticks)/float(interval)*10.0
      conc = 1.1*pow(ratio,3)-3.8*pow(ratio,2)+520*ratio+0.62;
      print("[Ratio, pcs/0.01cf]") 
      print("{:.1f}, {}".format(ratio, int(conc)))
      dust = open("ds_dust", "w")
      dust.write("Ratio,pcs/0.01cf\n")
      dust.write("{:.1f}, {}".format(ratio, int(conc)))
      dust.close()
      time.sleep(1)
      

def cbf(gpio, level, tick):
   global start_tick, last_tick, low_ticks, high_ticks, run
   if start_tick is not None:
      ticks = pigpio.tickDiff(last_tick, tick)
      last_tick = tick
      if level == 0: # Falling edge.
         high_ticks = high_ticks + ticks
      else: # Rising edge.
         low_ticks = low_ticks + ticks
      interval = pigpio.tickDiff(start_tick, tick)
      if interval >= INTERVAL:
         results(interval)
         start_tick = tick
         last_tick = tick
         low_ticks = 0
         high_ticks = 0
   else:
      start_tick = tick
      last_tick = tick


####DUST SENSOR CODE END###
      
pi = pigpio.pi() # Connect to local Pi.

pi.set_mode(RX, pigpio.INPUT)

cb = pi.callback(RX, pigpio.EITHER_EDGE, cbf)

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
ser = serial.Serial('/dev/ttyS0',  9600, timeout = 1)	#Open the serial port at 9600 baud

#init serial
ser.flush()

############# carbon dioxide CO2 #####################
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
SPICLK = 21
SPIMISO = 6
SPIMOSI = 13
SPICS = 26

# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

# 10k trim pot connected to adc #0
gas_sensor = 0;
o2_sensor = 1;
c = CO2()


#########||||||||||******#       START OF PROCESS     #******||||||||||#########
while True:
                read_gas = readadc(gas_sensor, SPICLK, SPIMOSI, SPIMISO, SPICS)
                read_o2 = readadc(o2_sensor, SPICLK, SPIMOSI, SPIMISO, SPICS)
                measuredVout_o2 = read_o2*(3.3/1023)
                measuredVout_gas = read_gas*(3.3/1023)
                o2_conc = measuredVout_o2*0.1348
                o2_percent_conc = o2_conc*100
                print "Reading Gas:", measuredVout_gas
                localtime = time.asctime( time.localtime(time.time()) )
                g = open("ds_gas", "w")
                g.write("Gas Presence (V):\n")
                g.write(str(measuredVout_gas))
                g.close()
                print "Reading % O2:", o2_percent_conc
                o = open("ds_o2", "w")
                o.write("Oxygen % Conc:  \n")
                o.write(str(o2_percent_conc))
                o.close()
                try:
                    co2 = c.calibrateZero()
                    time.sleep(0.5)
                    print "CO2[ppm, C]:",c.read()
                    co = open("ds_co2", "w")
                    co.write("CO2 [ppm, C]:\n")
                    co.write(str(c.read()))
                    co.close()
                except IndexError:
                    print "Unable to read"
                    co = open("ds_co2", "w")
                    co.write("CO2 sensor error")
                    co.close()
                except KeyboardInterrupt:
                    print "Exiting"
                    sys.exit(0)

time.sleep(3600)

cb.cancel() # Cancel callback.

pi.stop() # Disconnect from local Pi.
                



       
                
