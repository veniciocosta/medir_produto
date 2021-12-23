from tkinter import * 
from tkinter.ttk import *
master = Tk() 
master.geometry("200x200") 
  
  
label = Label(master,  text ="This is the main window") 
label.pack(pady = 10) 
btn = Button(master, text ="Click to open a new window") 
btn.pack(pady = 10) 
mainloop() 