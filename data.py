#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""A simple client to generate data for the nta_car program."""

import time
import os
import RPi.GPIO as GPIO
import sys
import logging

# number of records to record
_NUM_RECORDS = 1000

# assign our photo cells measurement ports
PHOTO_RIGHT = 0
PHOTO_LEFT = 1

# set up pins for the a2d chip
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25

# set up the SPI interface pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

# print data headers
#print "left,right"
#print "int,int"
#print ","


#-----------------------------------------------------------------------------
# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
#  photo cells are on 0, 1
#-----------------------------------------------------------------------------
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


def runData():
    global PHOTO_RIGHT
    global PHOTO_LEFT
    global SPICLK
    global SPIMOSI
    global SPIMISO
    global SPICS

    for i in xrange(_NUM_RECORDS):
        # read the sensors
        left = readadc(PHOTO_LEFT, SPICLK, SPIMOSI, SPIMISO, SPICS)
        right = readadc(PHOTO_RIGHT, SPICLK, SPIMOSI, SPIMISO, SPICS)
        print left, ",", right
        #time.sleep(0.5)


if __name__ == "__main__":
    runData()
