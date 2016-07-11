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
from threading import Thread

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

###LCD DISPLAY CODE START###
class Adafruit_CharLCD:

    # commands
    LCD_CLEARDISPLAY            = 0x01
    LCD_RETURNHOME              = 0x02
    LCD_ENTRYMODESET            = 0x04
    LCD_DISPLAYCONTROL          = 0x08
    LCD_CURSORSHIFT             = 0x10
    LCD_FUNCTIONSET             = 0x20
    LCD_SETCGRAMADDR            = 0x40
    LCD_SETDDRAMADDR            = 0x80

    # flags for display entry mode
    LCD_ENTRYRIGHT              = 0x00
    LCD_ENTRYLEFT               = 0x02
    LCD_ENTRYSHIFTINCREMENT     = 0x01
    LCD_ENTRYSHIFTDECREMENT     = 0x00

    # flags for display on/off control
    LCD_DISPLAYON               = 0x04
    LCD_DISPLAYOFF              = 0x00
    LCD_CURSORON                = 0x02
    LCD_CURSOROFF               = 0x00
    LCD_BLINKON                 = 0x01
    LCD_BLINKOFF                = 0x00

    # flags for display/cursor shift
    LCD_DISPLAYMOVE             = 0x08
    LCD_CURSORMOVE              = 0x00

    # flags for display/cursor shift
    LCD_DISPLAYMOVE             = 0x08
    LCD_CURSORMOVE              = 0x00
    LCD_MOVERIGHT               = 0x04
    LCD_MOVELEFT                = 0x00

    # flags for function set
    LCD_8BITMODE                = 0x10
    LCD_4BITMODE                = 0x00
    LCD_2LINE                   = 0x08
    LCD_1LINE                   = 0x00
    LCD_5x10DOTS                = 0x04
    LCD_5x8DOTS                 = 0x00



    def __init__(self, pin_rs=27, pin_e=22, pins_db=[25, 24, 23, 18], GPIO = None):
        # Emulate the old behavior of using RPi.GPIO if we haven't been given
        # an explicit GPIO interface to use
        if not GPIO:
                import RPi.GPIO as GPIO
                self.GPIO = GPIO
                self.pin_rs = pin_rs
                self.pin_e = pin_e
                self.pins_db = pins_db

                self.GPIO.setup(self.pin_e, GPIO.OUT)
                self.GPIO.setup(self.pin_rs, GPIO.OUT)

                for pin in self.pins_db:
                        self.GPIO.setup(pin, GPIO.OUT)

        self.write4bits(0x33) # initialization
        self.write4bits(0x32) # initialization
        self.write4bits(0x28) # 2 line 5x7 matrix
        self.write4bits(0x0C) # turn cursor off 0x0E to enable cursor
        self.write4bits(0x06) # shift cursor right

        self.displaycontrol = self.LCD_DISPLAYON | self.LCD_CURSOROFF | self.LCD_BLINKOFF

        self.displayfunction = self.LCD_4BITMODE | self.LCD_1LINE | self.LCD_5x8DOTS
        self.displayfunction |= self.LCD_2LINE

        """ Initialize to default text direction (for romance languages) """
        self.displaymode =  self.LCD_ENTRYLEFT | self.LCD_ENTRYSHIFTDECREMENT
        self.write4bits(self.LCD_ENTRYMODESET | self.displaymode) #  set the entry mode

        self.clear()


    def begin(self, cols, lines):

        if (lines > 1):
                self.numlines = lines
                self.displayfunction |= self.LCD_2LINE
                self.currline = 0


    def home(self):

        self.write4bits(self.LCD_RETURNHOME) # set cursor position to zero
        self.delayMicroseconds(3000) # this command takes a long time!
        

    def clear(self):

        self.write4bits(self.LCD_CLEARDISPLAY) # command to clear display
        self.delayMicroseconds(3000)    # 3000 microsecond sleep, clearing the display takes a long time


    def setCursor(self, col, row):

        self.row_offsets = [ 0x00, 0x40, 0x14, 0x54 ]

        if ( row > self.numlines ): 
                row = self.numlines - 1 # we count rows starting w/0

        self.write4bits(self.LCD_SETDDRAMADDR | (col + self.row_offsets[row]))


    def noDisplay(self): 
        """ Turn the display off (quickly) """

        self.displaycontrol &= ~self.LCD_DISPLAYON
        self.write4bits(self.LCD_DISPLAYCONTROL | self.displaycontrol)


    def display(self):
        """ Turn the display on (quickly) """

        self.displaycontrol |= self.LCD_DISPLAYON
        self.write4bits(self.LCD_DISPLAYCONTROL | self.displaycontrol)


    def noCursor(self):
        """ Turns the underline cursor on/off """

        self.displaycontrol &= ~self.LCD_CURSORON
        self.write4bits(self.LCD_DISPLAYCONTROL | self.displaycontrol)


    def cursor(self):
        """ Cursor On """

        self.displaycontrol |= self.LCD_CURSORON
        self.write4bits(self.LCD_DISPLAYCONTROL | self.displaycontrol)


    def noBlink(self):
        """ Turn on and off the blinking cursor """

        self.displaycontrol &= ~self.LCD_BLINKON
        self.write4bits(self.LCD_DISPLAYCONTROL | self.displaycontrol)


    def noBlink(self):
        """ Turn on and off the blinking cursor """

        self.displaycontrol &= ~self.LCD_BLINKON
        self.write4bits(self.LCD_DISPLAYCONTROL | self.displaycontrol)


    def DisplayLeft(self):
        """ These commands scroll the display without changing the RAM """

        self.write4bits(self.LCD_CURSORSHIFT | self.LCD_DISPLAYMOVE | self.LCD_MOVELEFT)


    def scrollDisplayRight(self):
        """ These commands scroll the display without changing the RAM """

        self.write4bits(self.LCD_CURSORSHIFT | self.LCD_DISPLAYMOVE | self.LCD_MOVERIGHT);


    def leftToRight(self):
        """ This is for text that flows Left to Right """

        self.displaymode |= self.LCD_ENTRYLEFT
        self.write4bits(self.LCD_ENTRYMODESET | self.displaymode);


    def rightToLeft(self):
        """ This is for text that flows Right to Left """
        self.displaymode &= ~self.LCD_ENTRYLEFT
        self.write4bits(self.LCD_ENTRYMODESET | self.displaymode)


    def autoscroll(self):
        """ This will 'right justify' text from the cursor """

        self.displaymode |= self.LCD_ENTRYSHIFTINCREMENT
        self.write4bits(self.LCD_ENTRYMODESET | self.displaymode)


    def noAutoscroll(self): 
        """ This will 'left justify' text from the cursor """

        self.displaymode &= ~self.LCD_ENTRYSHIFTINCREMENT
        self.write4bits(self.LCD_ENTRYMODESET | self.displaymode)


    def write4bits(self, bits, char_mode=False):
        """ Send command to LCD """

        self.delayMicroseconds(1000) # 1000 microsecond sleep

        bits=bin(bits)[2:].zfill(8)

        self.GPIO.output(self.pin_rs, char_mode)

        for pin in self.pins_db:
            self.GPIO.output(pin, False)

        for i in range(4):
            if bits[i] == "1":
                self.GPIO.output(self.pins_db[::-1][i], True)

        self.pulseEnable()

        for pin in self.pins_db:
            self.GPIO.output(pin, False)

        for i in range(4,8):
            if bits[i] == "1":
                self.GPIO.output(self.pins_db[::-1][i-4], True)

        self.pulseEnable()


    def delayMicroseconds(self, microseconds):
        seconds = microseconds / float(1000000) # divide microseconds by 1 million for seconds
        sleep(seconds)


    def pulseEnable(self):
        self.GPIO.output(self.pin_e, False)
        self.delayMicroseconds(1)               # 1 microsecond pause - enable pulse must be > 450ns 
        self.GPIO.output(self.pin_e, True)
        self.delayMicroseconds(1)               # 1 microsecond pause - enable pulse must be > 450ns 
        self.GPIO.output(self.pin_e, False)
        self.delayMicroseconds(1)               # commands need > 37us to settle


    def message(self, text):
        """ Send string to LCD. Newline wraps to second line"""

        for char in text:
            if char == '\n':
                self.write4bits(0xC0) # next line
            else:
                self.write4bits(ord(char),True)

