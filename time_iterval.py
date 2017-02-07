#!   /usr/bin/env   python3
# -*- coding: utf-8 -*
'''
A Python tool to measure Time Interval

@file
@date Created on Feb, 2017
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
import datetime
import time
import threading as th
import argparse as arg

from driver.gencounter import *
from driver.fca3103 import FCA3103
from misc.measured_data import MeasuredData

def guardaPorSi(datos, fichero):
    datos.flushToFile(fichero)
    # Me echo una siesta...
    time.sleep(10)

def main():
    '''
    A quick tool to measure time interval with the Tektronix FCA3103
    '''
    #TODO: Sorry no arguments parser, put values directly in variables

    # El 2 es la X en /dev/usbtmcX
    device = FCA3103(Interfaces.usb, 2, "Mi querido counter")
    datos = MeasuredData()
    device.resetDevice()
    # Todavía no está eso implementado en la API, así que a pelo
    device._drv.write("INPUT1:COUPLING DC")
    device._drv.write("INPUT2:COUPLING DC")
    device._drv.write("INPUT2:IMPedance MAX") # 1MOhm
    device._drv.write("INPUT1:IMPedance MAX")
    device.trigLevel("trig1:1.5 trig2:1.5")
    # El -1 es modo infinito
    cfg_str = "ref:A sampl:-1 tstamp:Y"
    t_meas = th.Thread(target=device.timeInterval, args=(cfg_str, datos))
    t_data = th.Thread(target=guardaPorSi, args=(datos, "salida.dat"))

    t_meas.start()
    time.sleep(20) # no hay que ser ansias
    t_data.start()

if __name__ == "__main__" :
    main()
