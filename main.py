import sys
import sqlite3
import speech_recognition as sr
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject
import application




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
        self.setWindowTitle("Speech Recognition App")
        self.setGeometry(0, 0, 1920//2, 1080//2)  # Set window size to half of full screen
        self.status_txt = "Hello There..."
        # Set up the background image
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 1920//2, 1080//2)
        pixmap = QPixmap("./imgs/bg.png")
        self.bg_label.setPixmap(pixmap)
        self.bg_label.setScaledContents(True)

        # Create label for title
        self.title_label = QLabel("MEDICATION FOR VISUALLY CHALLENGED", self)
        font = QFont()
        font.setPointSize(20)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet("color: black;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setGeometry(0, 50, 1920//2, 50)

        # Create the button for starting speech recognition
        self.listen_button = QPushButton("START LISTENING", self)
        self.listen_button.setGeometry(380, 400, 200, 50)
        self.listen_button.setStyleSheet("color: black; border: 1px solid black; border-radius: 10px; text-align: center;")
        self.listen_button.clicked.connect(self.start_listening)

        # Create label for status text
        self.status_label = QLabel(self.status_txt, self)
        self.status_label.setGeometry(630, 500, 300, 50)  # Adjust as needed
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
            self.signal_emitter.status_updated.emit("NEW USER CREATED")
        else:
            self.signal_emitter.status_updated.emit("ONLY DIGITS ALLOWED")
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
            self.signal_emitter.status_updated.emit("LOGGED IN SUCCESSFULLY")
            application.main()
        else:
            print("User does not exist.")
            print(result)
            self.signal_emitter.status_updated.emit("LOG IN FAILED")

    def start_listening(self):
        self.listen_button.setText("LISTENING")  # Change button text

        # Run speech recognition in a separate thread
        self.thread = SpeechRecognitionThread()
        self.thread.recognition_result.connect(self.handle_recognition_result)
        self.thread.start()

    def handle_recognition_result(self, text):
        if text == "register":
            self.signal_emitter.status_updated.emit("REGISTER WITH DIGITS")
            text = self.speech_to_text()        
            self.insert_into_table(text)
        elif text == "login":
            self.signal_emitter.status_updated.emit("LOG-IN DIGITS?")
            text = self.speech_to_text()        
            self.check_login(text)
        elif text == "Unknown":
            self.signal_emitter.status_updated.emit("Sorry, could not understand audio.")
        elif text == "RequestError":
            self.signal_emitter.status_updated.emit("Error fetching results")
        else:
            print("NOTHING WE CAN DO THEN")

        # Asynchronously update button text back to "Start Listening" after 2 seconds
        QTimer.singleShot(2000, lambda: self.listen_button.setText("START LISTENING"))

    def speech_to_text(self):
        recognizer = sr.Recognizer()

        with sr.Microphone() as source:
            print("Listening...")
            self.signal_emitter.status_updated.emit("Listening...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            print("Recognizing speech...")
            self.signal_emitter.status_updated.emit("RECOGNIZING...")
            text = recognizer.recognize_google(audio)
            self.signal_emitter.status_updated.emit(text)
            return text
        except sr.UnknownValueError:
            print("Sorry, could not understand audio.")
            self.signal_emitter.status_updated.emit("Sorry, could not understand audio.")
            return None
        except sr.RequestError as e:
            print("Error fetching results; {0}".format(e))
            self.signal_emitter.status_updated.emit("DB ERROR OCCURED")
            return None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpeechApp()
    window.show()
    sys.exit(app.exec_())
