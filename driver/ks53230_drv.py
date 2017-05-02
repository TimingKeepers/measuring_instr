#!   /usr/bin/env   python3
# -*- coding: utf-8 -*
'''
Driver for the KEYSIGHT 53230A Universal Frequency Counter/Timer

@file
@date Created on Apr. 28, 2017
@author Daniel Melgarejo García (danimegar<AT>gmail.com)
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

import time
import vxi11

class KS53230_drv() :
    '''
    KEYSIGHT 53230A driver.
    '''

    def __init__(self, Device) :
        '''
        Constructor

        Args:
            Device (ip) : device ip address
        '''

	self =  vxi11.Instrument(Device)

        info = self.query("*IDN?")
        self.manufacturer = info.split(",")[0]
        self.device = info.split(",")[1]
        self.serial = info.split(",")[2]

    # ------------------------------------------------------------------------ #

    def deviceInfo(self) :
        '''
        Method to retrieve device information.

        Returns:
            A string with manufacturer, device name and serial number.
        '''
        return ("%s %s (s/n : %s)" % (self.manufacturer, self.device, self.serial))
