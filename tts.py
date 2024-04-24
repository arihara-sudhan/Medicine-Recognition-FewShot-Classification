import pyttsx3
engine = pyttsx3.init() # object creation
rate = engine.getProperty('rate')
engine.setProperty('rate', 125)

def speak(txt):
    engine.say(txt)
    engine.runAndWait()
    engine.stop()
