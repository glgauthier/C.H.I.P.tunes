#!/usr/bin/python
#--------------------------------------
# Original code by Matt Hawkins
# http://www.raspberrypi-spy.co.uk/
#
# Modified by Georges Gauthier to work with the NTC C.H.I.P.
# http://www.georgesgauthier.com/chip-ympd/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#--------------------------------------

#imports
import CHIP_IO.GPIO as GPIO
import time
import subprocess
import socket

from mpd import MPDClient
client = MPDClient()
client.timeout = 10                # network timeout in seconds (floats
client.idletimeout = None          # timeout for fetching the result of

# Define GPIO to LCD mapping
LCD_RS = "XIO-P4"
LCD_E  = "XIO-P2"
LCD_D4 = "XIO-P7"
LCD_D5 = "XIO-P5"
LCD_D6 = "XIO-P3"
LCD_D7 = "XIO-P6"

# Button inputs (interrput pins)
next = "XIO-P0"
playpause = "XIO-P1"
prev = "AP-EINT1"
dispmode = "AP-EINT3"

# Define some device constants
LCD_WIDTH = 16    # Maximum characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

# display cursor loc
i = 16;
j = 16;
# default display mode 
dmode = "status"

def main():
    """Set up pin interrupts and GPIO"""
    # interrupt for play/pause
    GPIO.setup(playpause, GPIO.IN)
    GPIO.add_event_detect(playpause, GPIO.RISING)
    GPIO.add_event_callback(playpause,playpauseHandler,100)
    # interrupt for next song
    GPIO.setup(next, GPIO.IN)
    GPIO.add_event_detect(next, GPIO.RISING)
    GPIO.add_event_callback(next,nextHandler,100)
    # interrupt for previous song
    GPIO.setup(prev, GPIO.IN)
    GPIO.add_event_detect(prev, GPIO.RISING)
    GPIO.add_event_callback(prev,prevHandler,100)
    # interrupt for display mode
    GPIO.setup(dispmode, GPIO.IN)
    GPIO.add_event_detect(dispmode, GPIO.RISING)
    GPIO.add_event_callback(dispmode,modeHandler,100)
    # LCD display GPIO
    GPIO.setup(LCD_E, GPIO.OUT)  # E
    GPIO.setup(LCD_RS, GPIO.OUT) # RS
    GPIO.setup(LCD_D4, GPIO.OUT) # DB4
    GPIO.setup(LCD_D5, GPIO.OUT) # DB5
    GPIO.setup(LCD_D6, GPIO.OUT) # DB6
    GPIO.setup(LCD_D7, GPIO.OUT) # DB7


    # Initialise display
    lcd_init()

    local_ip = "Connecting ... "  
    
    while True:
        # ~~~~~~~~ find local ip for debug if it hasn't already been recorded ~~~~~~~~
        if len(local_ip) < 10 or local_ip == "Connecting ... ": 
            local_ip = subprocess.check_output(["hostname","-I"])
            local_ip = local_ip[:len(local_ip)-1] #cut off \n
            if len(local_ip) < 10:
                local_ip = "Connecting ... "
        client.connect("localhost", 6600)  # connect to localhost:6600

        status = client.status()
        
        # ~~~~~~~~ only display "playback stopped" message on non-status disp mode ~~~~~~~~
        if status["state"] == "stop" and dmode != "status": 
            lcd_string("Playback Stopped",LCD_LINE_1)
            lcd_string(status["playlistlength"]+ " in queue",LCD_LINE_2)  
        elif status["state"] == "stop": # fixes crash if mpd has been started with an empty queue
            status = client.stats();
            uptime = "%.01fh uptime" % (int(status["uptime"])/3600.0)
            lcd_string(uptime,LCD_LINE_1)
            lcd_string(local_ip, LCD_LINE_2)
        
        # ~~~~~~~~ if state == paused and disp is in music mode, indicate so ~~~~~~~~
        elif status["state"] == "pause" and dmode != "status":
            lcd_string("Paused         ",LCD_LINE_1)
            lcd_string(status["song"] + " of " + status["playlistlength"],LCD_LINE_2)
        
        # ~~~~~~~~  if a song is currently playing ~~~~~~~~
        else:
        # get info on current song
            current = client.currentsong()

            # ~~~~~~~~ Scrolling artist text ~~~~~~~~
            artistLength = len(current["artist"]);
            if (artistLength) <= 16:
                artistStr = current["artist"]
            else:
                if j < (artistLength + 1):
                    artistStr = current["artist"][(-16+j):j]
                    j = j + 1
                if j == (artistLength + 1):
                    artistStr = current["artist"][(-16+j):j]
                    j = 16;

            # ~~~~~~~~ Scrolling title text ~~~~~~~~ 
            titleLength = len(current["title"]);
            if (titleLength) <= 16:
                titleStr = current["title"]
            else:
                if i < (titleLength + 1):
                    titleStr = current["title"][(-16+i):i]
                    i = i + 1
                if i == (titleLength + 1):
                    titleStr = current["title"][(-16+i):i]
                    i = 16;

        # ~~~~~~~~ Write text to display ~~~~~~~~
        updateDisplay(dmode,status,artistStr,titleStr)

        client.close()
        client.disconnect()

        time.sleep(0.5) # 1/2 second delay
        
