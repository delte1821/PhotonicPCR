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
from utils.Thermalcycling import *
from utils.Flumeasurement import *

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