#!/usr/bin/env python3
"""
cb_view: Graphical data viewer
License: MIT
Author: Esme Rubinstein <rubinstein@twinleaf.com>, Tom Kornack <kornack@twinleaf.com>
"""

import matplotlib
import time
import argparse
import tkinter
import tlpyplot
import numpy as np

# styles and fonts
matplotlib.use("TkAgg")
matplotlib.style.use("ggplot")

def changeQSize(widget, plotter, plotter2, tio):
    seconds = widget.get()
    rate = plotter.ss.rate()
    windowLength = int(float(seconds)*float(rate))
    plotter.changeQueueSize(windowLength)
    plotter2.changeQueueSize(windowLength)

def readTemp(tio):
    return tio.string_1_tcac_reaction6.therm()[0]

def changeTemp(widget, plotter, plotter2, tio):
    newTemp = widget.get()
    currentTemp = readTemp(tio)
    tio.string_1_tcac_reaction6.therm.pid.setpoint(int(newTemp))
    tempDiff = abs(newTemp - currentTemp)
    while tempDiff >= 3:
        time.sleep(60*5)
        currentTemp = readTemp(tio)
        tempDiff = abs(newTemp - currentTemp)

def upDownEntry(widget, direction, plotter, plotter2, tio, func):
    current = float(widget.get())
    if direction == "up":
        new = current + 1
    elif direction == "down":
        new = current - 1
    widget.delete(0,'end')
    widget.insert(0,new)
    func(widget, plotter, plotter2, tio)

def processCommandLineArgs():
    parser = argparse.ArgumentParser(prog='Cell Bakeout Monitor', 
                             description='Cell Bakeout')
    parser.add_argument("url", 
                nargs='?', 
                default='tcp://localhost/',
                help='URL: tcp://localhost')
    args = parser.parse_args()
    tio = tlpyplot.tldevicesync.DeviceSync(args.url)
    time.sleep(1)
    return tio

def saveData(plotter):
    f = tkinter.filedialog.asksaveasfile(mode = 'w', defaultextension = ".txt")
    if f is None:
        return
    a = np.asarray(plotter.alldata)
    np.savetxt(f, a.T, delimiter=",")
    f.close()

def createPlot(streamList, windowLength):
    plotter = tlpyplot.TLPyPlot(queueLength = windowLength, streamList = streamList)
    return plotter

def setDefaults(tio):
    start_length = 500
    start_stream = [tio.string_1_tcac_reaction6.therm]
    return start_stream, start_length

class graphInterface(tkinter.Tk):
    def __init__(self, tio, plotter, plotter2, windowLength, *args, **kwargs):
        tkinter.Tk.__init__(self, *args, **kwargs)
        #tkinter.Tk.iconbitmap(self, default="clienticon.ico")
        tkinter.Tk.wm_title(self, "Twinleaf Monitor")

        container = tkinter.Frame(self)
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        menubar = tkinter.Menu(container)
        filemenu = tkinter.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save", command = lambda: saveData(plotter))
        filemenu.add_command(label="Quit", command=quit)
        menubar.add_cascade(label="File", menu=filemenu)

        dataTF = tkinter.Menu(menubar, tearoff=1)
        menubar.add_cascade(label = "Graph Settings", menu = dataTF)

        helpmenu = tkinter.Menu(menubar, tearoff = 0)
        menubar.add_cascade(label = "Help", menu = helpmenu)

        tkinter.Tk.config(self, menu=menubar)

        self.frames = {}
        frame = GraphPage(tio, plotter, plotter2, windowLength, container, self)
        self.frames[GraphPage] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(GraphPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class GraphPage(tkinter.Frame):
    def __init__(self, tio, plotter, plotter2, windowLength, parent, controller):
        tkinter.Frame.__init__(self,parent)
        
        def graphSettings():
            subframe = tkinter.Frame(self)
            subsubframe = tkinter.Frame(subframe)

            label2 = tkinter.Label(subsubframe, text = "Window Duration (s)")
            label2.grid(column = 1, row = 0)

            e = tkinter.Entry(subsubframe)
            e.insert(0, int(windowLength)/int(plotter.ss.rate()))
            e.grid(column = 2, row = 0)
            e.focus_set()
            e.bind('<Return>', lambda event: changeQSize(e, plotter, plotter2, tio))
            e.bind('<Up>', lambda event: upDownEntry(e, "up", plotter, plotter2, tio, changeQSize))
            e.bind('<Down>', lambda event: upDownEntry(e, "down", plotter, plotter2, tio, changeQSize))

            label3 = tkinter.Label(subsubframe, text = "Change Set Point (C):")
            label3.grid(column=3, row =0)

            e2= tkinter.Entry(subsubframe)
            e2.insert(0, tio.string_1_tcac_reaction6.therm.pid.setpoint())
            e2.grid(column = 4, row = 0)
            e2.focus_set()
            e2.bind('<Return>', lambda event: changeTemp(e2, plotter, plotter2, tio))
            e2.bind('<Up>', lambda event: upDownEntry(e2, "up", plotter, plotter2, tio, changeTemp))
            e2.bind('<Down>', lambda event: upDownEntry(e2, "down", plotter, plotter2, tio, changeTemp))

            subsubframe2 = tkinter.Frame(subframe)

            quitbutton = tkinter.Button(subsubframe2, text = "Quit", command = quit)
            quitbutton.grid(column = 4, row = 0)

            savebutton = tkinter.Button(subsubframe2, text = "Save", command = lambda: saveData(plotter))
            savebutton.grid(column = 3, row = 0, padx = 20)

            subsubframe.grid(row = 0, column = 0)
            subsubframe2.grid(row = 0, column = 1)

            subframe.pack()

        graphSettings()

        canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(plotter.fig, self)
        #plotter.allax[0].set_ylabel("Temperature (C)")
        canvas.draw()
        canvas.get_tk_widget().pack(fill = "both", expand = True)
        canvas._tkcanvas.pack(side = tkinter.TOP, fill = "both" ,expand = True)

        canvas2 = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(plotter2.fig, self)
        #plotter2.allax[0].set_ylabel("Temperature (C)")
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill = "both", expand = True)
        canvas2._tkcanvas.pack(side = tkinter.TOP, fill = "both" ,expand = True)

def main():
    # get DeviceSync
    tio = processCommandLineArgs()
    
    # get defaults for the graph 
    start_stream , start_length = setDefaults(tio)
    
    # create plot instance
    plotter = createPlot(start_stream, start_length)
    plotter.fig.delaxes(plotter.allax[1])
    plotter.fig.delaxes(plotter.allax[2])
    plotter.allax[0].change_geometry(1,1,1)
    plotter.allax[0].set_xlabel(plotter.xlabel)
    plotter2 = createPlot([tio.uion0.pressure], 500)
    
    app = graphInterface(tio, plotter, plotter2, start_length)
    app.geometry("1290x900")
    aniv = matplotlib.animation.FuncAnimation(plotter.fig, plotter.animate, interval = 100)
    anim = matplotlib.animation.FuncAnimation(plotter2.fig, plotter2.animate, interval = 100)
    app.mainloop()

if __name__ == "__main__":
    main()