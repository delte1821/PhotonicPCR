# This code is developed by Young Jae Kim, Ji Wook Choi (Sogang University, Korea)

# History:
# 20.08.01 PCR thermal cycling
# 20.08.07 Graphical User Interface (GUI) update
# 20.08.08 Time calculation update 
# 20.08.12 PID control update 
# 20.08.12 SQL database update
# 20.10.20 Thermocouple update 
# 21.03.10 Database file update
# 21.03.11 Git repository added

# ---------------------------------------------------------------------------------------------------------------------------------------------
# Start of code


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


# ---------------------------------------------------------------------------------------------------------------------------------------------
def PCRcycle(tHS, Ths, tDE, Tde, tAN, Tan, tEX, Tex, Nc, Cond):
    
    #Initialsing
    GPIO.setmode(GPIO.BCM)
    DEBUG = 1
    
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO) # SCK: 11, MOSI: 10, MISO: 9
    cs = digitalio.DigitalInOut(board.D5)
    cs.direction = digitalio.Direction.OUTPUT
    thermocouple = MAX31856(spi, cs)
    
    # SQL operations
    conn = sqlite3.connect('PhotonicPCR.db')    # Connecting to database
    c = conn.cursor()                           # Creating cursor for access
    # Creating table with experiments index (if it does not exist)
    c.execute('CREATE TABLE IF NOT EXISTS experiments (Date varchar(255), Dataname varchar(255), Condition varchar(255))')
    # Creating table for Temperature profile
    c.execute('CREATE TABLE IF NOT EXISTS Tempprofile (Timename varchar(255), Time varchar(255), Tempname varchar(255),Temp varchar(255))')
    conn.commit()

    # Creating table in SQL database to save data to
    date = datetime.date.today()                # Determining current data
    rows = c.execute('''select * from experiments''')   # Finding previous number of experiments
    rows = rows.fetchall()
    rows = len(rows) + 1                          # Incrementing by one to create new unique index
    dataname = 'data_'+str(rows)                # Unique name for table containging cycling data
    c.execute('Insert INTO experiments (Date, Dataname, Condition) VALUES (?,?,?)',(date,dataname,Cond))  # Adding thermal data table to db
    conn.commit()                               # Comminting change to db

    # Creating table for Experimental data
    c.execute('CREATE TABLE IF NOT EXISTS ' + dataname + ' (Time, MeasT, SetT, PID, PWM, Temp)')
    
    # Defining parameters
    variables = c.execute('SELECT Value FROM Variables')
    variables = [float(item[0]) for item in variables.fetchall()]
    # Variables as imported from database
    Freq = variables[0]     # Number of measurements per second [Hz]
    Kp = variables[1]       # Value for K part
    Ki = variables[2]       # Value for I part
    Kd = variables[3]      # Value for d part
    freq_PWM = variables[4]# Frequency for PWM in Hz
    maxPID = variables[5]  # Value for conversion of PID to PWM
    
    # Initialising parameters for cycling
    j = 0           # Counter for cycles
    i = 0           # Counter for steps
    stepTime = 0     # Internal timer for step times
    setTime = 0     # Target time for step
    TotTime = 0       # Overall elappsed time
    fanon = 0       # is the cooling fan on? 0 for no, 1 for yes
    Waitt = 1 / Freq    # Wait time (s)
    
    # Defining PID doefficients
    i0 = 0
    e0 = 0
    uPID = 0
    
    # Defining pin connections
    PINPWM = 27     # Pin for PWM
    PINFAN = 17     # Pin for active cooling with fan

    # Setup SPI interface pins
    GPIO.setup(PINPWM, GPIO.OUT)
    GPIO.setup(PINFAN, GPIO.OUT)
    
    # Writing entered values to Tprof in database
    c.execute('UPDATE Tempprofile SET Time = ? WHERE Timename = ?',(tHS,'Hot Start'))
    c.execute('UPDATE Tempprofile SET Temp = ? WHERE Timename = ?',(Ths,'Hot Start'))
    c.execute('UPDATE Tempprofile SET Time = ? WHERE Timename = ?',(tDE,'Denaturation'))
    c.execute('UPDATE Tempprofile SET Temp = ? WHERE Timename = ?',(Tde,'Denaturation'))
    c.execute('UPDATE Tempprofile SET Time = ? WHERE Timename = ?',(tAN,'Annealing'))
    c.execute('UPDATE Tempprofile SET Temp = ? WHERE Timename = ?',(Tan,'Annealing'))
    c.execute('UPDATE Tempprofile SET Time = ? WHERE Timename = ?',(tEX,'Extension'))
    c.execute('UPDATE Tempprofile SET Temp = ? WHERE Timename = ?',(Tex,'Extension'))
    c.execute('UPDATE Tempprofile SET Time = ? WHERE Timename = ?',(Nc,'Cycle'))
    conn.commit()

    # Setting up PWM
    func_PWM = GPIO.PWM(PINPWM, freq_PWM)
    # Measurment loop
    func_PWM.start(0) # Starting PWM
    t0 = time.time()

    while j <= Nc:
    
        if (j == 0 & i != 66.6): # Hot start, random number so true for all i, if j = 0
            setT = Ths
            setTime = tHS
            i = 2 # So once timer is up this gets updated to cycling
        elif (j >= 0 and i == 0):     # Cycling: Denaturation
            setT = Tde
            setTime = tDE
        elif (j >= 0 and i == 1):     # Cycling: Annealing
            setT = Tan
            setTime = tAN
        elif (j >= 0 and i == 2):     # Cycling: Extension
            setT = Tex
            setTime = tEX 
    
        t1 = time.time()
        # Measuring Temperature
        Temperature = float(thermocouple.temperature)
        Temperature = round(Temperature, 4)
            
        # Determining time
        t2 = time.time()
        TotTime = t2 - t0
        TotTime = round(TotTime, 1)
        
        # Determining PID
        (uPID, e, I) = PIDcontrol(Temperature, setT, Waitt, Kp, Ki, Kd, i0, e0)
        uPID = round(uPID, 4)
    
        # Determining new Duty cycle to achieve heating / cooling
        dcycle_PWM = uPID / maxPID * 100 # Calculating new dutycycle according to PID
    
        # Making sure new Duty cycle is maximum 100% and minimum 0
        if dcycle_PWM > 100:
            dcycle_PWM = 100
            GPIO.output(PINFAN,False)
        elif dcycle_PWM < 0:
            dcycle_PWM = 0
            GPIO.output(PINFAN,True)
        
        # Updating Duty Cycle
        func_PWM.ChangeDutyCycle(dcycle_PWM)
        
        # Converting to string for writing to file
        strTotTime = str(TotTime)
        strTemperature = str(Temperature)
        strsetT = str(setT)
        struPID = str(uPID)
        strdcycle_PWM = str(dcycle_PWM)
        
        # Writing data to database
        c.execute('INSERT INTO ' +dataname + ' VALUES ('+ str(TotTime) +',' + str(Temperature) + ', ' + str(setT) + ', ' + str(uPID) + ', ' + str(dcycle_PWM) + ', 0)')
        print("Time: ", TotTime, "Temperature: ", Temperature, "PWM: ", dcycle_PWM)
        
        # Updating timers and moving to next step / cycle if required
        dt = t2 - t1
        stepTime = stepTime + dt
    
        if stepTime >= setTime:  # Time for step ellapsed
            i = i+1             # Moving on to next step
            stepTime = 0         # Reseting time
            if i >= 3:          # Moving to next cycle
                i = 0           # Reseting step counter
                j = j+1         # Moving to next cycle
                e = 0
                I = 0
                   
    # Clearing GPIOs and stopping LEDs
    func_PWM.stop() # Stoping PWM
    GPIO.cleanup()
    conn.commit()
    conn.close()
    
    print('Run Complete [', dataname, ']')
    
    return


