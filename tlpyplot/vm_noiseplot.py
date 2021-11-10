#!/usr/bin/env python3
"""
tlgraph: Class to create a matplotlib noise graph that updates live using data from a Twinleaf I/O data source, notably from any object that has a readAvailable() method. This can be a sensor.data object, or a sensor.stream object, or even a sensors.syncstream object. 
License: MIT
Author: Esme Rubinstein <rubinstein@twinleaf.com>, Tom Kornack <kornack@twinleaf.com>
"""
import threading
import tldevicesync
import matplotlib.pyplot
import matplotlib.animation
import numpy as np
import scipy.signal

def powerSpectralDensity(x, Fs):
    freqs, psd = scipy.signal.periodogram(x, Fs, detrend='linear', scaling='density', window='blackmanharris')
    psd = np.sqrt(psd)
    freqs = freqs[1:] # Skip zero Hz element
    psd = psd[1:]
    return freqs, psd

def logBin(freqs, psd, N=200, mode=1, verbosity=0):
    xs = freqs
    ys = psd
    # mode = 0 is for normal average
    # mode = 1 is for adding in quadrature
    # Data must be ascending in frequency
    if xs[0] == 0: # Avoid zero frequency
        xs = xs[1:]
        ys = ys[1:]
    df = xs[1] - xs[0]
    xmax = xs[-1]
    xmin = xs[0]
    maxlogx = np.log(xmax)
    minlogx = np.log(xmin)
    bins = np.exp(np.arange(N, dtype = float)/(N-1.)*(maxlogx-minlogx)+minlogx)
    bins[0] = xmin
    bins[-1] = xmax
    binindex = 1
    vi = 0
    sumy = 0
    sumx= 0
    count = 0
    binnedx = []
    binnedy = []
    try:
        while vi < len(xs) and binindex < len(bins):
            if verbosity>1:
                print('This bin is for X between %1.9e and %1.9e; current X = %1.9e'
                    %(bins[binindex-1], bins[binindex], xs[vi]))
            if bins[binindex-1] <= xs[vi] <= bins[binindex]:
                sumx = sumx + xs[vi]
                count = count + 1
                if mode == 0: sumy = sumy + ys[vi]
                if mode == 1: sumy = sumy + ys[vi]**2
                vi = vi + 1
            else:
                if xs[vi] > bins[binindex-1] and count == 0:
                    binindex = binindex + 1
                else:
                    #print(count)
                    binnedx.append(sumx/count)
                    if mode == 0: binnedy.append(sumy/count)
                    if mode == 1: binnedy.append(np.sqrt(sumy/count))
                    sumy = 0
                    sumx= 0
                    count = 0
                    binindex = binindex + 1
    except:
        print('logBin ERROR! Diagnostics:');
        print('vi',vi)
        print('binindex',binindex)
        print('len(bins)',len(bins))
        print("len(xs)",len(xs))
        print('bins[binindex-1]',bins[binindex-1])
        print("xs[vi]",xs[vi])
        raise Exception("logBin Failed")
    return np.array(binnedx),np.array(binnedy)

def subtractPolynomial(xdata, ydata):
    p = np.polyfit(xdata, ydata, 3)
    poly = np.polyval(p,xdata)
    ydata = ydata - poly
    return ydata

class vmNoise(threading.Thread):
    def __init__(self, streamList, plotter):
        self.plotter = plotter
        self.threadLock = threading.Lock()
        self.streamList = streamList
        matplotlib.rcParams['font.family'] = 'Palatino'
        self.fig = matplotlib.pyplot.figure()#constrained_layout=True)
        self.fig.subplots_adjust(left=0.08, right=0.97, top=0.97, bottom=0.22)
        self.ss = tldevicesync.SyncStream(self.streamList)

        self.gs = matplotlib.gridspec.GridSpec(1,1,figure = self.fig, hspace = 0.1, wspace = 0.01)
        self.xdata = []
        self.xfreq = []
        self.ydata = []
        self.yfreq = []
        self.zdata = []
        self.zfreq = []

        self.ax3 = self.fig.add_subplot(self.gs[0])
        self.ax1line = matplotlib.lines.Line2D([],[], color='blue', linewidth = 0.5, label = "X Noise")
        self.ax2line = matplotlib.lines.Line2D([],[], color='green', linewidth = 0.5, label = "Y Noise")
        self.ax3line = matplotlib.lines.Line2D([],[], color='red', linewidth = 0.5, label = "Z Noise")
        self.ax3.add_line(self.ax1line)
        self.ax3.add_line(self.ax2line)
        self.ax3.add_line(self.ax3line)
        matplotlib.pyplot.legend()
        self.ax3.set_xlabel("Frequency (Hz)")
        self.ax3.set_ylabel("Noise (nT/$\sqrt{\mathrm{Hz}}$)")
        #self.ani = matplotlib.animation.FuncAnimation(self.fig, self.animate, interval=2000)
        self.run()
        
    def run(self,*args):
        #self.threadLock.acquire(1) 
        def noise():
            with self.threadLock:
                data = self.plotter.alldata
            Fs = self.ss.rate()

            def retrieveData(axis, data):
                if axis == 'X':
                    index = 0
                elif axis == 'Y':
                    index = 1
                elif axis == 'Z':
                    index = 2
                if len(data[index]) > 2:
                    data = subtractPolynomial(self.plotter.data_t, data[index])
                    data = np.array(data)
                    freqs, psd = powerSpectralDensity(data, Fs)
                    freqs, psd = logBin(freqs, psd, N=500)
                else:
                    freqs = np.array([0,0])
                    psd = np.array([0,0])
                return [freqs, psd]

            Xdata = retrieveData('X', data)
            Ydata = retrieveData('Y', data)
            Zdata = retrieveData('Z', data)
            return (Xdata, Ydata, Zdata)
        
        newData = noise()

        with np.errstate(divide='ignore', invalid='ignore'):
            self.xfreq = np.log(newData[0][0])
            self.xdata = np.log(newData[0][1])
            self.yfreq = np.log(newData[1][0])
            self.ydata = np.log(newData[1][1])
            self.zfreq = np.log(newData[2][0])
            self.zdata = np.log(newData[2][1])

        self.ax1line.set_data(self.xfreq, self.xdata)
        self.ax2line.set_data(self.yfreq, self.ydata)
        self.ax3line.set_data(self.zfreq, self.zdata)
        self.ax3.relim()
        self.ax3.autoscale_view()
        #self.threadLock.release()
        #return self.ax1line#, self.ax2line, self.ax3line

    def runInThread(self, *args):
        thr = threading.Thread(daemon = True, target = self.run, args = (self, *args))
        thr.start()

