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
import sys
import time
from colorthief import ColorThief
from threading import Timer
from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image, ImageGrab
from pythonosc import udp_client

if os.name == "nt":
    from desktopmagic.screengrab_win32 import getDisplayRects, getRectAsImage, getDisplaysAsImages

window = Tk()
window.title("Colouren by Thomas P (V1.1)")
window.geometry("700x600")
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
    global Pause
    Pause = True
    global T
    T.cancel()
    time.sleep(0.25)
    T.cancel()
    time.sleep(0.25)
    sys.exit()
    # window.destroy()


def mode_average():
    mode_entry.config(text='average')
    Config['mode'] = 'average'
    mode_average_file = None
    if os.name == "posix":
        mode_average_file = open(os.path.expanduser("~/Library/Application Support/Colouren/config.json"), 'w')
    elif os.name == "nt":
        mode_average_file = open(os.path.expanduser("~\Colouren\config.json"), 'w')
    mode_average_file.write(json.dumps(Config))
    mode_average_file.close()


def mode_dominant():
    mode_entry.config(text='dominant')
    Config['mode'] = 'dominant'
    mode_dominant_file = None
    if os.name == "posix":
        mode_dominant_file = open(os.path.expanduser("~/Library/Application Support/Colouren/config.json"), 'w')
    elif os.name == "nt":
        mode_dominant_file = open(os.path.expanduser("~\Colouren\config.json"), 'w')
    mode_dominant_file.write(json.dumps(Config))
    mode_dominant_file.close()


def sel():
    var.get()
    sel_file = None
    if os.name == "posix":
        sel_file = open(os.path.expanduser("~/Library/Application Support/Colouren/config.json"), 'w')
    elif os.name == "nt":
        sel_file = open(os.path.expanduser("~\Colouren\config.json"), 'w')
    if os.name == "nt" and len(getDisplayRects()) >= 2:
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
    Config['ip'] = ip_entry.get()
    Config['port'] = port_entry.get()
    Config['optimisation'] = int(optimisation_entry.get())
    Optimisation = int(Config["optimisation"])
    Config['frequency'] = round(1 / int(frequency_entry.get()), 2)
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
        messagebox.showinfo('Yippee!', 'Correct details entered, will now begin sending information over OSC.')
        Pause = False
        verify_and_update_osc()


def calculate_and_send_packet():
    if not Pause:
        client = udp_client.SimpleUDPClient(Config['ip'], int(Config['port']))
        red = 0
        green = 0
        blue = 0
        desktop_image = None
        if os.name == "nt":
            desktop_image = getRectAsImage(getDisplayRects()[Config['display'] - 1])
        elif os.name == "posix":
            desktop_image = ImageGrab.grab()
        if Config['mode'] == 'average':
            for y in range(0, desktop_image.size[1], Optimisation):
                for x in range(0, desktop_image.size[0], Optimisation):
                    colour = desktop_image.getpixel((x, y))
                    red = red + colour[0]
                    green = green + colour[1]
                    blue = blue + colour[2]
            red = int(
                round((red / ((desktop_image.size[1] / Optimisation) * (desktop_image.size[0] / Optimisation))), 0))
            green = int(
                round((green / ((desktop_image.size[1] / Optimisation) * (desktop_image.size[0] / Optimisation))), 0))
            blue = int(
                round((blue / ((desktop_image.size[1] / Optimisation) * (desktop_image.size[0] / Optimisation))), 0))
        elif Config['mode'] == 'dominant':
            color_thief = ColorThief(desktop_image)
            colours = color_thief.get_color(quality=25)
            red, green, blue = colours
        try:
            client.send_message("/red", red)
            client.send_message("/green", green)
            client.send_message("/blue", blue)
        except socket.error:
            print("Packet Missed")
    else:
        return


T = PerpetualTimer(0.25, calculate_and_send_packet)


