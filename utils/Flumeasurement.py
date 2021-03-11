# Importing required packages
import os
import RPi.GPIO as GPIO
import datetime
import board
import busio
import digitalio
from utils.MAX31856 import MAX31856
import time
import datetime
import tkinter as tk
import sqlite3
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# ------------------------------------------------------------------------
def FluMeasurement():
    # Parameters
    Vref = 0.55
    R1 = 1000
    t = 0
    delay = 0.1
    # SPI configuration
    spi = busio.SPI(clock=board.D21, MISO=board.D19, MOSI=board.D20)
    #spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
    cs = digitalio.DigitalInOut(board.D12)
    mcp = MCP.MCP3008(spi, cs)                    
    
    # AnalogToDigitalConversion
    chan0 = AnalogIn(mcp, MCP.P0)
    Abs = chan0.value
    
    return(Abs)