import sys
import os
import threading
import queue
import time
import speech_recognition as sr
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                            QFrame, QScrollArea, QTabWidget, QTableWidget,
                            QTableWidgetItem, QHeaderView, QComboBox, QMessageBox,
                            QLineEdit, QFormLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPainter
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

# Import the voice assistant module and database manager
import vassist
from db_manager import db 

class WorkerSignals(QObject):
    """Defines the signals available from the worker thread."""
    conversation = pyqtSignal(str, str)
    status = pyqtSignal(str, str)
    error = pyqtSignal(str)  # New signal for error messages

    # Added __init__ to properly initialize the QObject base class
    def __init__(self):
        super().__init__()

class VoiceAssistantGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set up the window
        self.setWindowTitle("Voice Assistant")
        self.setMinimumSize(800, 600)
        
        # Message queue for thread-safe communication
        self.signals = WorkerSignals()
        
        # Assistant state
        self.is_running = False
        self.assistant_thread = None
        self.should_stop = threading.Event()
        
        # Database connection state
        self.db_connected = False
        self.conversation_id = None
        
        # Try to connect to database
        try:
            self.conversation_id = db.start_conversation()
            self.db_connected = True
        except Exception as e:
            self.signals.error.emit(f"Database connection failed: {str(e)}")
            self.db_connected = False
        
        # Set up the UI
        self.init_ui()
        
        # Connect signals
        self.signals.conversation.connect(self.update_conversation)
        self.signals.status.connect(self.update_status)
        self.signals.error.connect(self.show_error)
        
        # Load user preferences
        self.load_preferences()
        
        # Add a welcome message
        self.update_conversation("SYSTEM", "Welcome to Voice Assistant! Click 'Start Listening' to begin.")

    def init_ui(self):
        """Initialize the user interface"""
        # Create central widget and tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_assistant_tab()
        self.create_history_tab()
        self.create_stats_tab()
        self.create_preferences_tab()
    
    def create_assistant_tab(self):
        """Create the main assistant tab"""
        assistant_tab = QWidget()
        layout = QVBoxLayout(assistant_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Voice Assistant")
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Status frame
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        # Status label
        self.status_label = QLabel("Status: Idle")
        self.status_label.setFont(QFont("Arial", 12))
        status_layout.addWidget(self.status_label)
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 16))
        self.status_indicator.setStyleSheet("color: gray;")
        status_layout.addWidget(self.status_indicator, alignment=Qt.AlignRight)
        
        layout.addWidget(status_frame)
        
        # Conversation display
        conversation_frame = QFrame()
        conversation_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        conversation_layout = QVBoxLayout(conversation_frame)
        conversation_layout.setContentsMargins(10, 10, 10, 10)
        
        self.conversation_display = QTextEdit()
        self.conversation_display.setReadOnly(True)
        self.conversation_display.setFont(QFont("Arial", 10))
        conversation_layout.addWidget(self.conversation_display)
        
        layout.addWidget(conversation_frame)
        
        # Control buttons
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        # Start button
        self.start_button = QPushButton("Start Listening")
        self.start_button.clicked.connect(self.start_assistant)
        control_layout.addWidget(self.start_button)
        
        # Stop button
        self.stop_button = QPushButton("Stop Listening")
        self.stop_button.clicked.connect(self.stop_assistant)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)
        
        # Spacer
        control_layout.addStretch()
        
        # Exit button
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close)
        control_layout.addWidget(exit_button)
        
        layout.addWidget(control_frame)
        
        # Wake word info
        wake_word_label = QLabel("Wake Word: 'Hey Assistant'")
        wake_word_label.setFont(QFont("Arial", 10, QFont.StyleItalic))
        wake_word_label.setAlignment(Qt.AlignCenter)
        wake_word_label.setStyleSheet("color: #666666;")
        layout.addWidget(wake_word_label)
        
        # Add tab
        self.tab_widget.addTab(assistant_tab, "Assistant")
    
    def create_history_tab(self):
        """Create the conversation history tab"""
        history_tab = QWidget()
        layout = QVBoxLayout(history_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Conversation History")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["Time", "Speaker", "Message"])
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.history_table)
        
        # Refresh button
        refresh_button = QPushButton("Refresh History")
        refresh_button.clicked.connect(self.load_conversation_history)
        layout.addWidget(refresh_button)
        
        # Add tab
        self.tab_widget.addTab(history_tab, "History")
        
        # Load initial history
        self.load_conversation_history()
    
    def create_stats_tab(self):
        """Create the statistics tab"""
        stats_tab = QWidget()
        layout = QVBoxLayout(stats_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Command Statistics")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Time period selector
        period_layout = QHBoxLayout()
        period_label = QLabel("Time Period:")
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Last 7 days", "Last 30 days", "All time"])
        self.period_combo.currentIndexChanged.connect(self.update_statistics)
        period_layout.addWidget(period_label)
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()
        layout.addLayout(period_layout)
        
        # Charts layout
        charts_layout = QHBoxLayout()
        
        # Create pie chart for command usage
        self.usage_chart = QChart()
        pie_chart_view = QChartView(self.usage_chart)
        pie_chart_view.setRenderHint(QPainter.Antialiasing)
        charts_layout.addWidget(pie_chart_view)
        
        # Create bar chart for success rate
        self.success_chart = QChart()
        bar_chart_view = QChartView(self.success_chart)
        bar_chart_view.setRenderHint(QPainter.Antialiasing)
        charts_layout.addWidget(bar_chart_view)
        
        layout.addLayout(charts_layout)
        
        # Stats table
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(3)
        self.stats_table.setHorizontalHeaderLabels(["Command Type", "Count", "Success Rate"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.stats_table)
        
        # Add tab
        self.tab_widget.addTab(stats_tab, "Statistics")
        
        # Load initial statistics
        self.update_statistics()
    
    def create_preferences_tab(self):
        """Create the preferences tab"""
        preferences_tab = QWidget()
        layout = QVBoxLayout(preferences_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_label = QLabel("Preferences")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title_label)

        # Use QFormLayout for better label-widget alignment
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.WrapLongRows)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setSpacing(10)

        # Wake Word setting
        self.wake_word_edit = QLineEdit() # Create the QLineEdit for wake word
        self.wake_word_edit.setPlaceholderText("e.g., Hey Assistant")
        form_layout.addRow("Wake Word:", self.wake_word_edit)

        # Voice Speed setting
        self.voice_speed_combo = QComboBox()
        self.voice_speed_combo.addItems(["0.8", "1.0", "1.2", "1.5"])
        form_layout.addRow("Voice Speed:", self.voice_speed_combo)

        # Voice Gender setting
        self.voice_gender_combo = QComboBox()
        self.voice_gender_combo.addItems(["Male", "Female"]) # Adjust based on available voices
        form_layout.addRow("Voice Gender:", self.voice_gender_combo)

        layout.addLayout(form_layout)

        # Save button
        save_button = QPushButton("Save Preferences")
        save_button.clicked.connect(self.save_preferences)
        layout.addWidget(save_button, alignment=Qt.AlignRight)

        layout.addStretch() # Add spacer at the bottom

        # Add tab
        self.tab_widget.addTab(preferences_tab, "Preferences")
    
    def update_conversation(self, speaker, text):
        """Add a message to the conversation display and log to database"""
        # Update the conversation display
        self.conversation_display.moveCursor(self.conversation_display.textCursor().End)
        
        # Format based on speaker
        if speaker == "USER":
            self.conversation_display.insertHtml(f'<p><span style="color: #0066cc; font-weight: bold;">You: </span>'
                                               f'<span style="color: #0066cc;">{text}</span></p>')
        elif speaker == "ASSISTANT":
            self.conversation_display.insertHtml(f'<p><span style="color: #cc6600; font-weight: bold;">Assistant: </span>'
                                               f'<span style="color: #cc6600;">{text}</span></p>')
        else:
            self.conversation_display.insertHtml(f'<p><span style="color: #999999; font-style: italic;">{text}</span></p>')
        
        # Auto-scroll to the bottom
        self.conversation_display.verticalScrollBar().setValue(
            self.conversation_display.verticalScrollBar().maximum()
        )
        
        # Log to database
        if self.conversation_id:
            db.log_message(speaker, text, self.conversation_id)
    
    def update_status(self, status, color="gray"):
        """Update the status display"""
        self.status_label.setText(f"Status: {status}")
        self.status_indicator.setStyleSheet(f"color: {color};")
    
    def start_assistant(self):
        """Start the voice assistant in a separate thread"""
        if not self.is_running:
            self.is_running = True
            self.should_stop.clear()
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Update status
            self.signals.status.emit("Starting...", "orange")
            self.signals.conversation.emit("SYSTEM", "Assistant is starting...")
            
            # Create and start the assistant thread
            self.assistant_thread = threading.Thread(target=self.run_assistant)
            self.assistant_thread.daemon = True
            self.assistant_thread.start()
    
    def stop_assistant(self):
        """Stop the voice assistant"""
        if self.is_running:
            self.signals.status.emit("Stopping...", "orange")
            self.signals.conversation.emit("SYSTEM", "Stopping assistant...")
            
            # Signal the thread to stop
            self.should_stop.set()
            
            # Wait for the thread to finish
            if self.assistant_thread and self.assistant_thread.is_alive():
                self.assistant_thread.join(timeout=2)
            
            # Update UI
            self.is_running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
            self.signals.status.emit("Idle", "gray")
            self.signals.conversation.emit("SYSTEM", "Assistant stopped")
            
            # End the conversation in the database if connected
            if self.db_connected and self.conversation_id:
                try:
                    db.end_conversation(self.conversation_id)
                    # Start a new conversation for next time
                    self.conversation_id = db.start_conversation()
                except Exception as e:
                    self.signals.error.emit(f"Database error: {str(e)}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.stop_assistant()
        # End the conversation in the database if connected
        if self.db_connected and self.conversation_id:
            try:
                db.end_conversation(self.conversation_id)
            except Exception as e:
                self.signals.error.emit(f"Database error: {str(e)}")
        event.accept()
    
    def run_assistant(self):
        """Run the voice assistant"""
        # Initialize recognizer with adjusted settings
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8
        
        # Override vassist's speak function to update the GUI
        original_speak = vassist.speak
        
        def gui_speak(text):
            """Override speak function to update GUI"""
            self.signals.conversation.emit("ASSISTANT", text)
            self.signals.status.emit("Speaking", "green")
            original_speak(text)
            if not self.should_stop.is_set():
                self.signals.status.emit("Listening", "blue")
        
        # Replace the speak function
        vassist.speak = gui_speak
        
        # Greet the user
        self.signals.conversation.emit("SYSTEM", "Assistant is ready!")
        vassist.wish_me()
        
        # Main loop
        self.signals.status.emit("Listening", "blue")
        
        while not self.should_stop.is_set():
            try:
                # Listen for wake word
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    self.signals.status.emit("Listening for wake word", "blue")
                    try:
                        audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                    except sr.WaitTimeoutError:
                        continue
                
                try:
                    # Try to recognize the wake word
                    text = recognizer.recognize_google(audio).lower()
                    
                    if self.wake_word in text:
                        self.signals.conversation.emit("USER", self.wake_word)
                        self.signals.status.emit("Active", "green")
                        vassist.speak("How can I help you?")
                        
                        # Listen for command
                        with sr.Microphone() as cmd_source:
                            recognizer.adjust_for_ambient_noise(cmd_source)
                            self.signals.status.emit("Listening for command", "blue")
                            try:
                                cmd_audio = recognizer.listen(cmd_source, timeout=5, phrase_time_limit=10)
                            except sr.WaitTimeoutError:
                                vassist.speak("I didn't hear a command. Please try again.")
                                continue
                        
                        try:
                            # Try to recognize the command
                            command = recognizer.recognize_google(cmd_audio).lower()
                            self.signals.conversation.emit("USER", command)
                            
                            # Process the command
                            self.signals.status.emit("Processing", "orange")
                            
                            # Log the command if database is connected
                            if self.db_connected:
                                try:
                                    command_type = "general"
                                    if 'wikipedia' in command:
                                        command_type = "wikipedia"
                                    elif 'youtube' in command:
                                        command_type = "youtube"
                                    elif 'time' in command:
                                        command_type = "time"
                                    elif 'email' in command:
                                        command_type = "email"
                                    db.log_command(command_type, command)
                                except Exception as e:
                                    self.signals.error.emit(f"Database logging error: {str(e)}")
                            
                            # Handle different commands
                            try:
                                if any(word in command for word in ['exit', 'goodbye', 'quit', 'bye']):
                                    vassist.speak("Goodbye! Have a great day!")
                                    self.stop_assistant()
                                    return
                                elif 'wikipedia' in command:
                                    vassist.search_wikipedia(command)
                                elif 'open youtube' in command:
                                    vassist.open_website("https://www.youtube.com")
                                elif 'open google' in command:
                                    vassist.open_website("https://www.google.com")
                                elif 'time' in command:
                                    vassist.get_time()
                                elif 'email' in command:
                                    vassist.compose_email()
                                else:
                                    # Use AI for general queries
                                    response = vassist.chat_with_ai(command)
                                    vassist.speak(response)
                            except Exception as cmd_error:
                                vassist.speak("I encountered an error processing your request.")
                                self.signals.conversation.emit("SYSTEM", f"Error: {str(cmd_error)}")
                            
                        except sr.UnknownValueError:
                            vassist.speak("I didn't catch that. Can you repeat?")
                        except sr.RequestError:
                            vassist.speak("I'm having trouble connecting to the speech recognition service.")
                        except Exception as e:
                            vassist.speak("I encountered an error processing your request.")
                            self.signals.conversation.emit("SYSTEM", f"Error: {str(e)}")
                
                except sr.UnknownValueError:
                    # No wake word detected, continue listening
                    pass
                except sr.RequestError:
                    self.signals.conversation.emit("SYSTEM", "Speech recognition service unavailable")
                    time.sleep(5)  # Wait before retrying
            
            except Exception as e:
                self.signals.conversation.emit("SYSTEM", f"Error: {str(e)}")
                time.sleep(1)
        
        # Restore original speak function
        vassist.speak = original_speak
    
    def load_conversation_history(self):
        """Load conversation history from database"""
        if not self.db_connected:
            self.signals.error.emit("Cannot load history: Database not connected")
            return
            
        try:
            history = db.get_conversation_history(limit=50)
            
            # Clear the table
            self.history_table.setRowCount(0)
            
            # Add rows to the table
            for i, message in enumerate(history):
                self.history_table.insertRow(i)
                
                # Format timestamp (handle both string and datetime objects)
                try:
                    timestamp = message['timestamp']
                    if isinstance(timestamp, str):
                        # If it's a string, just use it as is
                        formatted_time = timestamp
                    else:
                        # If it's a datetime object, format it
                        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    formatted_time = "Unknown time"
                    print(f"Error formatting timestamp: {e}")
                
                # Add items to the row
                self.history_table.setItem(i, 0, QTableWidgetItem(formatted_time))
                self.history_table.setItem(i, 1, QTableWidgetItem(message['speaker']))
                self.history_table.setItem(i, 2, QTableWidgetItem(message['message_text']))
        except Exception as e:
            self.signals.error.emit(f"Error loading history: {str(e)}")
            print(f"Detailed error: {e}")  # Add detailed error logging
    
    def update_statistics(self):
        """Update statistics charts and table"""
        if not self.db_connected:
            self.signals.error.emit("Cannot update statistics: Database not connected")
            return
            
        try:
            # Determine time period
            period_index = self.period_combo.currentIndex()
            days = [7, 30, 90, 365][period_index]
            
            # Get statistics
            stats = db.get_command_statistics(days=days)
            
            # Update charts and table
            self.update_command_chart(stats)
            self.update_command_table(stats)
        except Exception as e:
            self.signals.error.emit(f"Error updating statistics: {str(e)}")
    
    def update_command_chart(self, stats):
        """Update the command usage charts"""
        try:
            # Clear existing series from both charts
            self.usage_chart.removeAllSeries()
            self.success_chart.removeAllSeries()
            
            # Create pie series for command usage
            pie_series = QPieSeries()
            
            # Create bar series for success rates
            bar_series = QBarSeries()
            success_set = QBarSet("Success Rate (%)")
            categories = []
            
            # Add data to both charts
            for stat in stats:
                command_type = stat['command_type']
                count = stat['count']
                successful = stat['successful']
                success_rate = (successful / count) * 100 if count > 0 else 0
                
                # Add to pie chart
                pie_series.append(command_type, count)
                
                # Add to bar chart
                success_set.append(success_rate)
                categories.append(command_type)
            
            # Update pie chart
            self.usage_chart.addSeries(pie_series)
            self.usage_chart.setTitle("Command Usage")
            
            # Update bar chart
            bar_series.append(success_set)
            self.success_chart.addSeries(bar_series)
            
            # Create axes for bar chart
            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            self.success_chart.addAxis(axis_x, Qt.AlignBottom)
            bar_series.attachAxis(axis_x)
            
            axis_y = QValueAxis()
            axis_y.setRange(0, 100)
            axis_y.setTitleText("Success Rate (%)")
            self.success_chart.addAxis(axis_y, Qt.AlignLeft)
            bar_series.attachAxis(axis_y)
            
            # Set bar chart title
            self.success_chart.setTitle("Command Success Rates")
            
        except Exception as e:
            self.signals.error.emit(f"Error updating charts: {str(e)}")

    def update_command_table(self, stats):
        """Update the command statistics table"""
        try:
            # Clear the table
            self.stats_table.setRowCount(0)
            
            # Add rows to the table
            for i, stat in enumerate(stats):
                command_type = stat['command_type']
                count = stat['count']
                successful = stat['successful']
                success_rate = (successful / count) * 100 if count > 0 else 0
                
                # Add to table
                self.stats_table.insertRow(i)
                self.stats_table.setItem(i, 0, QTableWidgetItem(command_type))
                self.stats_table.setItem(i, 1, QTableWidgetItem(str(count)))
                self.stats_table.setItem(i, 2, QTableWidgetItem(f"{success_rate:.1f}%"))
                
        except Exception as e:
            self.signals.error.emit(f"Error updating command table: {str(e)}")
    
    def load_preferences(self):
        """Load user preferences from database or use defaults"""
        if self.db_connected:
            try:
                self.wake_word = db.get_user_preference("wake_word", "Hey Assistant").lower()
            except:
                self.wake_word = "Hey Assistant"
        else:
            self.wake_word = "Hey Assistant"
        
        # Load voice settings
        voice_speed = db.get_user_preference("voice_speed", "1.0")
        self.voice_speed_combo.setCurrentText(voice_speed)
        
        voice_gender = db.get_user_preference("voice_gender", "Male")
        self.voice_gender_combo.setCurrentText(voice_gender)
        
        # Apply voice settings
        self.apply_voice_settings()
    
    def save_preferences(self):
        """Save user preferences to database"""
        # Save wake word
        wake_word = self.wake_word_edit.text()
        db.set_user_preference("wake_word", wake_word)
        
        # Save voice settings
        voice_speed = self.voice_speed_combo.currentText()
        db.set_user_preference("voice_speed", voice_speed)
        
        voice_gender = self.voice_gender_combo.currentText()
        db.set_user_preference("voice_gender", voice_gender)
        
        # Apply voice settings
        self.apply_voice_settings()
        
        # Show confirmation
        QMessageBox.information(self, "Preferences Saved", "Your preferences have been saved successfully.")
    
    def apply_voice_settings(self):
        """Apply voice settings to the speech engine"""
        try:
            # Get voice settings
            voice_speed = float(self.voice_speed_combo.currentText())
            voice_gender = self.voice_gender_combo.currentText()
            
            # Apply to pyttsx3 engine
            engine = vassist.engine
            engine.setProperty('rate', int(voice_speed * 200))  # Base rate is around 200
            
            # Set voice gender
            voices = engine.getProperty('voices')
            for voice in voices:
                # This is a simplistic approach - voice selection varies by platform
                if voice_gender.lower() in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
        except Exception as e:
            print(f"Error applying voice settings: {e}")
    
    def show_error(self, message):
        """Show error message in a dialog"""
        QMessageBox.critical(self, "Error", message)

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Try to connect to database but don't block if it fails
    try:
        if not db.connection or not db.connection.is_connected():
            print("Warning: Database connection failed. Some features will be disabled.")
    except Exception as e:
        print(f"Warning: Database connection error: {e}")
    
    window = VoiceAssistantGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()