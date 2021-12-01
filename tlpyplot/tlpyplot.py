#!/usr/bin/env python3
"""
tlgraph: Class to create a matplotlib graph that updates live using data from a Twinleaf I/O data source, notably from any object that has a readAvailable() method. This can be a sensor.data object, or a sensor.stream object, or even a sensors.syncstream object. 
License: MIT
Author: Esme Rubinstein <rubinstein@twinleaf.com>, Tom Kornack <kornack@twinleaf.com>
"""

import tldevicesync
import collections
import matplotlib.pyplot
import matplotlib.animation
import time

class TLPyPlot:
    def __init__(self,
                 queueLength,
                 streamList,
                 xlabel="Time (s)",
                 wallSync = False):
        self.wallSync = wallSync
        self.pause = False
        self.streamList = streamList
        self.queueLength = queueLength
        self.xlabel = xlabel

        matplotlib.rcParams['font.family'] = 'Palatino'
        self.fig = matplotlib.pyplot.figure()#constrained_layout=True)
        self.fig.subplots_adjust(left=0.08, right=0.97, top=0.96, bottom=0.12)

        self.firstTime = []
        for i in range(len(self.streamList)):
            self.firstTime.append(True)
        self.subtractValue = []

        self.reinitialize(self.queueLength, self.streamList)
        self.animate()

    def reinitialize(self, queueLength, streamList):
        self.subtractValue = []
        #self.tio = tldevicesync.DeviceSync(self.connectionPort)
        self.streamList = streamList
        self.firstTime = []
        for i in range(len(self.streamList)):
            self.firstTime.append(True)
        self.data_t = []
        if self.wallSync:
            self.ss = []
            self.numStreams = len(streamList)
            for i in range(self.numStreams):
                self.data_t.append(collections.deque(maxlen = queueLength))
                self.ss.append(tldevicesync.SyncStream([self.streamList[i]]))
            self.numStreams += 1
        else:
            self.ss = tldevicesync.SyncStream(streamList)
            self.numStreams = len(self.ss.read(samples = 1))
            self.data_t.append(collections.deque(maxlen = queueLength))

        self.gs = matplotlib.gridspec.GridSpec(self.numStreams-1,1,figure = self.fig, hspace = 0.1, wspace = 0.01)
        self.alldata = []
        self.allax = []
        self.allaxline = []
        
        for i in range(1,self.numStreams): #pubQueueLength
            self.alldata.append(collections.deque(maxlen = queueLength))
            self.allax.append(self.fig.add_subplot(self.gs[i-1]))
            self.allaxline.append(matplotlib.lines.Line2D([],[],color = 'black', linewidth = 0.5))
            self.allax[i-1].add_line(self.allaxline[i-1])
            if self.wallSync:
                self.allax[i-1].set_ylabel(self.ss[i-1].columnnames()[1])
            else:
                self.allax[i-1].set_ylabel(self.ss.columnnames()[i])
            if i == self.numStreams - 1:
                self.allax[i-1].set_xlabel(self.xlabel)
            else:
                matplotlib.pyplot.setp(self.allax[i-1].get_xticklabels(), visible = True)

    def changeQueueSize(self, size):
        #rate = plotter.ss[0].rate()
        #windowLength = int(float(seconds)*float(rate))
        if self.wallSync:
            newT = []
            for i in range(self.numStreams-1):
                newT.append(collections.deque(maxlen = int(float(size)*float(self.ss[0].rate()))))
                newT[i].extend(self.data_t[i])
                self.data_t[i] = newT[i]
        else:
            newT = collections.deque(maxlen = size)
            newT.extend(self.data_t[0])
            self.data_t[0] = newT
        newData = []
        for i in range(1, self.numStreams):
            newData.append(collections.deque(maxlen = int(float(size)*float(self.ss[0].rate()))))
            newData[i-1].extend(self.alldata[i-1])
        self.alldata = newData

    def animate(self,*args):
        if self.wallSync:
            dataLoad = []
            timeStamps = []
            for i in range(self.numStreams-1):
                newPoints = self.ss[i].readAvailable()
                if type(newPoints[0]) is not list:
                    newPoints[0] = [newPoints[0]]
                    newPoints[1] = [newPoints[1]]
                if self.firstTime[i]:
                    self.subtractValue.append(newPoints[0][0])
                newPoints[0][:] = [time - self.subtractValue[i] for time in newPoints[0]]
                timeStamps.append(newPoints[0])
                dataLoad.append(newPoints[1])
                self.firstTime[i] = False
            for i in range(len(dataLoad)):
                if type(dataLoad[i]) is not list:
                    dataLoad[i] = [dataLoad[i]]
                    timeStamps[i] = [timeStamps[i]]
                if not self.pause:
                    self.data_t[i].extend(timeStamps[i])
                    self.alldata[i].extend(dataLoad[i])
                    self.allaxline[i].set_data(self.data_t[i], self.alldata[i])
                    #self.allax[i].set_xlim(self.data_t[0][0], self.data_t[0][-1])
                    self.allax[i].relim()
                    self.allax[i].autoscale_view()
        else:
            dataLoad = self.ss.readAvailable()
            for i in range(len(dataLoad)):
                if type(dataLoad[i]) is not list:
                    dataLoad[i] = [dataLoad[i]]
                if not self.pause:
                    if i == 0:
                        self.data_t[0].extend(dataLoad[i])
                    else:
                        self.alldata[i-1].extend(dataLoad[i])
                        self.allaxline[i-1].set_data(self.data_t[0], self.alldata[i-1])
                        self.allax[i-1].set_xlim(self.data_t[0][0], self.data_t[0][-1])
                        self.allax[i-1].relim()
                        self.allax[i-1].autoscale_view()

