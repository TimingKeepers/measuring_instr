#!   /usr/bin/env   python3
# -*- coding: utf-8 -*
'''
Class that implements a container for storing the measured values from the instruments.

This class is thread safe, so it call be used from multiple threads in a safe way.
The intent for this class is enable one thread to be measuring data while
another thread can save the data, print the data or do some kind of statistics.

@file
@date Created on Nov. 29, 6
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
import queue

# Custom exceptions for the module
class ContainerEmpty(Exception):
    def __init__(self, message, available, requested):
        self.message = message
        self.available = available
        self.requested = requested

class ContainerFull(Exception):
    def __init__(self, message, size, other):
        self.message = message
        self.size = size
        self.other = other

class BufferSaved(Exception):
    def __init__(self, message="The data buffer is already saved to a file"):
        self.message = message

class MeasuredData():
    '''
    Class that implements a container for storing the measured values from the instruments.
    '''
    ## Blocking timeout
    _timeout = 5

    def __init__(self, size=0):
        '''
        Constructor

        Args:
            size (int) : An integer that sets the upperbound limit of the number of items in the queue. Use 0 for an unlimited queue.
        '''
        ## The internal thread-safe queue
        self._queue = queue.Queue(maxsize=size)

    def addMeasures(self, meas, tstamp=None):
        '''
        Method to add a new measure to the buffer (thread-safe)

        Args:
            meas (float) : A new measure
            tstamp (float) : Timestamp value for the measure
        '''
        try:
            if tstamp is None:
                self._queue.put((meas), timeout=self._timeout)
            else : self._queue.put((meas, tstamp), timeout=self._timeout)
        except queue.Full as e:
            raise ContainerFull(message="No more space available",
            size=self._queue.maxsize, other=e)

    def getMeasures(self, count=1):
        '''
        Take the last _count_ measures from the buffer

        Args:
            count (int) : How many values take from the buffer

        Returns:
            A list with the measured values from the instrument
        '''
        ret_buf = []
        if count > self._queue.qsize():
            raise ContainerEmpty(message="No more data is ready to be fetch",
            available=self._queue.qsize(), requested=count)
        ret_buf = [self._queue.get(timeout=self._timeout) for i in range(count)]

        return ret_buf

    def flushToFile(self, ofile="output.dat"):
        '''
        Method to save all the content of the buffer to a file

        The output format is:
        <value in E notation>, <timestamp>

        Args:
            ofile (str) : Name of the output file
        '''
        if self._queue.qsize() == 0:
            raise BufferSaved()

        with open(ofile, 'a') as f:
            meas = self.getMeasures(self._queue.qsize())
            for i in meas:
                out = str(i)[1:-1] if type(i) is tuple else str(i)
                f.write("%s\n" % (out))
