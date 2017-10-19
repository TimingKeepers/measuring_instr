#!   /usr/bin/env   python3
# -*- coding: utf-8 -*
'''
Class that implements the interface GenCounter for the KEYSIGHT 53230A
Universal Frequency Counter/Timer.

@file
@date Created on May. 3, 2017
@author Daniel Melgarejo Garcia (danimegar<AT>gmail.com)
@author Felipe Torres González (felipetg<AT>ugr.es)
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
    ## How many samples read each time
    step = 5
    ## How much time (s) wait between consecutive read of samples
    deadtime = 1

    def __init__(self, interface, port, logger,name=None) :
        '''
        Constructor

        Args:
            IP (str) : Device ip address
            name (str) : An identifier for the device
            logger (logging)
        '''
        self._port = port
        self._conn = interface
        self.name = name
        self.logger = logger
        self._savedTrigCfg = None
        self._savedTrigLev = None
        if self._conn != Interfaces.vxi11:
            logger.error("By now %s is not supported." % str(interface))
            raise NotImplementedError("Only vxi11 connection is supported.")

        self._drv = KS53230_drv(self._port)

    def open(self) :
        '''
        Method to open the connection with the device

        This method only ask the device for its name and returns it.
        '''
        info = self._drv.deviceInfo()
        self.logger.info("Device open: %s" % info)
        # TODO: Check what is returned when no connection is up
        return info

    def close(self) :
        '''
        Method to close the connection with the device
        '''
        self.logger.info("Connection closed with %s" % self._drv.deviceInfo())
        self._drv.inst.close()
    

    def resetDevice(self) :
        '''
        Method to reset the device

        This method resets all the params in the device to the default
        values.
        '''
        self.logger.info("Device reset")
        self._drv.write("*RST")

    def trigLevel(self, cfgstr) :
        '''
        Method to set the trigger mode and level for a specified channel.

        Args:
            cfgstr (str) : A string containing valid params

        The expected params in this method are:
            trig<ch>:<value> Where ch is the channel index in the counter and value could be:
                - A numeric value for the voltage (in V).
                - a<%> The key "a" (auto) followed by a percentage, i.e. a50 for mode auto at 50% of the amplitude for the signal.

        '''
        cfgdict = self.parseConfig(cfgstr)
        self.logger.debug("Config parsed: %s" % (str(cfgdict)))
        keys = " ".join(cfgdict.keys())
        keys = re.findall(r"(trig\d)", keys)
        if keys == [] :
            raise AttributeError("No valid params passed to trigLevel")

        for k in keys :
            # First, detect if the trigger mode is auto or manual
            cur_t = cfgdict[k]
            # Mode auto
            if cur_t[0] == "a":
                percent = cur_t[-2:]
                logging.debug("Mode auto for channel %s at %s\%" % (k[-1], str(percent)))
            # Mode manual
            else:
                volts = float(cur_t)
                #TODO: channel number
                logging.debug("Mode manual for channel %s at %fV" % (k[-1], volts))
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
        self.logger.debug("Config parsed: %s" % (str(cfgdict)))
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

    def configureTrigger(self, cfgstr) :
        '''
        Method to configure common settings for the trigger system.

        Args:
            cfgstr (str) : A string containing valid params

        The expected params in this method are:
            cnt (int) : Number of triggers that will be accepted by the instrument before returning to idle state.
            del (int) : Delay time (s) between the trigger signal and enabling the gate open for the first measurement.
            Could be any value from 0 to 3600 with a microsecond resolution.
            slo (str) : Use rising (pos) edge or falling edge (neg).
            sou (str) : Selection of the trigger source:
                - imm -> Continuous mode.
                - bus -> Software trigger (*TRG command).
                - ext -> External source (rear Trig in BNC connector).

        Raises:
            AttributeError when an invalid value was passed as argument.
        '''
        cfgdict = self.parseConfig(cfgstr)
        self._savedTrigCfg = cfgstr
        self.logger.debug("Config parsed: %s" % (str(cfgdict)))
        if "cnt" in cfgdict:
            count = int(cfgdict["cnt"])
            if count < 1 or count > 1000000:
                msg = "Trigger Count out of limits (%d)" % count
                raise AttributeError(msg)
            self._drv.write("TRIGGer:COUNt %d" % int(count))
        if "del" in cfgdict:
            delay = int(cfgdict["del"])
            if delay < 0 or delay > 3600:
                msg = "Trigger delay out of limits (%d)" % delay
                raise AttributeError(msg)
            delay = ("%.6f" % delay)
            self._drv.write("TRIGGer:DELay %s" % delay)
        if "sou" in cfgdict:
            source = cfgdict["sou"]
            valid_src = ['imm', 'bus', 'ext']
            if source not in valid_src:
                msg = "Trigger source not valid (%s)" % source
                raise AttributeError(msg)
            self._drv.write("TRIGGer:SOURce %s" % source)
        if "slo" in cfgdict:
            slope = cfgdict["slo"]
            valid_slope = ['pos', 'neg']
            if slope not in valid_slope:
                msg = "Trigger slope not valid (%s)" % slope
                raise AttributeError(msg)
            self._drv.write("TRIGGer:SLOPe %s" % slope)

    def timeInterval(self, cfgstr, meas_out) :
        '''
        Method to measure Time Interval between the input channels

        Args:
            cfgstr (str) : A string containing valid params

        The expected params in this method are:
            ref (int) : The channel used as reference
            ch (int) : The channel to measure the time interval
            (ref:A, ref_chan = 1, other chan = 2; else ref_chan = 2, other chan=1)
            tstamp (str) : Time Stamp: (Y)es or (N)o, (tstamp:Y)
            sampl (int) : Samples number, range 1 - 1000000, (sampl:1000000)
            coup (str) : coupling ac or dc, (coup:dc)
            imp (int or str) : impedance range 50 - 1000000, (imp:1000000)
        '''
        cfgdict = self.parseConfig(cfgstr)
        logging.debug("Config parsed: %s" % (str(cfgdict)))
        # Repasar la configuración parseada
        ref_chan, other_chan = (1,2) if cfgdict["ref"] == "A" else (2,1)
        samples = int(cfgdict["sampl"])

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

        k = 0
        while k < samples:
            # Enable the trigger for a new measure, and wait until a PPS pulse
            # arrives at ref channel. No timeout need by the control software.

            # Do you want time stamps?
            if 'tstamp' in cfgstr and cfgdict["tstamp"] == "Y" :
                timestamp = time.localtime()
                timest = time.strftime(format("%H%M%S"),timestamp)+"\n"
            cur = self._drv.query("READ?")
            if 'tstamp' in cfgstr and cfgdict["tstamp"] == "Y" :
                meas_out.addMeasures(int(timest), float(cur))
            else:
                meas_out.addMeasures(float(cur))
            k += 1
