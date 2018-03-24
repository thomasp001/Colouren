"""
Copyright © 2018 Thomas P
Permission is hereby granted, free of charge, to any person obtaining a copy of this software
and associated documentation files (the “Software”), to deal in the Software without
restriction, including without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import json
import os
import socket
from threading import Timer
from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image
from pythonosc import udp_client
from desktopmagic.screengrab_win32 import getDisplayRects, getRectAsImage, getDisplaysAsImages

window = Tk()
window.title("Colouren by Thomas P")
window.geometry("700x550")
window.configure(background='grey')
window.resizable(width=False, height=False)

var = IntVar()
Config = {}
Pause = False
Optimisation = 10
Frequency = 0.25


class PerpetualTimer:

    def __init__(self, t, h_function):
        self.t = t
        self.hFunction = h_function
        self.thread = Timer(self.t, self.handle_function)

    def handle_function(self):
        self.hFunction()
        self.thread = Timer(self.t, self.handle_function)
        self.thread.start()

    def start(self):
        self.thread.start()

    def cancel(self):
        self.thread.cancel()

    def is_alive(self):
        return self.thread.isAlive()


def quitting():
    global T
    T.cancel()
    window.destroy()


def sel():
    var.get()
    sel_file = None
    if os.name == "posix":
        sel_file = open(os.path.expanduser("~/Library/Application Support/Colouren/config.json"), 'w')
    elif os.name == "nt":
        sel_file = open(os.path.expanduser("~\Colouren\config.json"), 'w')
    if len(getDisplayRects()) >= 2:
        Config['display'] = var.get()
    else:
        Config['display'] = 1
    sel_file.write(json.dumps(Config))
    sel_file.close()


def update_details():
    global Pause
    global Optimisation
    update_details_file = None
    error = 0
    if os.name == "posix":
        update_details_file = open(os.path.expanduser("~/Library/Application Support/Colouren/config.json"), 'w')
    elif os.name == "nt":
        update_details_file = open(os.path.expanduser("~\Colouren\config.json"), 'r+')
    Config['ip'] = ipentry.get()
    Config['port'] = portentry.get()
    Config['optimisation'] = optimisationentry.get()
    Optimisation = Config["optimisation"]
    Config['frequency'] = round(1/frequencyentry.get(), 2)
    if not verify_ip():
        Pause = True
        Config['ip'] = ""
        error += 1
    if not verify_port():
        Pause = True
        Config['port'] = ""
        error += 2
    update_details_file.write(json.dumps(Config))
    update_details_file.close()
    if error == 1:
        messagebox.showerror('Whoops!', 'Looks like you don\'t have a properly formatted IP address. '
                                        'Fix your IP address to continue.')
    elif error == 2:
        messagebox.showerror('Whoops!', 'Looks like you don\'t have a properly formatted port. '
                                        'Fix your port to continue.')
    elif error == 3:
        messagebox.showerror('Whoops!', 'Looks like you don\'t have a properly formatted port and IP address.'
                                        'Fix your port to continue.')
    elif error == 0:
        messagebox.showinfo('Yippy!', 'Correct details entered, will now begin sending information over OSC.')
        Pause = False
        verify_and_update_osc()


def calculate_and_send_packet():
    if not Pause:
        client = udp_client.SimpleUDPClient(Config['ip'], int(Config['port']))
        red = 0
        green = 0
        blue = 0
        desktop_image = getRectAsImage(getDisplayRects()[Config['display'] - 1])
        for y in range(0, desktop_image.size[1], Optimisation):
            for x in range(0, desktop_image.size[0], Optimisation):
                colour = desktop_image.getpixel((x, y))
                red = red + colour[0]
                green = green + colour[1]
                blue = blue + colour[2]
        red = int(round((red / ((desktop_image.size[1] / Optimisation) * (desktop_image.size[0] / Optimisation))), 0))
        green = int(
            round((green / ((desktop_image.size[1] / Optimisation) * (desktop_image.size[0] / Optimisation))), 0))
        blue = int(round((blue / ((desktop_image.size[1] / Optimisation) * (desktop_image.size[0] / Optimisation))), 0))
        try:
            client.send_message("/red", red)
            client.send_message("/green", green)
            client.send_message("/blue", blue)
        except socket.error:
            print("Missed a packet")


T = PerpetualTimer(0.25, calculate_and_send_packet)


def verify_and_update_osc():
    global T
    global Optimisation
    Optimisation = Config["optimisation"]
    T = PerpetualTimer(Config["optimisation"], calculate_and_send_packet)
    if not T.is_alive() and verify_ip() and verify_port():
        T.start()
    else:
        return


def verify_ip():
    try:
        socket.inet_aton(Config['ip'])
        return True
    except socket.error:
        return False


def verify_port():
    try:
        if 0 <= int(Config['port']) <= 65535:
            return True
        else:
            return False
    except ValueError:
        return False


# Start Program
if __name__ == "__main__":
    # Load Configuration
    # If using MacOS
    if os.name == "posix":
        if os.path.isdir(os.path.expanduser("~/Library/Application Support/Colouren")):
            if os.path.exists(os.path.expanduser("~/Library/Application Support/Colouren/config.json")):
                file = open(os.path.expanduser("~/Library/Application Support/Colouren/config.json"), 'r')
                file_text = file.read()
                Config = json.loads(file_text)
                file.close()
            else:
                file = open(os.path.expanduser("~/Library/Application Support/Colouren/config.json"), 'w+')
                Config = {'ip': '', 'port': '', 'display': 1, 'optimisation': 10, 'refresh': 0.25}
                file.write(json.dumps(Config))
                file.close()
        else:
            os.makedirs(os.path.expanduser("~/Library/Application Support/Colouren"))
            file = open(os.path.expanduser("~/Library/Application Support/Colouren/config.json"), 'w+')
            Config = {'ip': '', 'port': '', 'display': 1, 'optimisation': 10, 'refresh': 0.25}
            file.write(json.dumps(Config))
            file.close()
    # If using Windows
    elif os.name == "nt":
        if os.path.isdir(os.path.expanduser("~\Colouren")):
            if os.path.exists(os.path.expanduser("~\Colouren\config.json")):
                file = open(os.path.expanduser("~\Colouren\config.json"), 'r')
                Config = json.loads(file.read())
                file.close()
            else:
                file = open(os.path.expanduser("~\Colouren\config.json"), 'w+')
                Config = {'ip': '', 'port': '', 'display': 1, 'optimisation': 10, 'refresh': 0.25}
                file.write(json.dumps(Config))
                file.close()
        else:
            os.makedirs(os.path.expanduser("~\Colouren"))
            file = open(os.path.expanduser("~\Colouren\config.json"), 'w+')
            Config = {'ip': '', 'port': '', 'display': 1, 'optimisation': 10, 'refresh': 0.25}
            file.write(json.dumps(Config))
            file.close()

    desktop1img = getDisplaysAsImages()[0]
    try:
        desktop2img = getDisplaysAsImages()[1]
    except IndexError:
        desktop2img = Image.new('RGB', (100, 100))

    desktop1img = desktop1img.resize((int(150 * (desktop1img.size[0] / desktop1img.size[1])), 150), Image.ANTIALIAS)
    desktop2img = desktop2img.resize((int(150 * (desktop2img.size[0] / desktop2img.size[1])), 150), Image.ANTIALIAS)
    desktop1image = ImageTk.PhotoImage(desktop1img)
    desktop2image = ImageTk.PhotoImage(desktop2img)

    # Top Label
    titlelabel = Label(window, text="Colouren By Thomas P", bg='grey', font=("Times", 25), pady=15)
    titlelabel.pack(side="top")

    # Desktops Frame
    optionsFrame = Frame(window, bg='grey')
    optionsFrame.pack(side="top")

    # Instructions
    instructionlabel = Label(optionsFrame, text="Which display do you wish to output colour information for?",
                             bg='grey', font=("Ariel", 15), pady=15)
    instructionlabel.pack(side="top")

    # Create two seperate frames
    leftFrame = Frame(optionsFrame, bg='grey')
    rightFrame = Frame(optionsFrame, bg='grey')
    leftFrame.pack(side="left", expand=True)
    rightFrame.pack(side="left", expand=True)

    # The Label widget is a standard Tkinter widget used to display a text or image on the screen.
    desktop1panel = Radiobutton(leftFrame, image=desktop1image, variable=var, value=1, command=sel)
    desktop1panel.pack(side="top", expand=True)
    desktop2panel = Radiobutton(rightFrame, image=desktop2image, variable=var, value=2, command=sel)
    desktop2panel.pack(side="top", expand=True)

    # Radio Button and Labels
    desktop1label = Radiobutton(leftFrame, text="Display 1", variable=var, value=1, command=sel, bg='grey')
    desktop1label.pack(side="top")
    if len(getDisplayRects()) >= 2:
        desktop2label = Radiobutton(rightFrame, text="Display 2", variable=var, value=2, command=sel, bg='grey')
    else:
        desktop2label = Radiobutton(rightFrame, text="Not Available", variable=var, value=2, command=sel, bg='grey')
    desktop2label.pack(side="top")

    # Set a default display
    if Config["display"] == 1:
        desktop1label.select()
    elif Config["display"] == 2:
        desktop2label.select()
    else:
        desktop1label.select()
    sel()

    # Title Label
    osclabel = Label(window, text="What are the details for your OSC server?", bg='grey', font=("Ariel", 15), pady=15)
    osclabel.pack(side="top")

    # Create Frame for ArtNet Information
    detailsFrame = Frame(window, bg='grey', padx=10)
    detailsFrame.pack(side="top", expand=False, fill="x")

    # IP Address
    iplabel = Label(detailsFrame, text="IP Address: ", bg='grey')
    iplabel.grid(column=0, columnspan=3, row=1, pady=2)
    ipentry = Entry(detailsFrame, exportselection=0)
    ipentry.grid(column=3, row=1, pady=2)

    # Port
    portlabel = Label(detailsFrame, text="Port: ", bg='grey')
    portlabel.grid(column=0, columnspan=3, row=2, sticky="w", pady=2)
    portentry = Entry(detailsFrame, exportselection=0)
    portentry.grid(column=3, columnspan=4, row=2, pady=2, sticky="w")
    portlabel2 = Label(detailsFrame, text="(Default: 7700)", bg='grey')
    portlabel2.grid(column=7, row=2, pady=2)

    # Optimisation
    optimisationlabel = Label(detailsFrame, text="Optimisation: ", bg='grey')
    optimisationlabel.grid(column=0, columnspan=3, row=3, pady=2)
    optimisationentry = Spinbox(detailsFrame, exportselection=0, _from=1, to=15)
    optimisationentry.grid(column=3, row=3, pady=2)
    optimisationlabel2 = Label(detailsFrame, text="(Default: 10, Higher is more optimised)", bg='grey')
    optimisationlabel2.grid(column=7, row=3, pady=2)

    # Frequency
    frequencylabel = Label(detailsFrame, text="Frequency: ", bg='grey')
    frequencylabel.grid(column=0, columnspan=3, row=4, pady=2)
    frequencyentry = Spinbox(detailsFrame, exportselection=0, _from=1, to=10)
    frequencyentry.grid(column=3, row=4, pady=2)
    frequencylabel2 = Label(detailsFrame, text="(Default: 4. Amount of refreshes/second.)", bg='grey')
    frequencylabel2.grid(column=7, row=4, pady=2)

    # Apply Button
    applybutton = Button(detailsFrame, bg="grey", text="Apply", command=update_details)
    applybutton.grid(column=0, row=4, columnspan=8, pady=2)

    # Information
    # Title Label
    artnetlabel = Label(window,
                        text="Colouren calulates the average colour of one of your display outputs and sends that\n"
                             "information in RGB format to another computer on the network over Open Sound Control.",
                        bg='grey', font=("Ariel", 12), pady=15)
    artnetlabel.pack(side="bottom")

    # Set Defaults
    if verify_ip():
        ipentry.insert(0, Config['ip'])
    else:
        ipentry.insert(0, '192.168.')
    if verify_port():
        portentry.insert(0, Config['port'])
    else:
        portentry.insert(0, '7700')
    if len(str(Config['optimisation'])) >= 1:
        optimisationentry.insert(0, str(Config['optimisation']))
    else:
        optimisationentry.insert(0, '10')
    if len(str(Config['frequency'])) >= 1:
        frequencyentry.insert(0, str(1/Config['frequency']))
    else:
        frequencyentry.insert(0, '4')
    verify_and_update_osc()

    window.protocol("WM_DELETE_WINDOW", quitting)
    window.mainloop()
