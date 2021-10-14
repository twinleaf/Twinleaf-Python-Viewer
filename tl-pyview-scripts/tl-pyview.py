import matplotlib

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import matplotlib.animation
from matplotlib import style
import matplotlib.pyplot

import time
import re
import argparse

import tkinter as tk
from tkinter import ttk

import realTimePlotter as rtp

# styles and fonts
matplotlib.use("TkAgg")
LARGE_FONT = ("cronos pro", 25)
NORM_FONT = ("cronos pro", 15)
style.use("ggplot")

def processCommandLineArgs():
    parser = argparse.ArgumentParser(prog='vectorMonitor', 
                             description='Vector Field Graphing Monitor')
    parser.add_argument("url", 
                nargs='?', 
                default='tcp://localhost/',
                help='URL: tcp://localhost')
    args = parser.parse_args()
    tio = rtp.tldevicesync.DeviceSync(args.url)
    time.sleep(1)
    return tio

def getStreams():
    vmrStreamList = ["vector", "accel", "gyro", "bar", "therm"]
    return vmrStreamList

# finds connected devices and returns dict of devices and columnnames for those devices
def findConnectedDevices(tio):
    devAttributes = {}
    for device in tio._routes:
        if device == '/':
            m = getattr(tio, tio._routes[device].dev.name().lower())
            name = tio._routes[device].dev.name().lower()
            devAttributes[name] = m.data.columnnames()
        else:
            m = getattr(tio,tio._routes[device].dev.name().lower()+str(device))
            name = tio._routes[device].dev.name().lower()+str(device)
            devAttributes[name] = m.data.columnnames()
    return devAttributes

# popup message general function
def popupmsg(msg):
    popup = tk.Tk()
    popup.wm_title("!")
    label = ttk.Label(popup, text = msg, font = NORM_FONT)
    label.pack(side = 'top', fill = 'x', pady = 10)
    B1 = ttk.Button(popup, text = "Ok", command = popup.destroy)
    B1.pack()
    popup.mainloop()

# pause function
def loadChart():
    if rtp.chartLoad == True:
        rtp.chartLoad = False
    else:
        rtp.chartLoad = True

# set initial stream list by looking at connected devices
def setDefaults(tio, vmrStreamList):
    start_length = 500
    defaultStream = "Enter Streams Here"
    connectedDevices = findConnectedDevices(tio)
    for device in connectedDevices:
        if "sync" not in device:
            defaultStream = device.lower() + "." + vmrStreamList[0]
            device = getattr(tio,device.lower())
            stre = getattr(device, vmrStreamList[0])
            start_stream = [stre]
    return defaultStream, start_stream, start_length

def createPlot(streamList, windowLength):
    plotter = rtp.RealtimePlotG(queueLength = windowLength, streamList = streamList)
    return plotter

