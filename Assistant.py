import pyttsx3
import speech_recognition as sr
from datetime import date
import time
import eel
import webbrowser
import datetime
from pynput.keyboard import Key, Controller
from queue import Queue
import sys
import os
from os import listdir
from os.path import isfile, join

import Smart_Mouse
import subprocess
import smartboard
from threading import Thread

today = date.today()
r = sr.Recognizer()
keyboard = Controller()
engine = pyttsx3.init('sapi5')
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

file_exp_status = False
files = []
path = ''
is_awake = True

def reply(audio):
    ChatBot.addAppMsg(audio)
    print(audio)
    engine.say(audio)
    engine.runAndWait()

# Global variable to store the smartboard process
smartboard_process = None

def open_smartboard():
    global smartboard_process
    smartboard_process = subprocess.Popen(["python", "smartboard.py"])

def close_smartboard():
    global smartboard_process
    if smartboard_process is not None:
        smartboard_process.terminate()
        smartboard_process = None

class ChatBot:

    started = False
    userinputQueue = Queue()

    def isUserInput():
        return not ChatBot.userinputQueue.empty()

    def popUserInput():
        return ChatBot.userinputQueue.get()

    def close_callback(route, websockets):
        # if not websockets:
        #     print('Bye!')
        exit()

    @eel.expose
    def getUserInput(msg):
        ChatBot.userinputQueue.put(msg)
        print(msg)
    
    def close():
        ChatBot.started = False
    
    def addUserMsg(msg):
        eel.addUserMsg(msg)
    
    def addAppMsg(msg):
        eel.addAppMsg(msg)

    def start():
        path = os.path.dirname(os.path.abspath(__file__))
        eel.init(path + r'\web', allowed_extensions=['.js', '.html'])
        try:
            eel.start('index.html', mode='chrome',
                                    host='localhost',
                                    port=27005,
                                    block=False,
                                    size=(350, 480),
                                    position=(10,100),
                                    disable_cache=True,
                                    close_callback=ChatBot.close_callback)
            ChatBot.started = True
            while ChatBot.started:
                try:
                    eel.sleep(10.0)
                except:
                    #main thread exited
                    break
        
        except:
            pass

def wish():
    hour = int(datetime.datetime.now().hour)
    if hour >= 0 and hour < 12:
        reply("Good Morning!")
    elif hour >= 12 and hour < 18:
        reply("Good Afternoon!")
    else:
        reply("Good Evening!")
    reply("I am Spark, how may I help you?")

with sr.Microphone() as source:
    r.energy_threshold = 500 
    r.dynamic_energy_threshold = False

def record_audio():
    with sr.Microphone() as source:
        r.pause_threshold = 0.8
        voice_data = ''
        audio = r.listen(source, phrase_time_limit=5)
        try:
            voice_data = r.recognize_google(audio)
        except sr.RequestError:
            reply('Sorry my Service is down. Plz check your Internet connection')
        except sr.UnknownValueError:
            print('cant recognize')
            pass
        return voice_data.lower()

def respond(voice_data):
    global file_exp_status, files, is_awake, path
    print(voice_data)
    voice_data.replace('spark','')
    eel.addUserMsg(voice_data)

    if is_awake == False:
        if 'wake up' in voice_data:
            is_awake = True
            wish()

    elif 'hello' in voice_data:
        wish()

    elif 'what is your name' in voice_data:
        reply('My name is Spark!')

    elif 'date' in voice_data:
        reply(today.strftime("%B %d, %Y"))

    elif 'time' in voice_data:
        reply(str(datetime.datetime.now()).split(" ")[1].split('.')[0])

    elif 'search' in voice_data:
        reply('Searching for ' + voice_data.split('search')[1])
        url = 'https://google.com/search?q=' + voice_data.split('search')[1]
        try:
            webbrowser.get().open(url)
            reply('This is what I found')
        except:
            reply('Please check your Internet')

    elif 'location' in voice_data:
        reply('Which place are you looking for ?')
        temp_audio = record_audio()
        eel.addUserMsg(temp_audio)
        reply('Locating...')
        url = 'https://google.nl/maps/place/' + temp_audio + '/&amp;'
        try:
            webbrowser.get().open(url)
            reply('This is what I found ')
        except:
            reply('Please check your Internet')

    elif ('bye' in voice_data) or ('by' in voice_data):
        reply("Good bye! Have a nice day.")
        is_awake = False

    elif ('exit' in voice_data) or ('terminate' in voice_data):
        if Smart_Mouse.SmartMouse.gc_mode:
            Smart_Mouse.SmartMouse.gc_mode = 0
        ChatBot.close()
        sys.exit()
        
    elif ('start smart mouse' in voice_data) or ('open smart mouse' in voice_data):
        if Smart_Mouse.SmartMouse.gc_mode:
            reply('Smart Mouse is already active')
        else:
            gc = Smart_Mouse.SmartMouse()
            t = Thread(target = gc.start)
            t.start()
            reply('Starting Smart Mouse')

    elif ('stop smart mouse' in voice_data) or ('close smart mouse' in voice_data):
        if Smart_Mouse.SmartMouse.gc_mode:
            Smart_Mouse.SmartMouse.gc_mode = 0
            reply('Smart Mouse stopped')
        else:
            reply('Smart Mouse is already inactive')
    
    elif ('open smart board' in voice_data) or ('start smart board' in voice_data):
        open_smartboard()
        reply("Opening Smart Board Application.")

    elif ('close smart board' in voice_data) or ('stop smart board' in voice_data):
        close_smartboard()
        reply("Closing Smart Board Application.")

    elif 'copy' in voice_data:
        with keyboard.pressed(Key.ctrl):
            keyboard.press('c')
            keyboard.release('c')
        reply('Copied')
          
    elif 'pest'  in voice_data or 'paste' in voice_data:
        with keyboard.pressed(Key.ctrl):
            keyboard.press('v')
            keyboard.release('v')
        reply('Pasted')
        
    
                   
    else: 
        reply('I am not functioned to do this !')

t1 = Thread(target = ChatBot.start)
t1.start()

while not ChatBot.started:
    time.sleep(0.5)

wish()
voice_data = None
while True:
    if ChatBot.isUserInput():
        voice_data = ChatBot.popUserInput()
    else:
        voice_data = record_audio()

    if 'spark' in voice_data:
        try:
            respond(voice_data)
        except SystemExit:
            reply("Exit Successfull")
            break
        except:
            print("EXCEPTION raised while closing.") 
            break
