#!/usr/bin/python

# Python to process iSpindel HTTP JSON and print to an e-ink screen and log

# Curl to test: 
# $ curl http://localhost:8000/ -d '{"name":"test","ID":12345678,"angle":60.123456,"temperature":23.4567,"temp_units":"C","battery":4.123456,"gravity":1.012345,"interval":123,"RSSI":-56}'

CONFIG_EPAPER = True
HOST = ''
PORT = 8000

# Libraries for data handling, ePaper, logging, webserver
import sys
import os
import time
import random
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep, strftime, gmtime
from PIL import Image,ImageDraw,ImageFont

# Waveshare 2.13" V2 (250x122)
fontdir = os.path.join(sys.path[0], 'fonts')
libdir = os.path.join(sys.path[0], 'lib')
sys.path.append(libdir)
from waveshare_epd import epd2in13_V2

# Log to both screen (DEBUG) and logfile (INFO)
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(message)s')

# Log file - just the JSON (INFO)
fh = logging.FileHandler('ispindel.log', mode='a', encoding='utf-8')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
log.addHandler(fh)

# Console - everything (DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
log.addHandler(ch)

def displayOnEPaper(epd, data):
    # Thermal readings
    tempunit = data.get('temp_units', 'C')
    tempval = data.get('temperature', 0.0)
    thermal = "Thermal: {:.1f}\u00b0{}".format(tempval, tempunit)
 
    # Other readings
    gravity = "Gravity: {:.3f}".format(data.get('gravity', 0.000))
    battery = "Battery: {:.2f}V".format(data.get('battery', 0.00))

    # Create an image
    image = Image.new('1', (epd.height, epd.width), 255)
    font = ImageFont.load(os.path.join(fontdir, '10x20.pil'))
    draw = ImageDraw.Draw(image)

    # Randomly move the text around
    x = random.randint(0,100)
    y = random.randint(0,62)

    # Print the lines of text  
    draw.text((x,y), gravity, fill=0, font=font)
    draw.text((x,y+20), thermal, fill=0, font=font)
    draw.text((x,y+40), battery, fill=0, font=font)
    
    # Display on Screen
    epd.init(epd.FULL_UPDATE)
    epd.display(epd.getbuffer(image))
    epd.sleep()

# Handler to accept the POST requests and log/display the values
class postHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Get the payload and unencode the bytes JSON to a dict
        len = int(self.headers.get('content-length'))
        postdata = self.rfile.read(len)
        jsondata = json.loads(postdata)

        # Send back an empty OK response
        self.send_response(200)
        self.send_header('Content-Length', '0')
        self.end_headers()

        # Log and write to the display
        log.info(jsondata)
        if CONFIG_EPAPER:
            displayOnEPaper(epd, jsondata)

# Use try: to capture interrupt events
try:
    # Initialise the ePaper display
    if CONFIG_EPAPER:
        # Set up the display
        epd = epd2in13_V2.EPD()

        # Clear the display
        epd.init(epd.FULL_UPDATE)
        epd.Clear(0xFF)
        sleep(2)

    # Fire up the HTTP Server with the POST handler
    with HTTPServer((HOST, PORT), postHandler) as webserver:
        webserver.serve_forever()

# This allows the display to be blanked under a controlled shutdown
except KeyboardInterrupt:    
    # Shutdown, logging and clearing as we go
    log.debug("Shutdown received")

    # Clean up the display
    if CONFIG_EPAPER:
        epd.init(epd.FULL_UPDATE)
        epd.Clear(0xFF)
        epd2in13_V2.epdconfig.module_exit()
    exit()