###LCD DISPLAY CODE END###



RX=16

INTERVAL=30000000

start_tick = None
last_tick = None
low_ticks = 0
high_ticks = 0

GPIO.setmode(GPIO.BCM)
DEBUG = 1

###DUST SENSOR CODE BEGIN###
lcd = Adafruit_CharLCD()
def results(interval):
   global low_ticks, high_ticks
   if interval != 0:
      ratio = float(low_ticks)/float(interval)*10.0
      conc = 1.1*pow(ratio,3)-3.8*pow(ratio,2)+520*ratio+0.62;


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

def dust_start():      
    pi = pigpio.pi() # Connect to local Pi.

    pi.set_mode(RX, pigpio.INPUT)

    cb = pi.callback(RX, pigpio.EITHER_EDGE, cbf)

def dust_end():
    time.sleep(3600)

    cb.cancel() # Cancel callback.

    pi.stop() # Disconnect from local Pi.

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

#!/usr/bin/env python

RoAPin = 17    # pin11
RoBPin = 19    # pin12

globalCounter = 0

flag = 0
Last_RoB_Status = 0
Current_RoB_Status = 0

RoAPin = 11    # pin11
RoBPin = 35    # pin12

globalCounter = 0

flag = 0
Last_RoB_Status = 0
Current_RoB_Status = 0

