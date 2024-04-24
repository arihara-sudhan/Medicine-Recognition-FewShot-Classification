import sys
import sqlite3
import speech_recognition as sr
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject, QSize
from screeninfo import get_monitors
import application
from tts import speak

SCREEN_INFO = get_monitors()[0]

class SignalEmitter(QObject):
    status_updated = pyqtSignal(str)

class SpeechRecognitionThread(QThread):
    recognition_result = pyqtSignal(str)

    def run(self):
        recognizer = sr.Recognizer()

        with sr.Microphone() as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            print("Recognizing speech...")
            text = recognizer.recognize_google(audio)
            self.recognition_result.emit(text)
        except sr.UnknownValueError:
            print("Sorry, could not understand audio.")
            self.recognition_result.emit("Unknown")
        except sr.RequestError as e:
            print("Error fetching results; {0}".format(e))
            self.recognition_result.emit("RequestError")

class SpeechApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.x, self.y = SCREEN_INFO.x, SCREEN_INFO.y
        self.w, self.h = SCREEN_INFO.width, SCREEN_INFO.height
        self.setWindowTitle("MEDICATION FOR VISUALLY CHALLENGED")
        self.setGeometry(0, 0, self.w, self.h)  # Set window size to half of full screen
        self.status_txt = "Hello There... Please click Start Listening..."
        # SETTING BACKGROUND IMAGE
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(self.x, self.y, self.w, self.h-150)
        pixmap = QPixmap("./imgs/bg.jpg")
        self.bg_label.setPixmap(pixmap)
        self.bg_label.setScaledContents(True)

        # TITLE LABEL
        self.title_label = QLabel("MEDICATION", self)
        self.title_label1 = QLabel("F O R  V I S U A L L Y  C H A L L E N G E D", self)
        font = QFont()
        font.setFamily("Roboto")
        font.setPointSize(80)
        font.setBold(True)
        self.title_label.setFont(font)
        font.setPointSize(28)
        font.setBold(False)
        self.title_label1.setFont(font)
        self.title_label.setStyleSheet("color: black;")
        self.title_label1.setStyleSheet("color: black;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label1.setAlignment(Qt.AlignCenter)
        self.title_label.setGeometry(0, 200, 600, 100)
        self.title_label1.setGeometry(0, 260, 600, 100)

        # Create the button for starting speech recognition
        self.listen_button = QPushButton("START LISTENING", self)
        self.listen_button.setGeometry(50, 340, 250, 50)
        self.listen_button.setStyleSheet("color: black; border: 1px solid black; border-radius: 10px; text-align: center;")
        self.listen_button.clicked.connect(self.start_listening)
        self.listen_button1 = self.listen_button
        self.listen_button1 = QPushButton("EXIT", self)
        self.listen_button1.setGeometry(310, 340, 250, 50)
        self.listen_button1.setStyleSheet("color: black; border: 1px solid black; border-radius: 10px; text-align: center;")
        self.listen_button1.clicked.connect(QApplication.quit)
        # Create label for status text
        self.status_label = QLabel(self.status_txt, self)
        self.status_label.setGeometry(self.w//2-120, self.h-200, 300, 50)  # Adjust as needed
        self.status_label.setStyleSheet("color: black;")

        # Create SignalEmitter instance
        self.signal_emitter = SignalEmitter()
        self.signal_emitter.status_updated.connect(self.update_status)

    def update_status(self, text):
        self.status_txt = text
        self.status_label.setText(self.status_txt)

    def insert_into_table(self, text):
        # Connect to SQLite database
        conn = sqlite3.connect('speech.db')
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS speech_text (
                            id INTEGER PRIMARY KEY,
                            text TEXT
                        )''')

        # Insert text into table if it only contains digits
        if text.isdigit():
            cursor.execute("INSERT INTO speech_text (text) VALUES (?)", (text,))
            conn.commit()
            print("Text inserted into table.")
            speak("REGISTRATION SUCCESSFUL!")
            self.signal_emitter.status_updated.emit("NEW USER CREATED")
        else:
            self.signal_emitter.status_updated.emit("ONLY DIGITS ALLOWED")
            speak("SPEECH IS NOT CLEAR. TRY ONLY DIGITS")
            print("Text does not contain only digits. Skipping insertion.")

        # Close connection
        conn.close()

    def check_login(self, text):
        # Connect to SQLite database
        conn = sqlite3.connect('speech.db')
        cursor = conn.cursor()

        # Check if text exists in table
        cursor.execute("SELECT * FROM speech_text WHERE text=?", (text,))
        result = cursor.fetchone()

        # Close connection
        conn.close()

        if result:
            print("User exists.")
            speak("SHOW THE TABLET AND PRESS ENTER")
            self.signal_emitter.status_updated.emit("LOGGED IN SUCCESSFULLY")
            application.main()
        else:
            print("User does not exist.")
            speak("CHECK AGAIN PLEASE")
            print(result)
            self.signal_emitter.status_updated.emit("LOG IN FAILED")

    def start_listening(self):
        speak("REGISTER OR LOGIN")
        self.listen_button.setStyleSheet("background-color: black; color: white; border: 1px solid white; border-radius: 10px; text-align: center;")
        self.listen_button.setText("LISTENING")  # Change button text

        # Run speech recognition in a separate thread
        self.thread = SpeechRecognitionThread()
        self.thread.recognition_result.connect(self.handle_recognition_result)
        self.thread.start()

    def handle_recognition_result(self, text):
        if text == "register":
            speak("TELL SOME DIGITS TO REGISTER YOU")
            self.signal_emitter.status_updated.emit("REGISTER WITH DIGITS")
            text = self.speech_to_text()        
            self.insert_into_table(text)
        elif text == "login":
            speak("LOG IN WITH DIGITS YOU REGISTERED")
            self.signal_emitter.status_updated.emit("LOG-IN DIGITS?")
            text = self.speech_to_text()        
            self.check_login(text)
        elif text == "Unknown":
            speak("SORRY. WE COULD NOT UNDERSTAND YOU")
            self.signal_emitter.status_updated.emit("Sorry, could not understand audio.")
        elif text == "RequestError":
            speak("SOME SERVER ERROR OCCURED")
            self.signal_emitter.status_updated.emit("Error fetching results")
        else:
            print("NOTHING WE CAN DO THEN")
            speak("COULD YOU REPHRASE PLEASE?")

        # Asynchronously update button text back to "Start Listening" after 2 seconds
        QTimer.singleShot(2000, lambda: self.listen_button.setText("START LISTENING"))

    def speech_to_text(self):
        recognizer = sr.Recognizer()

        with sr.Microphone() as source:
            print("Listening...")
            speak("LISTENING TO YOU")
            self.signal_emitter.status_updated.emit("Listening...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            print("Recognizing speech...")
            speak("RECOGNIZING NOW...")
            self.signal_emitter.status_updated.emit("RECOGNIZING...")
            text = recognizer.recognize_google(audio)
            self.signal_emitter.status_updated.emit(text)
            return text
        except sr.UnknownValueError:
            speak("WE COULD NOT UNDERSTAND")
            print("Sorry, could not understand audio.")
            self.signal_emitter.status_updated.emit("Sorry, could not understand audio.")
            return None
        except sr.RequestError as e:
            speak("SERVER SIDE ERROR OCCURED")
            print("Error fetching results; {0}".format(e))
            self.signal_emitter.status_updated.emit("DB ERROR OCCURED")
            return None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpeechApp()
    window.show()
    speak("WELCOME TO MEDICINE RECOGNIZER")
    sys.exit(app.exec_())
