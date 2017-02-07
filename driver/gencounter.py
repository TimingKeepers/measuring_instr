#!   /usr/bin/env   python3
#    coding: utf8
'''
Abstract class to define the API for a Frequency Counter/Timer

This API defines the usual commands for a Frequency Counter/Timer:
- Measure Frequency of an input channel
- Measure Period of an input channel
- Measure Time Interval
- Measure Peak-to-Peak input voltage
And some common commands to manage the instrument.

@file
@author Felipe Torres González (torresfelipex1<AT>gmail.com)
@date Created on Nov 3, 2016
@copyright GPL v3
'''

# API for the Frequency Counter/Timer instruments
# Copyright (C) 2016  Felipe Torres González (torresfelipex1<AT>gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import abc
import enum
import logging


__meas_instr__ = "GenCounter"

class Interfaces(enum.Enum) :
    '''
    This class represents the supported interfaces in the instruments.
    '''
    usb      = 0
    usb_acm  = 1
    vxi11    = 2

class GenCounter() :
    '''
    Abstract class to define the API for a Frequency Counter/Timer
    '''
    __metaclass__ = abc.ABCMeta

    ## How many input channels has the instrument
    _nChannels = 2

    ## How many samples take (for supported measures)
    _samples = 1

    ## Time between samples (ms)
    _interval = 1e3

    ## Enable debug output
    _dbg = False

    ## Driver for the communication
    _drv = None

    ## The port used (IP, serial, usbtmc)
    _port = None

    ## The interface used by the driver
    _conn = None


    @abc.abstractmethod
    def __init__(self, interface, port, name=None) :
        '''
        Constructor

        Args:
            interface (Interfaces) : The interface used to communicate with the device
            port (str) : The port used (serial port, IP, ...)
            name (str) : An identifier for the device
        '''

    @abc.abstractmethod
    def open(self) :
        '''
        Method to open the connection with the device
        '''

    @abc.abstractmethod
    def resetDevice(self) :
        '''
        Method to reset the device
        '''

    @abc.abstractmethod
    def trigLevel(self, cfgstr) :
        '''
        Method to set the trigger level for a channel

        Args:
            cfgstr (str) : A string containing valid params

        The expected params in this method are:
            trig<ch>:<float>, (trig1:0.8, the values are in Volts)
        '''

    @abc.abstractmethod
    def freq(self, cfgstr) :
        '''
        Method to measure the frequency of the input signal in a channel

        Args:
            cfgstr (str) : A string containing valid params

        The expected params in this method are:
            ch (int) : Index of the channel
        '''

    @abc.abstractmethod
    def period(self, cfgstr) :
        '''
        Method to measure the period of the input signal in a channel

        Args:
            ch (int) : Index of the channel
        '''

    @abc.abstractmethod
    def timeInterval(self, cfgstr) :
        '''
        Method to measure Time Interval between the input channels

        Args:
            cfgstr (str) : A string containing valid params

        The expected params in this method are:
            ref (int) : The channel used as reference
            ch (int) : The channel to measure the time interval
        '''

    @abc.abstractmethod
    def pkToPk(self, cfgstr) :
        '''
        Method to measure the pk-to-pk amplitude of an input signal

        Args:
            ch (int) : Index of the channel
        '''

    def parseConfig(self, cfgstr) :
        '''
        Method to parse a configuration string

        Methods defined by this API expect a string containing the
        arguments needed by the methods. The syntax should be:
        <token>:<value> [<token>:<value>]

        This method parses the input string to a dict ready to be
        passed to a method.

        The parseConfig method doesn't filters out any token. The
        other caller method should take only the needed tokens
        from the dict.

        Args:
            cfgstr (str) : A string containing a configuration chain.
        '''
        if cfgstr is None:
            logging.warning("Empty cfg string passed to the Config Parser")
            return ""

        cfgstr = cfgstr.strip()
        cfgdict = {}

        for s in cfgstr.split(" ") :
            if s[0] == " " : continue
            key, val = s.split(":")
            cfgdict[key] = val

        return cfgdict
