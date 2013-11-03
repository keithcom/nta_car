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

"""A simple client to create a CLA model for the ski game."""

import time
import os
import RPi.GPIO as GPIO
import sys
import logging
import csv

from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.data.inference_shifter import InferenceShifter

import description2

# set up pins for the a2d chip
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25

# set up the SPI interface pins
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

# assign our photo cells measurement ports
PHOTO_RIGHT = 0
PHOTO_LEFT = 1

# assign port for controlling the car
GO_FORWARD = 4
TURN_LEFT = 22
TURN_RIGHT = 17
GPIO.setup(GO_FORWARD, GPIO.OUT)
GPIO.setup(TURN_LEFT, GPIO.OUT)
GPIO.setup(TURN_RIGHT, GPIO.OUT)

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


#-----------------------------------------------------------------------------
# nupic functions
#-----------------------------------------------------------------------------
def createModel():
  return ModelFactory.create(description2.config)



def drive():
    global PHOTO_RIGHT
    global PHOTO_LEFT
    global SPICLK
    global SPIMOSI
    global SPIMISO
    global SPICS

    modelL = createModel()
    modelL.enableInference({'predictionSteps': [1], 'predictedField': 'left'})
    modelR = createModel()
    modelR.enableInference({'predictionSteps': [1], 'predictedField': 'right'})
    inf_shift = InferenceShifter();

    # - Train on the test data
    print "================================= Training Data =================================="
    print
    with open('data.csv', 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
        for row in spamreader:
            record = {'left': row[0], 'right': row[2]}
            result = inf_shift.shift(modelL.run(record))
            result = inf_shift.shift(modelR.run(record))

    # - Then set it free to run on it's own
    modelL.disableLearning()
    modelR.disableLearning()
    print "================================= Start Driving =================================="
    print
    while True:
        # read the sensors
        left = readadc(PHOTO_LEFT, SPICLK, SPIMOSI, SPIMISO, SPICS)
        right = readadc(PHOTO_RIGHT, SPICLK, SPIMOSI, SPIMISO, SPICS)
        record = {'left': left, 'right': right}

        result = inf_shift.shift(modelL.run(record))
        predicted = 0.0
        total_probability = 0.0
        for key, value in result.inferences['multiStepPredictions'][1].iteritems():
            predicted += float(key) * float(value)
            total_probability += float(value)
        predictedL = predicted / total_probability

        result = inf_shift.shift(modelL.run(record))
        predicted = 0.0
        total_probability = 0.0
        for key, value in result.inferences['multiStepPredictions'][1].iteritems():
            predicted += float(key) * float(value)
            total_probability += float(value)
        predictedR = predicted / total_probability

        # make driving decision
        diffL = predictedL - left
        diffR = predictedR - right
        if diffL > diffR and (diffL > 10 or diffR < -10):
            # turn left
            GPIO.output(TURN_LEFT, True)
            GPIO.output(TURN_RIGHT, False)
        elif diffR > diffL and (diffR > 10 or diffL < -10):
            # turn right
            GPIO.output(TURN_LEFT, False)
            GPIO.output(TURN_RIGHT, True)
        else:
            # go straight
            GPIO.output(TURN_LEFT, False)
            GPIO.output(TURN_RIGHT, False)

        # check anomaly score for speed


if __name__ == "__main__":
    drive()
