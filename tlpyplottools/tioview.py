#!/usr/bin/env python3
"""
tlview: Graphical data viewer
License: MIT
Author: Esme Rubinstein <rubinstein@twinleaf.com>, Tom Kornack <kornack@twinleaf.com>
"""

import matplotlib
import time
import argparse
import tkinter
import tlpyplot

# styles and fonts
matplotlib.use("TkAgg")
matplotlib.style.use("ggplot")

def processCommandLineArgs():
    parser = argparse.ArgumentParser(prog='tioview', 
                             description='Python Graphing Monitor')
    parser.add_argument("url", 
                nargs='?', 
                default='tcp://localhost/',
                help='URL: tcp://localhost')
    args = parser.parse_args()
    tio = tlpyplot.tldevicesync.DeviceSync(args.url)
    time.sleep(1)
    return tio

def getStreams(tio):
    deviceDict = {}
    for device in tio._routes:
        streams = []
        pstreams = tio._routes[device]._tio.protocol.streams
        for i in range(len(pstreams)):
            streams.append(pstreams[i]['source_name'])
        deviceDict[tio._routes[device]] = streams
    return deviceDict

# popup message general function
def popupmsg(msg):
    popup = tkinter.Tk()
    popup.wm_title("!")
    label = tkinter.Label(popup, text = msg)
    label.pack(side = 'top', fill = 'x', pady = 10)
    B1 = tkinter.Button(popup, text = "Ok", command = popup.destroy)
    B1.pack()
    popup.mainloop()

# pause function
# def loadChart():
#     if rtp.pause == True:
#         rtp.pause = False
#     else:
#         rtp.pause = True

# set initial stream list by looking at connected devices
def setDefaults(tio):
    start_length = 500
    defaultStream = "Enter Streams Here"
    connectedDevices = getStreams(tio)
    for key in tio._routes:
        device = tio._routes[key]
        if "sync" not in device.dev.name().lower():
            if key == '/':
                defaultStream = device.dev.name().lower() + "." + connectedDevices[device][0]
            else:
                defaultStream = device.dev.name().lower() + key + "." + connectedDevices[device][0]
            stre = getattr(device, connectedDevices[device][0])
            start_stream = [stre]
            break 
    return defaultStream, start_stream, start_length

def createPlot(streamList, windowLength):
    plotter = tlpyplot.TLPyPlot(queueLength = windowLength, streamList = streamList)
    return plotter


