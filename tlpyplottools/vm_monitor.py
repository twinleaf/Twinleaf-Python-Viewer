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


def color_change(widget, color):
    widget.config(foreground = color)

def processCommandLineArgs():
    parser = argparse.ArgumentParser(prog='vectorMonitor', 
                             description='Vector Field Graphing Monitor')
    parser.add_argument("url", 
                nargs='?', 
                default='tcp://localhost/',
                help='URL: tcp://localhost')
    args = parser.parse_args()
    tio = tlpyplot.tldevicesync.DeviceSync(args.url)
    time.sleep(1)
    return tio

# popup message general function
def popupmsg(msg):
    popup = tkinter.Tk()
    popup.wm_title("!")
    label = tkinter.Label(popup, text = msg)
    label.pack(side = 'top', fill = 'x', pady = 10)
    B1 = tkinter.Button(popup, text = "Ok", command = popup.destroy)
    B1.pack()
    popup.mainloop()

def setDefaults(tio):
    start_length = 500
    start_stream = [tio.vmr.vector]
    return start_stream, start_length

def createPlot(streamList, windowLength):
    plotter = tlpyplot.TLPyPlot(queueLength = windowLength, streamList = streamList)
    return plotter

class graphInterface(tkinter.Tk):
    def __init__(self, tio, plotter, windowLength, noiseplotter, *args, **kwargs):
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
        menubar.add_cascade(label = "Graph Settings", menu = dataTF)

        helpmenu = tkinter.Menu(menubar, tearoff = 0)
        menubar.add_cascade(label = "Help", menu = helpmenu)

        tkinter.Tk.config(self, menu=menubar)

        self.frames = {}
        frame = GraphPage(tio, plotter, windowLength, noiseplotter, container, self)
        self.frames[GraphPage] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(GraphPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class GraphPage(tkinter.Frame):
    def __init__(self, tio, plotter, windowLength, noiseplotter, parent, controller):
        tkinter.Frame.__init__(self,parent)
        
        def graphSettings():
            subframe = tkinter.Frame(self)
            subsubframe = tkinter.Frame(subframe)
            # label = tkinter.Label(subsubframe, text = "TIO Monitor")
            # label.grid(column = 0, row = 0, padx = 30)

            label2 = tkinter.Label(subsubframe, text = "Window Duration (s)")
            label2.grid(column = 1, row = 0)

            e = tkinter.Entry(subsubframe)
            e.insert(0, int(windowLength)/int(plotter.ss.rate()))
            e.grid(column = 2, row = 0)
            e.focus_set()

            def callback(var):
                seconds = e.get()
                rate = plotter.ss.rate()
                windowLength = int(float(seconds)*float(rate))
                plotter.changeQueueSize(windowLength)
                #print("set window length to", windowLength)

            e.bind('<Return>', callback)
            e.bind('<Enter>', lambda event: color_change(e, "dark green"))
            e.bind('<Leave>', lambda event: color_change(e, "black"))

            ratelabel = tkinter.Label(subsubframe, text = "Data Rate (Hz):")
            ratelabel.grid(column = 4, row = 0)

            e2 = tkinter.Entry(subsubframe)
            e2.insert(0, plotter.ss.rate())
            e2.grid(column = 5, row = 0)
            e2.focus_set()

            def rateCallback(var):
                rate = e2.get()
                rate = float(rate)
                tio._routes['/'].data.rate(rate)
                plotter.fig.clf()
                plotter.reinitialize(plotter.queueLength, plotter.streamList)
                plotter.allax[0].set_ylabel("Field X (nT)")
                plotter.allax[1].set_ylabel("Field Y (nT)")
                plotter.allax[2].set_ylabel("Field Z (nT)")
                
            e2.bind('<Return>', rateCallback)
            e2.bind('<Enter>', lambda event: color_change(e2, "dark green"))
            e2.bind('<Leave>', lambda event: color_change(e2, "black"))

            subsubframe2 = tkinter.Frame(subframe)

            quitbutton = tkinter.Button(subsubframe2, text = "Quit", command = quit)
            quitbutton.grid(column = 3, row = 0, padx = 20)

            subsubframe.grid(row = 0, column = 0)
            subsubframe2.grid(row = 0, column = 1)

            subframe.pack()

        graphSettings()

        def streamedValues():
            newframe = tkinter.Frame(self)
            valueDict = {}
            labels = ['BX', 'BY', 'BZ']#, 'P', 'T', 'ax', 'ay', 'az', 'gx', 'gy','gz']
            for i in range(len(labels)):
                label = tkinter.Label(newframe, text = labels[i])
                valueDict[label] = tkinter.Label(newframe)
                label.grid(column = i, row = 0)
                valueDict[label].grid(column = i, row = 1)

            def updater():
                i=0
                for key in valueDict:
                    valueDict[key].config(text = round(plotter.alldata[i][-1], 2))
                    i += 1
                self.after(100, updater)
            newframe.pack(side = 'bottom')#, pady=5)
            updater()
        
        streamedValues()

        plotter.allax[0].set_ylabel("Field X (nT)")
        plotter.allax[1].set_ylabel("Field Y (nT)")
        plotter.allax[2].set_ylabel("Field Z (nT)")
        canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(plotter.fig, self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill = "both", expand = True)
        canvas._tkcanvas.pack(side = tkinter.TOP, fill = "both" ,expand = True)

        canvas2 = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(noiseplotter.fig, self)
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
    noiseplotter = tlpyplot.vm_noiseplot.vmNoise([tio.vmr.vector], plotter)
    
    app = graphInterface(tio, plotter, start_length, noiseplotter)
    app.geometry("1290x800")
    aniv = matplotlib.animation.FuncAnimation(plotter.fig, plotter.animate, interval = 100)
    anin = matplotlib.animation.FuncAnimation(noiseplotter.fig, noiseplotter.runInThread, interval = 2000)
    app.mainloop()

if __name__ == "__main__":
    main()