def setup():
               # Numbers GPIOs by physical location
        GPIO.setup(RoAPin, GPIO.IN)    # input mode
        GPIO.setup(RoBPin, GPIO.IN)

def rotaryDeal():
        global flag
        global Last_RoB_Status
        global Current_RoB_Status
        global globalCounter
        Last_RoB_Status = GPIO.input(RoBPin)
        while(not GPIO.input(RoAPin)):
                Current_RoB_Status = GPIO.input(RoBPin)
                flag = 1
        if flag == 1:
                flag = 0
                if (Last_RoB_Status == 0) and (Current_RoB_Status == 1):
                        globalCounter = globalCounter + 1
                if (Last_RoB_Status == 1) and (Current_RoB_Status == 0):
                        globalCounter = globalCounter - 1

def knob():
        global globalCounter
        while True:
                rotaryDeal()
                if globalCounter > 3 :
                        globalCounter = 0
                if globalCounter <0 :
                        globalCounter = 3

def destroy():
        GPIO.cleanup()             # Release resource



#########||||||||||******#       START OF PROCESS     #******||||||||||#########
read_gas = readadc(gas_sensor, SPICLK, SPIMOSI, SPIMISO, SPICS)
read_o2 = readadc(o2_sensor, SPICLK, SPIMOSI, SPIMISO, SPICS)
measuredVout_o2 = read_o2*(3.3/1023)
measuredVout_gas = read_gas*(3.3/1023)
o2_conc = measuredVout_o2*0.1348
o2_percent_conc = o2_conc*100
def sensors():
    while True:
               
                #localtime = time.asctime( time.localtime(time.time()) )
                #g = open("gas", "a")
                #g.write(str(localtime))
                #g.write("||")
                #g.write("Gas Presence (V): ")
                #g.write(str(measuredVout_gas))
                #g.write("\n")
                #g.close()
                #o = open("oxygen", "a")
                #o.write(str(localtime))
                #o.write("||")
                #o.write("Oxygen Concentration (%): ")
                #o.write(str(o2_percent_conc))
                #o.write("\n")
                #o.close()
                try:
                    time.sleep(9)
                    co2 = c.calibrateZero()
                    time.sleep(0.5)
                
                except KeyboardInterrupt:
                    print "Exiting"
                    sys.exit(0)
                
                time.sleep(15)
def options():
    if globalCounter == 0:
        lcd.message("Gas Reading:\n")
        lcd.message(str(measuredVout_gas))
    if globalCounter == 1:
         lcd.message("Oxygen (%):\n")
         lcd.message(str(o2_percent_conc))
    if globalCounter == 2:
        try:
            lcd.message("CO2[ppm, C]:\n")
            lcd.message(c.read())
        except IndexError:
                    lcd.clear()
                    lcd.message("CO2 sensor error")
    if globalCounter == 3:
      lcd.message("Ratio,pcs/0.01cf\n")
      lcd.message("{:.1f}, {}".format(ratio, int(conc)))
        
def processes():
    dust_start()
    sensors()
    dust_end()

threadA=Thread(target=knob)
threadB=Thread(target=processes)
threadC=Thread(target=options)


if __name__ == '__main__':     # Program start from here
        try:
                setup()
                print '1'
                threadA.start()
                print '2'
                threadC.start()
                print '3'
                threadB.start()
                print '4'
        except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
                destroy()
                



       
                
