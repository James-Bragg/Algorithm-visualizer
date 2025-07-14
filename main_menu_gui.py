from tkinter import *
from pygame_visualizer import *
import tkinter as tk
from PIL import ImageTk, Image #pip install pillow
from DBViewer import *
from tkinter import filedialog

# constants
n_height = 840
n_width = 720

cr_back = '#1d2a48'
cr_white = '#FFFFFF'
cr_text = '#fff'
cr_button = '#48fee7'
cr_bg_text = '#0c171d'
str_title = 'Algorithm Visualizer'

#These are the variables to be passed into SQL
NumbersList = [] #List to append numbers into
SortList = ""


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master

        sort_list = ["Insertion Sort", "Bubble Sort", "Selection Sort"]  # List for options on the different sorts
        # Font_tuple = ("Comic Sans MS", 20, "bold")

        title_frame = Frame(self.master)
        first_text = Label(title_frame,
                           text="Welcome to,",

                           font=("Comic Sans MS", 15, "bold")
                           , fg=cr_text, background=cr_back)
        second_text = Label(title_frame,
                           text=str_title,
                           font=("Comic Sans MS", 15, "bold"), fg=cr_button, background=cr_back)

        #Asks for what specific algorithm to choose from
        algorithm_text = Label(self.master, text="Which Algorithm do you want?")
        self.algorithm = StringVar(self.master)  # Initialiation on the dropdown menu
        self.algorithm.set(sort_list[0])  # Show default value of dropdown
        algorithm_textbox = OptionMenu(self.master, self.algorithm, *sort_list) #Drop down menu
        algorithm_text.configure(background=cr_back, font=("Comic Sans MS", 10, "bold"), fg=cr_text)
        algorithm_textbox.configure(borderwidth=0, font=("Comic Sans MS", 12, "bold"))

        #Text box to ask what number you want to input
        txt_numbers = Label(self.master, text="What numbers do you want?", font=("Comic Sans MS", 10, "bold"))
        txt_numbers.configure(background=cr_back, fg=cr_text, borderwidth=0)
        #self.numbers_box = Entry(self.master, width=10, font=12)
        #self.numbers_box.configure(background=cr_bg_text, fg=cr_text)

        #Button to allow user to upload .txt file
        commit_button = Button(self.master, height=1, width=12, text="Input Number", command=self.commitnumber, font=("Comic Sans MS", 10, "bold"))
        commit_button.configure(background=cr_white, borderwidth=0, ) 

        #If anything other than the txt file is put in, it will throw this error message        
        self.wrong_text = Label(self.master, text="    ")
        self.wrong_text.configure(background=cr_back, font=("Comic Sans MS", 10, "bold"), fg=cr_text)
        self.list_text = Label(self.master, text="    ")
        self.list_text.configure(background=cr_back, font=("Comic Sans MS", 10, "bold"), fg=cr_text)
        
        #Button for final results
        finalcommit_button = Button(self.master, height=2, width=15, text="Confirm", command=self.commitfinal, font=("Comic Sans MS", 10, "bold"))
        finalcommit_button.configure(background=cr_button, borderwidth=0, )
        
        #Button to view database
        DB_button = Button(self.master, height=2, width=15, text="View Database", command=self.DBCommit, font=("Comic Sans MS", 10, "bold"))
        DB_button.configure(background=cr_button, borderwidth=0, )

        #Image for algorithm visualizer
        img = ImageTk.PhotoImage(Image.open('./1.png'))
        label = Label(self.master, image = img)
        label.img = img
        label.configure(borderwidth=0)

        #All of these below is the order they show in
        first_text.pack(in_=title_frame, side=LEFT)
        second_text.pack(in_=title_frame, side=RIGHT)
        title_frame.pack(pady=20)
        algorithm_text.pack(pady=5)
        algorithm_textbox.pack(pady=5)
        txt_numbers.pack(pady=5)
        #self.numbers_box.pack(pady=5)
        commit_button.pack(pady=10)
        self.wrong_text.pack(pady=5)
        self.list_text.pack(pady=5)
        finalcommit_button.pack(pady=10)
        DB_button.pack(pady=10)
        label.pack(pady=10)
        
    def commitnumber(self):  # The button to enter information 
        try: #It will allow user to upload .txt file
            txt = filedialog.askopenfilename()
            with open(""+txt) as file:
                #Strips "blank" spaces so it will only get numbers from list
                self.NumbersList = [self.NumbersList.rstrip('\n') for self.NumbersList in file] 
                self.NumbersList = list(map(int,self.NumbersList))
            self.wrong_text.configure(text="") #Will show all numbers that was in txt file
            for x in self.NumbersList:
                self.list_text.config(text=repr(self.NumbersList))
        except:
            self.wrong_text.configure(text="Please enter a number") #If wrong file uploaded it will spit error message
  
    def commitfinal(self):
        algorithm_value = str(self.algorithm.get())
        SortList = algorithm_value #Make initial sortlist to be passed into different script
        sort_list = ["Selection Sort", "Bubble Sort", "Insertion Sort"]
        main(self.NumbersList, SortList)

    def DBCommit(self):
        Commit()
    
#Tinker Commands
#This is where the code starts
def start():
    root = tk.Tk()
    root.title(str_title)
    root.geometry('{}x{}'.format(n_width, n_height))
    root.configure(background=cr_back)
    app = Application(master=root)
    app.mainloop()