class graphInterface(tkinter.Tk):
    def __init__(self, tio, plotter, defaultStream, windowLength, *args, **kwargs):
        tkinter.Tk.__init__(self, *args, **kwargs)
        #tkinter.Tk.iconbitmap(self, default="clienticon.ico")
        tkinter.Tk.wm_title(self, "Twinleaf Monitor")

        container = tkinter.Frame(self)
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        menubar = tkinter.Menu(container)
        filemenu = tkinter.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save", command = lambda: popupmsg("Not supported yet!"))
        filemenu.add_command(label="Quit", command=quit)
        menubar.add_cascade(label="File", menu=filemenu)

        dataTF = tkinter.Menu(menubar, tearoff=1)
        #dataTF.add_command(label = "Pause/Resume", command = lambda: loadChart())
        #dataTF.add_command(label = "Change Window Length", command = lambda: changeTimeFrame())
        menubar.add_cascade(label = "Graph Settings", menu = dataTF)

        helpmenu = tkinter.Menu(menubar, tearoff = 0)
        #helpmenu.add_command(label = "Tutorial", command = lambda: tutorial())
        menubar.add_cascade(label = "Help", menu = helpmenu)

        tkinter.Tk.config(self, menu=menubar)

        self.frames = {}
        for F in (StartPage, GraphPage):
            frame = F(tio, plotter, defaultStream, windowLength, container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class StartPage(tkinter.Frame):

    def __init__(self, tio,plotter, defaultStream, windowLength, parent, controller):
        tkinter.Frame.__init__(self,parent)
        label = tkinter.Label(self, text="Available Streams")
        label.pack()

        description = tkinter.Label(self, text = "Load available streams by typing them into the entry box below.  Entered stream values should look like: 'vmr0.vector, vmr1.bar', where different streams are separated by a comma. Only one stream from each device can be added.", bg = 'white', wraplength = 500)
        description.pack()

        def streamChart(tio):
            subframe = tkinter.Frame(self)
            labels = []
            streamb = []
            deviceAttributes = getStreams(tio)
            i = 0
            n = 0           
            for key in tio._routes:
                device = tio._routes[key]
                labels.append(tkinter.Label(subframe, text = device.dev.name()))
                labels[i].grid(column = i, row = 1)
                i+=1
                if 'sync' not in device.dev.name().lower():
                    for j in range(len(deviceAttributes[device])):
                        if key == '/':
                            stre = device.dev.name().lower()+"." + deviceAttributes[device][j]
                        else:
                            stre = device.dev.name().lower()+key+"." + deviceAttributes[device][j]
                        streamb.append(tkinter.Label(subframe,text = stre))
                        streamb[n].grid(column = i-1, row = j+2)
                        n +=1
            subframe.pack(pady = 20)

        streamChart(tio)

        def getStreamEntry():
            subframe2 = tkinter.Frame(self)
            e = tkinter.Entry(subframe2)
            e.insert(0, defaultStream)
            e.pack(side = 'left')
            e.focus_set()

            def callback():
                newSList = []
                strlst = (e.get())
                strlst = strlst.split(", ")
                devList = []
                for strstream in strlst:
                    strstream = strstream.split(".")
                    try:
                        devList.append(strstream[0])
                        dev = getattr(tio, strstream[0])
                        fullstream = getattr(dev, strstream[1])
                        newSList.append(fullstream)
                    except AttributeError:
                        popupmsg("Not a valid stream.  Entered stream values should look like: 'vmr0.vector, vmr1.bar', where different streams are separated by a comma and a space.")
                        break

                if len(devList) == len(set(devList)):
                    plotter.fig.clf()
                    plotter.reinitialize(500, newSList)
                    popupmsg("Stream successfully loaded, click 'Go!' to see plot")
        
                else:
                    popupmsg("Only one stream from each device can be added.")  

            b = tkinter.Button(subframe2, text = "Load Streams", width = 10, command = callback)
            b.pack(side = 'left')
            subframe2.pack()

        getStreamEntry()

        button = tkinter.Button(self, text="Go!",
                            command=lambda: controller.show_frame(GraphPage))
        button.pack()
        quitbutton = tkinter.Button(self, text = "Quit", command = quit)
        quitbutton.pack()

class GraphPage(tkinter.Frame):
    def __init__(self, tio, plotter, defaultStream, windowLength, parent, controller):
        tkinter.Frame.__init__(self,parent)
        

        def graphSettings():
            subframe = tkinter.Frame(self)
            subsubframe = tkinter.Frame(subframe)
            # label = tkinter.Label(subsubframe, text = "TIO Monitor")
            # label.grid(column = 0, row = 0, padx = 30)

            label2 = tkinter.Label(subsubframe, text = "Window Duration (s)")
            label2.grid(column = 1, row = 0)

            e = tkinter.Entry(subsubframe)
            e.insert(0, windowLength)
            e.grid(column = 2, row = 0)
            e.focus_set()

            def callback():
                seconds = e.get()
                rate = plotter.ss.rate()
                windowLength = int(seconds)*int(rate)
                plotter.changeQueueSize(windowLength)
                #print("set window length to", windowLength)

            b = tkinter.Button(subsubframe, text = "Submit", width = 5, command = callback)
            b.grid(column = 3, row = 0, padx = 20)

            subsubframe2 = tkinter.Frame(subframe)

            # pauseb = tkinter.Button(subsubframe2, text = "Pause/Resume", command = lambda: loadChart())
            # pauseb.grid(column = 0, row = 0, padx = 20)

            button1 = tkinter.Button(subsubframe2, text="Back to Home",
                            command=lambda: controller.show_frame(StartPage))
            button1.grid(column = 2, row = 0, padx = 20)

            quitbutton = tkinter.Button(subsubframe2, text = "Quit", command = quit)
            quitbutton.grid(column = 3, row = 0, padx = 20)

            subsubframe.grid(row = 0, column = 0)
            subsubframe2.grid(row = 0, column = 1)

            subframe.pack()

        graphSettings()

        canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(plotter.fig, self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill = "both", expand = True)
        
        toolbar = matplotlib.backends.backend_tkagg.NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side = tkinter.TOP, fill = "both" ,expand = True)

def main():
    # get DeviceSync
    tio = processCommandLineArgs()
    
    # get defaults for the graph 
    defaultStream, start_stream , start_length= setDefaults(tio)
    
    # create plot instance
    plotter = createPlot(start_stream, start_length)
    
    app = graphInterface(tio, plotter, defaultStream, start_length)
    app.geometry("1280x720")
    ani = matplotlib.animation.FuncAnimation(plotter.fig, plotter.animate, interval=100)#dev.data.rate())
    app.mainloop()

if __name__ == "__main__":
    main()
