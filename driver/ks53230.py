#!   /usr/bin/env   python3
# -*- coding: utf-8 -*
'''
Class that implements the interface GenCounter for the KEYSIGHT 53230A Universal Frequency Counter/Timer.

@file
@date Created on May. 3, 2017
@author Daniel Melgarejo Garcia (danimegar<AT>gmail.com)
@copyright LGPL v2.1
@ingroup measurement
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
from driver.ks53230_drv  import KS53230_drv

# This attribute permits dynamic loading inside wrcalibration class.
__meas_instr__ = "KS53230"

class KS53230(GenCounter) :
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

    def __init__(self, IP, name=None) :
        '''
        Constructor

        Args:
            IP (str) : Device ip address
            name (str) : An identifier for the device
        '''
        self._ip = IP
        self._drv = KS53230_drv(IP)

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
            trig<ch>:<float>, (trig1:0.8, the values are in Volts)
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

    def freq(self, cfgstr) :
        '''
        Method to measure the frequency of the input signal in a channel

        Args:
            cfgstr (str) : A string containing valid params

        The expected params in this method are:
            ch (int) : Index of the channel, (ch1:1, ch2:2 or ch1:1 ch2:2)
        '''
        self.freq_rawcfg = cfgstr
        cfgdict = self.parseConfig(cfgstr)
        logging.debug("Config parsed: %s" % (str(cfgdict)))
        keys = " ".join(cfgdict.keys())
        keys = re.findall(r"(ch\d)", keys)
        if keys == [] :
            raise Exception("No valid params passed to freq")
        
        for k in keys :
            self._drv.write("CONF:FREQ DEF,DEF,(@%d)" % int(k[-1]))
            self.trigLevel(cfgstr)
            self._drv.write("INPUT%d:COUPLING DC" % int(k[-1]))
            self._drv.write("INIT")
            time.sleep(3)
            print(self._drv.query("READ?"))
            logging.debug("Measuring Frequency in channel %d"
                          % (int(k[-1])))

    def period(self, cfgstr) :
        '''
        Method to measure the period of the input signal in a channel

        Args:
            cfgstr (str) : A string containing valid params

        The expected params in this method are:
            ch (int) : Index of the channel, (ch1:1, ch2:2 or ch1:1 ch2:2)
        '''
        self.period_rawcfg = cfgstr
        cfgdict = self.parseConfig(cfgstr)
        logging.debug("Config parsed: %s" % (str(cfgdict)))
        keys = " ".join(cfgdict.keys())
        keys = re.findall(r"(ch\d)", keys)
        if keys == [] :
            raise Exception("No valid params passed to period")
        
        for k in keys :
            self._drv.write("CONF:PER DEF,DEF,(@%d)" % int(k[-1]))
            self.trigLevel(cfgstr)
            self._drv.write("INPUT%d:COUPLING DC" % int(k[-1]))
            self._drv.write("INIT")
            time.sleep(3)
            print(self._drv.query("READ?"))
            logging.debug("Measuring Period in channel %d"
                          % (int(k[-1])))

    
    def timeInterval(self, cfgstr, meas_out) :
        '''
        Method to measure Time Interval between the input channels

        Args:
            cfgstr (str) : A string containing valid params

        The expected params in this method are:
            ref (int) : The channel used as reference
            ch (int) : The channel to measure the time interval
            (ref:A, ref_chan = 1, other chan = 2; else ref_chan = 2, other chan=1)
            tst (int) : Time Stamp, range 1 - 1000000, (tst:1000000)
            sampl (int) : Samples number, range 1 - 1000000, (sampl:1000000)
            coup (str) : coupling ac or dc, (coup:dc)
            imp (int or str) : impedance range 50 - 1000000, (imp:1000000) 
        '''
        cfgdict = self.parseConfig(cfgstr)
        logging.debug("Config parsed: %s" % (str(cfgdict)))
        # Repasar la configuración parseada
        ref_chan, other_chan = (1,2) if cfgdict["ref"] == "A" else (2,1)
        samples = int(cfgdict["sampl"])
        if 'tst' in cfgdict : 
            tstamp = int(cfgdict["tst"])
        
        # Measurement configuration --------------------------------------------
        # Specify the type of measurement to be done
        self._drv.write("CONFIGURE:TINTERVAL (@%d),(@%d)" % (ref_chan,
                        other_chan))
        # The last command overwrites trigger configuration :-(
        self._drv.write("INPUT1:COUPLING %s" % str(cfgdict["coup"]))
        self._drv.write("INPUT2:COUPLING %s" % str(cfgdict["coup"]))
        self._drv.write("INPUT1:IMPedance %f" % float(cfgdict["imp"]))
        self._drv.write("INPUT2:IMPedance %f" % float(cfgdict["imp"]))
        self.trigLevel(cfgstr)

        # It seems that specify the number of samples here doesn't work properly
        self._drv.write("TRIG:COUNT 1")
       
        # Taking measures from the instrument ----------------------------------
        ret =  []
        self._drv.write("INIT")

        # Do you want time stamps?
        #if 'tst' in cfgdict :
            #self._drv.write("FORM:DATA ASC")
            #self._drv.write("CONF:ARR:TST (%d)" % (tstamp))
            #self._drv.write("TST:RATE MIN")

        k = 0
        while k < samples:
            # Enable the trigger for a new measure, and wait until a PPS pulse
            # arrives at ref channel. No timeout need by the control software.
            cur = self._drv.query("READ?")
            if 'tst' in cfgstr :
                val, ts = cur.split(',',1)
                meas_out.addMeasures(float(val), float(ts))
            else: 
                meas_out.addMeasures(float(cur))
            k += 1
