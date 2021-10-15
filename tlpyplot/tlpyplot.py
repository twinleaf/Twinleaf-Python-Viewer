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

class TLPyPlot:
    def __init__(self,
                 queueLength,
                 streamList,
                 connectionPort = 'tcp://localhost',
                 xlabel="Time (s)"):

        self.pause = False
        self.connectionPort = connectionPort
        self.streamList = streamList
        self.queueLength = queueLength
        self.xlabel = xlabel

        matplotlib.rcParams['font.family'] = 'Palatino'
        self.fig = matplotlib.pyplot.figure()#constrained_layout=True)
        self.fig.subplots_adjust(left=0.08, right=0.97, top=0.97, bottom=0.08)

        self.reinitialize(self.queueLength, self.streamList)
        self.animate()

    def reinitialize(self, queueLength, streamList):
        #self.tio = tldevicesync.DeviceSync(self.connectionPort)
        self.ss = tldevicesync.SyncStream(streamList)

        self.numStreams = len(self.ss.read(samples = 1))
        self.gs = matplotlib.gridspec.GridSpec(self.numStreams-1,1,figure = self.fig, hspace = 0.1, wspace = 0.01)
        self.data_t = collections.deque(maxlen = queueLength)
        
        self.alldata = []
        self.allax = []
        self.allaxline = []
        
        for i in range(1,self.numStreams): #pubQueueLength
            self.alldata.append(collections.deque(maxlen = queueLength))
            self.allax.append(self.fig.add_subplot(self.gs[i-1]))
            self.allaxline.append(matplotlib.lines.Line2D([],[],color = 'black', linewidth = 0.5))
            self.allax[i-1].add_line(self.allaxline[i-1])
            self.allax[i-1].set_ylabel(self.ss.columnnames()[i])
            if i == self.numStreams - 1:
                self.allax[i-1].set_xlabel(self.xlabel)
            else:
                matplotlib.pyplot.setp(self.allax[i-1].get_xticklabels(), visible = False)

    def increaseQueueSize(self, size):
        newT = collections.deque(maxlen = size)
        newT.extend(self.data_t)
        self.data_t = newT
        newData = []
        for i in range(1, self.numStreams):
            newData.append(collections.deque(maxlen = size))
            newData[i-1].extend(self.alldata[i-1])
        self.alldata = newData

    def animate(self,*args):
        dataLoad = self.ss.readAvailable()
        for i in range(len(dataLoad)):
            if type(dataLoad[i]) is float:
                dataLoad[i] = [self.ss.read(samples = 1)[i]]
            if not self.pause:
                if i == 0:
                    self.data_t.extend(dataLoad[i])
                else:
                    self.alldata[i-1].extend(dataLoad[i])
                    self.allaxline[i-1].set_data(self.data_t, self.alldata[i-1])
                    self.allax[i-1].set_xlim(self.data_t[0], self.data_t[-1])
                    self.allax[i-1].relim()
                    self.allax[i-1].autoscale_view()
        return self.allaxline