class graphInterface(tk.Tk):
    def __init__(self, tio, plotter, vmrStreamList, defaultStream, windowLength, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        #tk.Tk.iconbitmap(self, default="clienticon.ico")
        tk.Tk.wm_title(self, "Twinleaf Monitor")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        menubar = tk.Menu(container)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save", command = lambda: popupmsg("Not supported yet!"))
        filemenu.add_command(label="Quit", command=quit)
        menubar.add_cascade(label="File", menu=filemenu)

        dataTF = tk.Menu(menubar, tearoff=1)
        #dataTF.add_command(label = "Pause/Resume", command = lambda: loadChart())
        #dataTF.add_command(label = "Change Window Length", command = lambda: changeTimeFrame())
        menubar.add_cascade(label = "Graph Settings", menu = dataTF)

        helpmenu = tk.Menu(menubar, tearoff = 0)
        #helpmenu.add_command(label = "Tutorial", command = lambda: tutorial())
        menubar.add_cascade(label = "Help", menu = helpmenu)

        tk.Tk.config(self, menu=menubar)

        self.frames = {}
        for F in (StartPage, Page1):
            frame = F(tio, plotter, vmrStreamList, defaultStream, windowLength, container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class StartPage(tk.Frame):

    def __init__(self, tio,plotter, vmrStreamList, defaultStream, windowLength, parent, controller):
        tk.Frame.__init__(self,parent)
        label = tk.Label(self, text="Available Streams", font = LARGE_FONT, fg = 'dark green')
        label.pack()

        description = tk.Label(self, text = "Load available streams by typing them into the entry box below.  Entered stream values should look like: 'vmr0.vector, vmr1.bar', where different streams are separated by a comma. Only one stream from each device can be added.", bg = 'white', wraplength = 500)
        description.pack()

        def streamChart(tio):
            subframe = tk.Frame(self)
            labels = []
            streamb = []
            deviceAttributes = findConnectedDevices(tio)
            i = 0
            n = 0           
            for device in deviceAttributes:
                labels.append(tk.Label(subframe, text = device.upper(), font = NORM_FONT))
                labels[i].grid(column = i, row = 1)
                i+=1
                if "vmr" in device.lower():
                    for j in range(len(vmrStreamList)):
                        stre = device.lower()+"." + vmrStreamList[j]
                        streamb.append(tk.Label(subframe,text = stre))
                        streamb[n].grid(column = i-1, row = j+2)
                        n +=1
            subframe.pack(pady = 20)

        streamChart(tio)

        def getStreamEntry():
            subframe2 = tk.Frame(self)
            e = ttk.Entry(subframe2)
            e.insert(0, defaultStream)
            e.pack(side = 'left')
            e.focus_set()

            def callback():
                newSList = []
                strlst = (e.get())
                strlst = re.split(r'[-,\s]\s*',strlst)
                devList = []
                for strstream in strlst:
                    strstream = strstream.split(".")
                    try:
                        devList.append(strstream[0])
                        dev = getattr(tio, strstream[0])
                        fullstream = getattr(dev, strstream[1])
                        newSList.append(fullstream)
                    except AttributeError:
                        popupmsg("Not a valid stream.  Entered stream values should look like: 'vmr0.vector, vmr1.bar', where different streams are separated by a comma.")
                        break

                if len(devList) == len(set(devList)):
                    plotter.fig.clf()
                    plotter.reinitialize(500, newSList)
                    popupmsg("Stream successfully loaded, click 'Go!' to see plot")
        
                else:
                    popupmsg("Only one stream from each device can be added.")  

            b = ttk.Button(subframe2, text = "Load Streams", width = 10, command = callback)
            b.pack(side = 'left')
            subframe2.pack()

        getStreamEntry()

        button = ttk.Button(self, text="Go!",
                            command=lambda: controller.show_frame(Page1))
        button.pack()
        quitbutton = ttk.Button(self, text = "Quit", command = quit)
        quitbutton.pack()

class Page1(tk.Frame):
    def __init__(self, tio, plotter, vmrStreamList, defaultStream, windowLength, parent, controller):
        tk.Frame.__init__(self,parent)
        

        def graphSettings():
            subframe = tk.Frame(self)
            subsubframe = tk.Frame(subframe)
            label = tk.Label(subsubframe, text = "VMR Monitor", font = LARGE_FONT, fg = 'dark green')
            label.grid(column = 0, row = 0, padx = 30)

            label2 = ttk.Label(subsubframe, text = "Change Window Length (s): ", font = NORM_FONT)
            label2.grid(column = 1, row = 0)

            e = ttk.Entry(subsubframe)
            e.insert(0, windowLength)
            e.grid(column = 2, row = 0)
            e.focus_set()

            def callback():
                length = e.get()
                windowLength = int(length)
                plotter.increaseQueueSize(windowLength)
                print("set window length to", windowLength)

            b = ttk.Button(subsubframe, text = "Submit", width = 5, command = callback)
            b.grid(column = 3, row = 0)

            subsubframe2 = tk.Frame(subframe)

            pauseb = ttk.Button(subsubframe2, text = "Pause/Resume", command = lambda: loadChart())
            pauseb.grid(column = 0, row = 0, padx = 20)

            button1 = ttk.Button(subsubframe2, text="Back to Home",
                            command=lambda: controller.show_frame(StartPage))
            button1.grid(column = 2, row = 0)

            quitbutton = ttk.Button(subsubframe2, text = "Quit", command = quit)
            quitbutton.grid(column = 3, row = 0, padx = 20)

            subsubframe.grid(row = 0, column = 0)
            subsubframe2.grid(row = 0, column = 1)

            subframe.pack()

        graphSettings()

        canvas = FigureCanvasTkAgg(plotter.fig, self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill = "both", expand = True)
        
        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side = tk.TOP, fill = "both" ,expand = True)

def main():
    # get DeviceSync
    tio = processCommandLineArgs()
    
    # get possible streams for each device, right now hardcoded for vmr
    vmrStreamList = getStreams()
    
    # get defaults for the graph 
    defaultStream, start_stream , start_length= setDefaults(tio, vmrStreamList)
    
    # create plot instance
    plotter = createPlot(start_stream, start_length)
    
    app = graphInterface(tio, plotter, vmrStreamList, defaultStream, start_length)
    app.geometry("1280x720")
    ani = matplotlib.animation.FuncAnimation(plotter.fig, plotter.animate, interval=100)#dev.data.rate())
    app.mainloop()

if __name__ == "__main__":
  main()
