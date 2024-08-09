from tkinter import *
from tkinter import messagebox
from tkinter import ttk

import requests
import datetime
import hashlib

import periodic

class WebsiteChecker(Frame): 
    """
        A simple tkinter app that will check a given website on a given frequency for a change. It will create an alert box when it detects a change from when it started. 
        This app will automatically start when created.
        
        Attributes
            parent (tk.TK) : the parent/ master window 
            logging (boolean): whether the application will print out when it has checked. Default value = False            
    """

    #static var
    VALUES = {
            "5 seconds" : 5,
            "10 seconds" : 10, 
            "30 seconds": 30, 
            "1 minute": 60, 
            "2 minutes": 120, 
            "5 minutes": 300
        }
        
    def __init__(self, parent, logging=False, *args, **kwargs):       
        super().__init__(parent, *args, **kwargs) 
        self.parent = parent
        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._schedule = None
        self.logging = logging
        
        self.setup_ui()

    def setup_ui(self):
        """set up the ui for the app"""
        # title label
        self.top_lable = ttk.Label(self, text="This app will check a url for changes while running")
        self.top_lable.grid(columnspan=2, row=0)

        # url selector
        self.url_label = ttk.Label(self, text="URL (starting with http): ")
        self.url_label.grid(column=0, row=1)
        self.url_entry = ttk.Entry(self)
        self.url_entry.grid(column=1, row=1)

        # frequency selector
        self.freq_label = ttk.Label(self, text="Frequency of check:")
        self.freq_label.grid(column = 0, row=2)
        self.freq_select = ttk.Combobox(self, state="readonly", values=list(WebsiteChecker.VALUES.keys()))
        self.freq_select.grid(column = 1, row=2)

        # run and stop button
        self.run_button = ttk.Button(self, text="Run", command=self.run)
        self.run_button.grid(column=0, row=3)
        self.stop_button = ttk.Button(self, text="Stop", command=self.stop)
        self.stop_button.grid(column=1, row=3)

        # quit button
        self.quit_button = ttk.Button(self, text="Quit", command=self.on_closing)
        self.quit_button.grid(columnspan=2, column=0, row=4)
    
        #label
        self.checking_label = ttk.Label(self, text="")
        self.checking_label.grid(columnspan=2, column=0, row=5)
    def get_url(self) -> str:
        """
            gets a full url. Makes the assumption it is using the http protocol if none is given.
        """ 
        url = self.url_entry.get()
        if url[:4] != "http": 
            url = "http://" + url
        return url

    @staticmethod
    def get_http_date() -> str: 
        #builidng http data
        now = datetime.datetime.now(datetime.UTC)
        return now.strftime("%a, %d %b %Y %H:%M:%S GMT")

    def run(self): 
        """
            starts up the main application of checking a url at a given frequency
            begins with disabling input fields
            then validates and cleans values in the url field and frequency field
            finally, decides on the function to check if a page has changed, and set up a schedule (defined in periodic.py) to check the website using that method
        """
        # freezing fields
        self.run_button.config(state=DISABLED)
        self.url_entry.config(state=DISABLED)
        self.freq_select.config(state=DISABLED)

        url = self.url_entry.get()
        freq_s = self.freq_select.get()
        if(not (url and freq_s)): 
            messagebox.showerror("Error", "Select a URL and a frequency to check")
            self.stop()
            return
        
        # cleaning url, requests lib likes it to be a full url
        url = self.get_url()
        
        # making request
        try: 
            resp = requests.get(url)
        except Exception as inst:
            messagebox.showerror("Error", f"bad url :{url}")
            self.stop()
            return
        
        # checking for valid frequency
        if freq_s not in WebsiteChecker.VALUES:
            messagebox.showerror("Error", "Invalid frequency")
            self.stop()
            return
        freq = WebsiteChecker.VALUES[freq_s]


        # we can check if a page has changed using the If-Modified-Since header
        # but if the header isn't supported by the server, we will instead compare other ways

        http_date = WebsiteChecker.get_http_date()

        # sending request with haeder
        resp = requests.head(
            url=url, 
            headers = {
                "If-Modified-Since": http_date
            },
            allow_redirects=True
        )

        # if head request reflects it understand the request, we will use it to check
        if resp.status_code == 304:
            self._schedule = periodic.Periodic(freq, lambda: self.check_header(http_date))
        # if head request was not understood, we will check for other ways
        else: 
            # we can either use the Last-Modified header if it is available, or hash the response i
            # hashing the response is likely to create false positives 
            if "Last-Modified" in resp.headers:
                # our hashing function will be to compare the Last modified header value
                hashf = lambda response: response.headers['Last-Modified']
            elif "ETag" in resp.headers:
                hashf = lambda response: response.headers['ETag']
            else: 
                # our hashing function will be to compare the hashes of the response object
                hashf = lambda response: hashlib.sha256(response.text.encode('utf-8')).hexdigest() 
            
            old_val = hashf(resp)
            self._schedule = periodic.Periodic(freq, lambda: self.check_url(old_val, hashf))
        
        self.checking_label.config(text = f"Checking {url}, starting at time {http_date}")
            
    def check_header(self, old_time): 
        """
        sends a head request to see if the page has been modified since old time
        will create message box if a change has been detected

        Args:
            old_time (str): time started in RFC 7231 format
        """
        url = self.get_url()

        try: 
            resp = requests.head(
                url=url, 
                headers = {
                    "If-Modified-Since": old_time
                },
                allow_redirects=True
            )
        except:
            messagebox.showerror("Error","Error with url. Stopping")
            self.stop()
        
        if resp.status_code == 200: 
            messagebox.showinfo("Change Detected", "A change has been detected")
        elif self.logging:
            print("checked, no change")

        self.checking_label.config(text = f"last checked: {WebsiteChecker.get_http_date()}")
    
    def check_url(self, old_hash, hash_fun): 
        """
        this function lets the user check for a change using a user defined function
        it will also attempt to clean the url and will create an error box if there is an issue

        Args:
            old_hash (A'): the 'hash' value of the initial requet, can be of any type. old_hash is expected to be the output of hash_fun(first_request)
            hash_fun (Request -> A'): the hashing function used to get the hash of a function. Of expected type "Request -> type(old_hash)". 
        """
        # cleaning url, requests lib likes it to be a full url
        url = self.get_url()
            
        #checking for valid frequency
        try: 
            resp = requests.get(url)
        except:
            messagebox.showerror("Error", "Error with url")
            self.stop() # panic exit
        
        new_hash = hash_fun(resp)
        if new_hash != old_hash: 
            messagebox.showinfo("Change Detected", "A change has been detected")
        elif self.logging: 
            print("checked, no change")
        self.checking_label.config(text = f"last checked: {WebsiteChecker.get_http_date()}")
    

    def stop(self): 
        """
        this funciton stops the scheduled tasks and returns functionality to the buttons
        """
        if self._schedule:
            self._schedule.stop()
            del self._schedule
            self._schedule = None
        self.run_button.config(state=NORMAL)
        self.url_entry.config(state=NORMAL)
        self.freq_select.config(state=READABLE)

    def on_closing(self):
        self.stop()
        self.parent.destroy()    

if __name__ == "__main__":
    messagebox.showwarning("Warning", "Sending requests to a website too frequently may result in being banned")

    root = Tk()
    app = WebsiteChecker(root, True)
    app.pack(side='top', fill='both', expand=True)
    root.attributes("-topmost", True)
    root.mainloop()
