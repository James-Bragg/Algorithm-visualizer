from tkinter import *
import tkinter as tk

from PIL import ImageTk, Image #pip install pillow
import sqlite3

# constants
n_height = 560
n_width = 610

cr_back = '#1d2a48'
cr_white = '#FFFFFF'
cr_text = '#fff'
cr_button = '#48fee7'
cr_bg_text = '#0c171d'
str_title = 'Algorithm Visualizer'


#These are the variables to be passed into SQL
NumbersList = [] #List to append numbers into
SortList = ""

conn = sqlite3.connect('SQLDB.sqlite3')
c = conn.cursor() #Initialising cursor
conn.commit()

key = 5
alphabet = "abcde5f6g1hi7jklmn8op9q2rs0tuv3wx4yz." + " "
def Decrypt(self): #Very basic decryption
    decrypt = ""
    for i in self:
        pos = alphabet.find(i) #Loops around decryption and shifts positions of letters
        newpos = (pos - 5) % 38
        decrypt = decrypt + str(alphabet[newpos])
    return(decrypt)

def rgb_hack(rgb):
    return "#%02x%02x%02x" % rgb

def Commit():
    root = tk.Tk()
    root.title(str_title)
    root.config(bg=rgb_hack((0,108,180)))
    root.geometry('{}x{}'.format(n_width, n_height))

    
    sql = c.execute("SELECT NumbersPicked, AlgorithmChosen, TimeTaken FROM tblMain")
    #rows = c.fetchall()

    #Each label below is the heading to display the database
    e = Label(root,width=20, text="Numbers Picked", borderwidth=0,relief='ridge',fg="white", anchor="w", bg=rgb_hack((0,50,83))) 
    e.grid(row=0,column=0,pady=5,padx=5)
    e = Label(root,width=20, text="Algorithm Choice", borderwidth=0,relief='ridge',fg="white", anchor="w", bg=rgb_hack((0,50,83))) 
    e.grid(row=0,column=1,pady=5,padx=5)
    e = Label(root,width=20, text="Time Taken", borderwidth=0,relief='ridge',fg="white", anchor="w", bg=rgb_hack((0,50,83))) 
    e.grid(row=0,column=2,pady=5,padx=5)
    i=1
    for data in sql: 
        for j in range(len(data)): #For loop to cycle through rows in database
            e = Label(root, width=20, text=Decrypt(str(data[j])),borderwidth=0,bg=rgb_hack((0,50,83)),relief='ridge', anchor='w', fg='white') 
            e.grid(row=i, column=j,padx=2,pady=2) 
        i=i+1

    root.mainloop()






#Tinker Commands
#This is where the code starts