def verify_and_update_osc():
    global T
    global Optimisation
    Optimisation = int(Config["optimisation"])
    if Config["mode"] == "dominant":
        Config["frequency"] = 1
    T = PerpetualTimer(float(Config["frequency"]), calculate_and_send_packet)
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
                Config = {'ip': '', 'port': '', 'display': 1, 'optimisation': 10, 'frequency': 0.25, 'mode': 'average'}
                file.write(json.dumps(Config))
                file.close()
        else:
            os.makedirs(os.path.expanduser("~/Library/Application Support/Colouren"))
            file = open(os.path.expanduser("~/Library/Application Support/Colouren/config.json"), 'w+')
            Config = {'ip': '', 'port': '', 'display': 1, 'optimisation': 10, 'frequency': 0.25, 'mode': 'average'}
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
                Config = {'ip': '', 'port': '', 'display': 1, 'optimisation': 10, 'frequency': 0.25, 'mode': 'average'}
                file.write(json.dumps(Config))
                file.close()
        else:
            os.makedirs(os.path.expanduser("~\Colouren"))
            file = open(os.path.expanduser("~\Colouren\config.json"), 'w+')
            Config = {'ip': '', 'port': '', 'display': 1, 'optimisation': 10, 'frequency': 0.25, 'mode': 'average'}
            file.write(json.dumps(Config))
            file.close()

    desktop_1_img = None
    desktop_2_img = None
    if os.name == "nt":
        desktop_1_img = getDisplaysAsImages()[0]
        try:
            desktop_2_img = getDisplaysAsImages()[1]
        except IndexError:
            desktop_2_img = Image.new('RGB', (100, 100))
    elif os.name == "posix":
        desktop_1_img = ImageGrab.grab()
        desktop_2_img = Image.new('RGB', (100, 100))

    desktop_1_img = desktop_1_img.resize((int(150 * (desktop_1_img.size[0] / desktop_1_img.size[1])), 150),
                                         Image.ANTIALIAS)
    desktop_2_img = desktop_2_img.resize((int(150 * (desktop_2_img.size[0] / desktop_2_img.size[1])), 150),
                                         Image.ANTIALIAS)
    desktop_1_image = ImageTk.PhotoImage(desktop_1_img)
    desktop_2_image = ImageTk.PhotoImage(desktop_2_img)

    # Top Label
    title_label = Label(window, text="Colouren By Thomas P", bg='grey', font=("Times", 25), pady=15)
    title_label.pack(side="top")

    # Desktops Frame
    options_frame = Frame(window, bg='grey')
    options_frame.pack(side="top")

    # Instructions
    instruction_label = Label(options_frame, text="Which display do you wish to output colour information for?",
                              bg='grey', font=("Ariel", 15), pady=15)
    instruction_label.pack(side="top")

    # Create two separate frames
    left_frame = Frame(options_frame, bg='grey')
    right_frame = Frame(options_frame, bg='grey')
    left_frame.pack(side="left", expand=True)
    right_frame.pack(side="left", expand=True)

    # The Label widget is a standard Tkinter widget used to display a text or image on the screen.
    desktop_1_panel = Radiobutton(left_frame, image=desktop_1_image, variable=var, value=1, command=sel)
    desktop_1_panel.pack(side="top", expand=True)
    desktop_2_panel = Radiobutton(right_frame, image=desktop_2_image, variable=var, value=2, command=sel)
    desktop_2_panel.pack(side="top", expand=True)

    # Radio Button and Labels
    desktop_1_label = Radiobutton(left_frame, text="Display 1", variable=var, value=1, command=sel, bg='grey')
    desktop_1_label.pack(side="top")

    if os.name == "nt" and len(getDisplayRects()) >= 2:
        desktop_2_label = Radiobutton(right_frame, text="Display 2", variable=var, value=2, command=sel, bg='grey')
    else:
        desktop_2_label = Radiobutton(right_frame, text="Not Available", variable=var, value=2, command=sel, bg='grey')
    desktop_2_label.pack(side="top")

    # Set a default display
    if Config["display"] == 1:
        desktop_1_label.select()
    elif Config["display"] == 2:
        desktop_2_label.select()
    else:
        desktop_1_label.select()
    sel()

    # Title Label
    osc_label = Label(window, text="What are the details for your OSC server?", bg='grey', font=("Ariel", 15), pady=15)
    osc_label.pack(side="top")

    # Create Frame for ArtNet Information
    detailsFrame = Frame(window, bg='grey', padx=10)
    detailsFrame.pack(side="top", expand=False, fill="x")

    # IP Address
    ip_label = Label(detailsFrame, text="IP Address: ", bg='grey')
    ip_label.grid(column=0, columnspan=3, row=1, pady=2, sticky='w')
    ip_entry = Entry(detailsFrame, exportselection=0)
    ip_entry.grid(column=3, row=1, pady=2, sticky='w')

    # Port
    port_label = Label(detailsFrame, text="Port: ", bg='grey')
    port_label.grid(column=0, columnspan=3, row=2, sticky="w", pady=2)
    port_entry = Entry(detailsFrame, exportselection=0)
    port_entry.grid(column=3, columnspan=4, row=2, pady=2, sticky="w")
    port_label2 = Label(detailsFrame, text="(Default: 7700)", bg='grey')
    port_label2.grid(column=7, row=2, pady=2, sticky='w')

    # Optimisation
    optimisation_label = Label(detailsFrame, text="Optimisation: ", bg='grey')
    optimisation_label.grid(column=0, columnspan=3, row=3, pady=2, sticky='w')
    optimisation_entry = Spinbox(detailsFrame, exportselection=0, from_=1, to=15)
    optimisation_entry.grid(column=3, row=3, pady=2)
    optimisation_label2 = Label(detailsFrame, text="(Default: 10, Higher is more optimised)", bg='grey')
    optimisation_label2.grid(column=7, row=3, pady=2, sticky='w')

    # Frequency
    frequency_label = Label(detailsFrame, text="Frequency: ", bg='grey')
    frequency_label.grid(column=0, columnspan=3, row=4, pady=2, sticky='w')
    frequency_entry = Spinbox(detailsFrame, exportselection=0, from_=1, to=10)
    frequency_entry.grid(column=3, row=4, pady=2)
    frequency_label2 = Label(detailsFrame, text="(Default: 4. Amount of refreshes/second)", bg='grey')
    frequency_label2.grid(column=7, row=4, pady=2, sticky='w')

    # Mode
    mode_label = Label(detailsFrame, text="Mode: ", bg='grey')
    mode_label.grid(column=0, columnspan=3, row=5, pady=2, sticky='w')
    mode_entry = Menubutton(detailsFrame, text="average", width=20, relief=RAISED)
    mode_menu = Menu(mode_entry, tearoff=0)
    mode_entry["menu"] = mode_menu
    mode_menu.add_command(label="average", command=mode_average)
    mode_menu.add_command(label="dominant", command=mode_dominant)
    mode_entry.grid(column=3, row=5, pady=2)
    mode_label2 = Label(detailsFrame, text="(Default: average. Method of generating colour.)", bg='grey')
    mode_label2.grid(column=7, row=5, pady=2, sticky='w')

    # Apply Button
    apply_button = Button(detailsFrame, bg="grey", text="Apply", command=update_details)
    apply_button.grid(column=0, row=6, columnspan=8, pady=2)

    # Information
    # Title Label
    artnet_label = Label(window,
                         text="Colouren calculates the average colour of one of your display outputs and sends that\n"
                              "information in RGB format to another computer on the network over Open Sound Control.",
                         bg='grey', font=("Ariel", 12), pady=15)
    artnet_label.pack(side="bottom")

    # Set Defaults
    if verify_ip():
        ip_entry.insert(0, Config['ip'])
    else:
        ip_entry.insert(0, '192.168.')
    if verify_port():
        port_entry.insert(0, Config['port'])
    else:
        port_entry.insert(0, '7700')
    optimisation_entry.delete(0)
    frequency_entry.delete(0)
    if len(str(Config['optimisation'])) >= 1:
        optimisation_entry.insert(0, str(Config['optimisation']))
    else:
        optimisation_entry.insert(0, '10')
    if len(str(Config['frequency'])) >= 1:
        frequency_entry.insert(0, str(int(1 / Config['frequency'])))
    else:
        frequency_entry.insert(0, '4')
    mode_entry.config(text=Config['mode'])
    verify_and_update_osc()

    window.protocol("WM_DELETE_WINDOW", quitting)
    window.mainloop()
