#!/usr/bin/env python

# low_high.py
# 2015-11-17
# Public Domain

import time
import pigpio

RX=16

INTERVAL=30000000

start_tick = None
last_tick = None
low_ticks = 0
high_ticks = 0


def results(interval):
   global low_ticks, high_ticks
   if interval != 0:
      ratio = float(low_ticks)/float(interval)*10.0
      conc = 1.1*pow(ratio,3)-3.8*pow(ratio,2)+520*ratio+0.62;
      print(int(conc), 'pcs/0.01cf')
      localtime = time.asctime( time.localtime(time.time()) )
      logger = str(int(conc))
      f = open('dust', 'a')
      f.write(str(localtime))
      f.write("||")
      f.write("pcs/0.01cf: ")
      f.write(logger)
      f.write("\n")
      f.close()
      
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
     
pi = pigpio.pi() # Connect to local Pi.

pi.set_mode(RX, pigpio.INPUT)

cb = pi.callback(RX, pigpio.EITHER_EDGE, cbf)

time.sleep(3600)

cb.cancel() # Cancel callback.

pi.stop() # Disconnect from local Pi.