# -------------------------------------------------------------------------
def PIDcontrol(Temperature, setT, Waitt, Kp, Ki, Kd, i0, e0):
    # Define constants
    dt = float(Waitt)
    Kp = float(Kp)
    Ki = float(Ki)
    Kd = float(Kd)
    i0 = float(i0)
    e0 = float(e0)
    # Define error
    e = setT - Temperature
    # Proportional coefficient
    uP = Kp * e
    # Integral coefficient
    I = i0 + e * dt
    uI = Ki * I
    # Differential coefficient
    dedt = (e - e0) / dt
    uD = Kd * dedt
    # update error
    e0 = e
    #Overall output
    uPID = uP + uI + uD
    
    return(uPID, e, I) 
    
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
# ------------------------------------------------------------------------
# Extracting values from database
conn2 = sqlite3.connect('PhotonicPCR.db')    # Connecting to database
c2 = conn2.cursor()                           # Creating cursor for acces

# Extracting values from imported text file
profile_time = c2.execute('SELECT Time FROM Tempprofile')
profile_time = [int(item[0]) for item in profile_time.fetchall()]
profile_temp = c2.execute('SELECT Temp FROM Tempprofile')
profile_temp = [int(item[0]) for item in profile_temp.fetchall()]

tHS = profile_time[0] # Time for denaturation
Ths = profile_temp[0] # Temperature for denaturation step       
tDE = profile_time[1] # Time for annealing step
Tde = profile_temp[1] # Temperature for annealing step
tAN = profile_time[2] # Time for extension step
Tan = profile_temp[2] # Temperature for extesnion step
tEX = profile_time[3] # Number of cycles
Tex = profile_temp[4] # Time for hot start
Nc = profile_time[4] # Temperatrue for hot start
conn2.close()

