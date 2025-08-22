import speech_recognition as sr
from PyQt5.QtCore import pyqtSignal, QThread
import logging

class VoiceCommandThread(QThread):
    commandDetected = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.recognizer = sr.Recognizer()
        self.commands = {
            "start": ["hello", "begin", "mulai"],
            "stop": ["stop", "end", "berhenti"]
        }
        self.setup_microphone()

    def setup_microphone(self):
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            self.errorOccurred.emit(f"Microphone error: {str(e)}")
            self.microphone = None

    def run(self):
        if not self.microphone:
            self.errorOccurred.emit("No microphone available")
            return

        self.running = True
        with self.microphone as source:
            while self.running:
                print("Listening for commands...")  # Debugging line
                try:
                    audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=2)
                    text = self.recognizer.recognize_google(audio, language="en-US").lower()
                    print(f"Recognized: {text}")  # Debugging line
                    for cmd, keywords in self.commands.items():
                        if any(keyword in text for keyword in keywords):
                            self.commandDetected.emit(cmd)
                            break
                            
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    logging.error(f"Voice recognition error: {e}")
                    self.errorOccurred.emit("Voice command failed")
                    continue

    def stop(self):
        self.running = False
        self.wait(2000)  # Wait up to 2 seconds