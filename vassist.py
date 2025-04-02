import subprocess
import speech_recognition as sr
import datetime
import wikipedia
import webbrowser
import pyttsx3
import ollama
from wikipedia.exceptions import DisambiguationError, PageError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Email configuration
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'dianaliess@gmail.com',
    'sender_password': 'xpyj hlpf yunp xoau',
    'contacts': {
        'diana': 'dianaelizabeth.torreslopez@triosstudent.com',
        'sachin': 'sachinantil4555@gmail.com',
        'dante': 'dante_lizzar@outlook.com',
        'sarmad': 'sarmad.mohammad@trios.com',
        '': '@.com'
    }
}

def speak(audio):
    """Text-to-speech output with fallback options"""
    print(f"ASSISTANT: {audio}")
    try:
        # Try macOS say command first
        subprocess.run(["say", "-v", "Alex", audio], check=True)
    except:
        try:
            # Fallback to pyttsx3
            engine.say(audio)
            engine.runAndWait()
        except Exception as e:
            print(f"Error in speech synthesis: {e}")

def take_command(timeout=5):
    """Listen for voice command and convert to text"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source, duration=1)
        # Set energy threshold
        recognizer.energy_threshold = 300
        # Set dynamic energy threshold
        recognizer.dynamic_energy_threshold = True
        # Set pause threshold
        recognizer.pause_threshold = 0.8
        
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            print("Processing...")
            try:
                text = recognizer.recognize_google(audio)
                print(f"Recognized: {text}")
                return text.lower()
            except sr.UnknownValueError:
                print("Could not understand audio")
                return ""
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                return ""
        except sr.WaitTimeoutError:
            print("No speech detected within timeout")
            return ""

def send_email(recipient, subject, body):
    """Send an email using configured settings"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def compose_email():
    """Guide user through email composition process"""
    # Get recipient
    speak("Who would you like to email? Your contacts are: " + ", ".join(EMAIL_CONFIG['contacts'].keys()))
    
    recipient_name = "none"
    while recipient_name == "none" or recipient_name not in EMAIL_CONFIG['contacts']:
        recipient_name = take_command()
        if recipient_name == "none":
            speak("I didn't catch that. Please say a contact name.")
        elif recipient_name not in EMAIL_CONFIG['contacts']:
            speak(f"I don't have {recipient_name} in contacts. Please try again.")
    
    recipient_email = EMAIL_CONFIG['contacts'][recipient_name]
    speak(f"Got it. Email for {recipient_name} is {recipient_email}.")

    # Get subject
    speak("What should the subject be?")
    subject = take_command()
    while subject == "none":
        speak("I didn't catch the subject. Please try again.")
        subject = take_command()

    # Get body
    speak("What would you like the email to say?")
    body = take_command()
    while body == "none":
        speak("I didn't catch the message. Please try again.")
        body = take_command()

    # Confirm
    speak(f"Ready to send to {recipient_name}. Subject: {subject}. Message: {body}. Say 'send' to confirm or 'cancel' to stop.")
    confirmation = take_command()
    
    if "send" in confirmation or "yes" in confirmation:
        if send_email(recipient_email, subject, body):
            speak(f"Email sent successfully to {recipient_name}!")
        else:
            speak("Sorry, I couldn't send the email.")
    else:
        speak("Email cancelled.")
    
    speak("Say 'Hey Assistant' if you need anything else.")

def open_website(url):
    """Open a website in the default web browser"""
    try:
        webbrowser.open(url)
        speak(f"Opening {url}")
        return True
    except Exception as e:
        speak(f"Sorry, I couldn't open {url}. Error: {str(e)}")
        return False

def search_wikipedia(query):
    """Search Wikipedia for the given query"""
    try:
        # Remove 'wikipedia' from the query
        query = query.replace('wikipedia', '').strip()
        
        # Search Wikipedia
        results = wikipedia.summary(query, sentences=2)
        speak(f"According to Wikipedia: {results}")
        
        # Open Wikipedia page
        wikipedia_url = f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
        open_website(wikipedia_url)
        
    except DisambiguationError as e:
        speak(f"There are multiple results for {query}. Please be more specific.")
    except PageError:
        speak(f"Sorry, I couldn't find any information about {query} on Wikipedia.")
    except Exception as e:
        speak(f"Sorry, I encountered an error while searching Wikipedia: {str(e)}")

def get_time():
    """Get the current time"""
    try:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {current_time}")
    except Exception as e:
        speak(f"Sorry, I couldn't get the current time. Error: {str(e)}")

def wish_me():
    """Greet the user based on time of day"""
    try:
        hour = datetime.datetime.now().hour
        if 0 <= hour < 12:
            speak("Good Morning!")
        elif 12 <= hour < 18:
            speak("Good Afternoon!")
        else:
            speak("Good Evening!")
        speak("I am your voice assistant. How can I help you?")
    except Exception as e:
        speak("Hello! I am your voice assistant. How can I help you?")

def chat_with_ai(query):
    """Chat with AI using Ollama"""
    try:
        # First try to pull the model if it doesn't exist
        try:
            ollama.pull('llama2')
        except Exception as e:
            print(f"Warning: Could not pull llama2 model: {e}")
            return "I'm having trouble connecting to the AI service. Please try again later."

        # Try to get a response
        response = ollama.chat(model='llama2', messages=[
            {
                'role': 'user',
                'content': query
            }
        ])
        return response['message']['content']
    except Exception as e:
        print(f"AI error: {e}")
        return "I'm having trouble connecting to the AI service right now."

def run_assistant():
    """Main assistant control loop"""
    recognizer = sr.Recognizer()
    
    while True:
        try:
            with sr.Microphone() as source:
                print("\nWaiting for 'Hey Assistant'...")
                audio = recognizer.listen(source, phrase_time_limit=5)
                query = recognizer.recognize_google(audio).lower()
                
                if "hey assistant" in query:
                    speak("How can I help you?")
                    command = take_command(timeout=8)
                    
                    if command == "none":
                        continue
                    elif "send email" in command or "compose email" in command:
                        compose_email()
                    elif "wikipedia" in command:
                        search_wikipedia(command)
                    elif "open youtube" in command:
                        webbrowser.open("youtube.com")
                        speak("Opening YouTube")
                    elif "open google" in command:
                        webbrowser.open("google.com")
                        speak("Opening Google")
                    elif "time" in command:
                        get_time()
                    elif "exit" in command or "quit" in command:
                        speak("Goodbye! Have a great day!")
                        return  # Exit the function
                    else:
                        response = chat_with_ai(command)
                        speak(response)
                        
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

def main():
    """Program entry point"""
    wish_me()
    run_assistant()  # Start the main loop

if __name__ == "__main__":
    main()