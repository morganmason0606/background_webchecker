from tkinter import *
from tkinter import messagebox, ttk

import requests
import datetime
import hashlib
import periodic

cat1banks = {
    "Bank of America": "", 
    "Bank of NY-Mellon": "", 
    "Citigroup": "", 
    "Goldman Sachs": "", 
    "JPMorgan Chase": "", 
    "Morgan Stanley": "", 
    "State Street": "", 
    "Wells Fargo": "", 
}
cat2banks ={
    "Northern Trust": "",
}

cat3banks={
    "US Bancorp": "",
}
class BankChecker(Frame):
    def __init__(self, parent: Tk, *args, **kwargs):
        super().__init__(parent, *args, *kwargs)
        self.parent = parent
        self.parent.protocol("WM_Delete_Window", self.on_closing)

    def on_closing(self):
        pass 

if __name__ == "__main__":
    root = Tk()
    app = BankChecker(root)
    app.pack(side='top', fill='both', expand=True)
    root.attributes("-topmost", True)
    root.mainloop()