def lcd_init():
    # Initialise display
    lcd_byte(0x33,LCD_CMD) # 110011 Initialise
    lcd_byte(0x32,LCD_CMD) # 110010 Initialise
    lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
    lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
    lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
    lcd_byte(0x01,LCD_CMD) # 000001 Clear display
    time.sleep(E_DELAY)

def lcd_byte(bits, mode):
    # Send byte to data pins
    # bits = data
    # mode = True  for character
    #        False for command
    GPIO.output(LCD_RS, mode) # RS
    # High bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits&0x10==0x10:
        GPIO.output(LCD_D4, True)
    if bits&0x20==0x20:
        GPIO.output(LCD_D5, True)
    if bits&0x40==0x40:
        GPIO.output(LCD_D6, True)
    if bits&0x80==0x80:
        GPIO.output(LCD_D7, True)
    # Toggle 'Enable' pin
    lcd_toggle_enable()
    # Low bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits&0x01==0x01:
        GPIO.output(LCD_D4, True)
    if bits&0x02==0x02:
        GPIO.output(LCD_D5, True)
    if bits&0x04==0x04:
        GPIO.output(LCD_D6, True)
    if bits&0x08==0x08:
        GPIO.output(LCD_D7, True)
    # Toggle 'Enable' pin
    lcd_toggle_enable()

def lcd_toggle_enable():
    # Toggle enable
    time.sleep(E_DELAY)
    GPIO.output(LCD_E, True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_E, False)
    time.sleep(E_DELAY)

def lcd_string(message,line):
    # Send string to display
    message = message.ljust(LCD_WIDTH," ")
    lcd_byte(line, LCD_CMD)
    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]),LCD_CHR)

def updateDisplay(dmode,status,artistStr,titleStr):
    if dmode == "songinfo": # artist and song shown on display
        lcd_string(artistStr,LCD_LINE_1)
        lcd_string(titleStr,LCD_LINE_2)
    elif dmode == "stats": # song playtime, number in playlist, and song shown
        m,s = divmod(int(float(status["elapsed"])),60)
        stamp = "%02d:%02d" % (m,s)
        songnum = str(int(status["song"]) + 1)
        lcd_string(stamp + " " + songnum + " of " + status["playlistlength"],LCD_LINE_1)
        lcd_string(titleStr,LCD_LINE_2)
    elif dmode == "status": # mpd uptime and C.H.I.P. ip address shown
        status = client.stats();
        uptime = "%.01fh uptime" % (int(status["uptime"])/3600.0)
        lcd_string(uptime,LCD_LINE_1) 
        lcd_string(local_ip, LCD_LINE_2)
        
def modeHandler(pin):
    if dmode == "songinfo":
        dmode = "stats"
    elif dmode == "stats":
        dmode = "status"
    else:
        dmode = "songinfo"
    i = 16; j = 16;

def nextHandler(pin):
    if dmode != "status":
        client.next()
    i = 16; j = 16;

def prevHandler(pin):
    if dmode != "status":
        client.previous()
    i = 16; j = 16;

def playpauseHandler(pin):
    if dmode != "status": 
        if status["state"] == "play": # if playing
            client.pause(1)
        elif status["state"] == "pause": # if paused
            client.pause(0)
        else: # if stopped
            client.play()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        lcd_byte(0x01, LCD_CMD)
        lcd_string("System Error :(",LCD_LINE_1)
        lcd_string("Please Reboot",LCD_LINE_2)
        GPIO.cleanup()