# -------------------------------------------------------------------------

root = tk.Tk() # Initialising graphical interface
h1 = tk.Label(root,justify='left',padx=10,text="Photonic PCR V1",font="Verdan 24 bold").grid(row=1, column=1)
h2 = tk.Label(root,justify='left',padx=10,text="by YJ Kim                                                 2020 ",font="Verdan 16 italic").grid(row=2, column=1)
h3 = tk.Label(root,justify='left',padx=10,text="     ",font="Verdan 24 italic").grid(row=3, column=1)


e1 = tk.Entry(root) # Time for hot start in seconds
e1.insert(0, tHS)
e2= tk.Entry(root) # Temperature for Hot start
e2.insert(0, Ths)
# Denaturation
e3 = tk.Entry(root) # Time for Denaturation step in seconds
e3.insert(0, tDE)
e4= tk.Entry(root) # Temperature for Denaturation start
e4.insert(0, Tde)
# Annealing
e5 = tk.Entry(root) # Time for Annealing step in seconds
e5.insert(0, tAN)
e6= tk.Entry(root) # Temperature for Annealing start
e6.insert(0, Tan)
# Extension
e7 = tk.Entry(root) # Time for Extension step in seconds
e7.insert(0, tEX)
e8= tk.Entry(root) # Temperature for Extension start
e8.insert(0, Tex)
# Number of cycles
e9 = tk.Entry(root) # Number of cycles
e9.insert(0, Nc)
# File name
e10 = tk.Entry(root) # file name
e10.insert(0, "test")

# Palcing Textboxes
# Hot start
tk.Label(root,text="Hot start time(s)").grid(row=4, column=0)
e1.grid(row=4, column=1)
tk.Label(root,text="Hot start temp(*C)").grid(row=4, column =2)
e2.grid(row=4, column=3)
# Denaturation
tk.Label(root,text="Denaturation time(s)").grid(row=5, column=0)
e3.grid(row=5, column=1)
tk.Label(root,text="Denaturation temp(*C)").grid(row=5, column =2)
e4.grid(row=5, column=3)
# Annealing
tk.Label(root,text="Annealing time(s)").grid(row=6, column=0)
e5.grid(row=6, column=1)
tk.Label(root,text="Annealing temp(*C)").grid(row=6, column =2)
e6.grid(row=6, column=3)
# Extension
tk.Label(root,text="Extension time(s)").grid(row=7, column=0)
e7.grid(row=7, column=1)
tk.Label(root,text="Extension temp(*C)").grid(row=7, column =2)
e8.grid(row=7, column=3)
# Cycles
tk.Label(root,text="Number of cycles").grid(row=8)
e9.grid(row=8, column=1)

tk.Label(root,text="Condition").grid(row=10, column=2)
e10.grid(row=10, column=3)

tk.Label(root, text="  ").grid(row=9)

# Start Button
button = tk.Button(root, text='Start', width=15, bg='green', command = lambda: PCRcycle(int(e1.get()),int(e2.get()),int(e3.get()),int(e4.get()),int(e5.get()),int(e6.get()),int(e7.get()),int(e8.get()),int(e9.get()), str(e10.get())))
button.grid(row=10, column=1)

tk.Label(root, text="  ").grid(row=11)

# Displaying interface
root.mainloop()