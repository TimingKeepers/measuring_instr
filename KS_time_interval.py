#!   /usr/bin/env   python3
# -*- coding: utf-8 -*

import re
import datetime
import time
import logging
import threading as th
import argparse as arg

from driver.gencounter import *
from driver.ks53230 import KS53230
from misc.measured_data import MeasuredData

def guardaPorSi(datos, fichero):
    datos.flushToFile(fichero)
    # Me echo una siesta...

def main():
    '''
    A quick tool to measure time interval with the Keysight 53230A
    '''

    inst = KS53230("192.168.0.6")
    
    #Vector de parámetros
    cfgstr = "trig1:1.5 trig2:1.5 ch1:1 ch2:2 sampl:10 ref:A coup:dc imp:1000000"
    
    #Reseteamos el dispositivo
    inst.resetDevice()
    
    #Definimos datos
    datos = MeasuredData()
    
    #Medimos y guardamos
    t_meas = th.Thread(target=inst.timeInterval, args=(cfgstr, datos))
    t_data = th.Thread(target=guardaPorSi, args=(datos, "salida.dat"))
    
    t_meas.start()
    time.sleep(60) # no hay que ser ansias
    t_data.start()
    
if __name__ == "__main__" :
    main()

