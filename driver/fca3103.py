#!   /usr/bin/env   python3
# -*- coding: utf-8 -*
'''
Class that implements the interface GenCounter for the Tektronix FCA3103.

@file
@date Created on Apr. 20, 2015
@date Modified on Nov. 24, 2016
@author Felipe Torres (torresfelipex1<AT>gmail.com)
@copyright LGPL v2.1
'''

#------------------------------------------------------------------------------|
#                   GNU LESSER GENERAL PUBLIC LICENSE                          |
#                 ------------------------------------                         |
# This source file is free software; you can redistribute it and/or modify it  |
# under the terms of the GNU Lesser General Public License as published by the |
# Free Software Foundation; either version 2.1 of the License, or (at your     |
# option) any later version. This source is distributed in the hope that it    |
# will be useful, but WITHOUT ANY WARRANTY; without even the implied warrant   |
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser   |
# General Public License for more details. You should have received a copy of  |
# the GNU Lesser General Public License along with this  source; if not,       |
# download it from http://www.gnu.org/licenses/lgpl-2.1.html                   |
#------------------------------------------------------------------------------|

#-------------------------------------------------------------------------------
#                                   Import                                    --
#-------------------------------------------------------------------------------
# Import system modules
import re
import time
import logging

# User modules
from driver.gencounter import GenCounter, Interfaces
from driver.fca3103_drv  import FCA3103_drv

# This attribute permits dynamic loading inside wrcalibration class.
__meas_instr__ = "FCA3103"

class FCA3103(GenCounter) :
    '''
    Class that implements the interface GenCounter for the Tektronix FCA3103.

    This implementation allow to use a Tektronix FCA3103 Timer/Counter/Analyzer
    as measurement instrument for White Rabbit calibration procedure.

    If master and slave channels are not specified when making a new copy of
    this class, they must be set before calling any of the methods of the class.
    '''

    ## If a value is far from mean value don't use it
    skip_values = False
    ## Error value, used for skip a value (in ps)
    error = 500000
    ## Keep the trigger values (in Volts)
    trig_rawcfg = None

    def __init__(self, interface, port, name=None) :
        '''
        Constructor

        Args:
            interface (Interfaces) : The interface used to communicate with the device
            port (str) : The port used (serial port, IP, ...)
            name (str) : An identifier for the device
        '''
        self._conn = interface
        self._port = port

        if self._conn != Interfaces.usb :
            raise Exception("Bad interface")

        self._drv = FCA3103_drv(port)

    def open(self) :
        '''
        Method to open the connection with the device

        This method only ask the device for its name and returns it.
        '''
        info = self._drv.deviceInfo()
        # TODO: Check what is returned when no connection is up
        return info

    def resetDevice(self) :
        '''
        Method to reset the device

        This method resets all the params in the device to the default
        values.
        '''
        logging.debug("Device to be reset...")
        self._drv.write("*RST")

    def trigLevel(self, cfgstr) :
        '''
        Method to set the trigger level for a channel

        Args:
            cfgstr (str) : A string containing valid params

        The expected params in this method are:
            trig<ch>:<float>, (trig1:0.08, the values are in Volts)
        '''
        self.trig_rawcfg = cfgstr
        cfgdict = self.parseConfig(cfgstr)
        logging.debug("Config parsed: %s" % (str(cfgdict)))
        keys = " ".join(cfgdict.keys())
        keys = re.findall(r"(trig\d)", keys)
        if keys == [] :
            raise Exception("No valid params passed to trigLevel")
        #logging.debug("Setting config tags: %s" % (str(keys)))

        for k in keys :
            self._drv.write("INPUT%d:LEVEL:AUTO OFF" % int(k[-1]))
            self._drv.write("INPUT%d:LEVEL %1.3f" % (int(k[-1]), float(cfgdict[k])) )
            logging.debug("Setting Trigger Level in channel %d to %1.3f"
                          % (int(k[-1]), float(cfgdict[k])) )

    def timeInterval(self, cfgstr, meas_out) :
        '''
        Method to measure Time Interval between the input channels

        Args:
            cfgstr (str) : A string containing valid params
            meas_out (MeasuredData) : The container for the measured data

        The expected params in this method are:
            ref:{A,B} The reference channel
            sampl:<int> The number of samples to be taken
            tstamp:{Y,N} Enable/Disable timestamping
        '''
        cfgdict = self.parseConfig(cfgstr)
        logging.debug("Config parsed: %s" % (str(cfgdict)))
        # Repasar la configuración parseada
        ref_chan, other_chan = (1,2) if cfgdict["ref"] == "A" else (2,1)
        samples = int(cfgdict["sampl"])
        tstamp = "ON" if cfgdict["tstamp"] == "Y" else "OFF"

        # Measurement configuration --------------------------------------------
        # Trigger mode not continuous
        self._drv.write("INIT:CONT OFF")
        # Specify the type of measurement to be done
        self._drv.write("CONFIGURE:TINTERVAL (@%d),(@%d)" % (ref_chan,
                        other_chan))
        # The last command overwrites trigger configuration :-(
        self.trigLevel(self.trig_rawcfg)
        # It seems that specify the number of samples here doesn't work properly
        self._drv.write("TRIG:COUNT 1;:ARM:COUNT 1")
        # Do you want time stamps?
        self._drv.write("FORMAT ASCII;:FORMAT:TINF %s" % (tstamp))

        # Taking measures from the instrument ----------------------------------
        ret =  []
        self._drv.write("INIT")

        k = 0
        while k < samples:
            # Enable the trigger for a new measure, and wait until a PPS pulse
            # arrives at ref channel. No timeout need by the control software.
            cur = self._drv.query("READ?")
            if tstamp == "ON":
                val, ts = cur.split(',')
                meas_out.addMeasures(float(val), float(ts))
            else: 
                meas_out.addMeasures(float(cur))
            k += 1
