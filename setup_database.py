import mysql.connector
from mysql.connector import Error
import getpass

def setup_database():
    print("MySQL Database Setup")
    print("-" * 50)
    
    # Get MySQL root password
    password = getpass.getpass("Enter MySQL root password: ")
    
    try:
        # First try to connect to MySQL server
        print("\nConnecting to MySQL server...")
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password=password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            print("Creating voice_assistant database if it doesn't exist...")
            cursor.execute("CREATE DATABASE IF NOT EXISTS voice_assistant")
            
            # Switch to voice_assistant database
            cursor.execute("USE voice_assistant")
            
            # Create tables
            print("Creating tables...")
            
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    start_time DATETIME,
                    end_time DATETIME
                )
            """)
            
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    conversation_id INT,
                    timestamp DATETIME,
                    speaker VARCHAR(50),
                    message_text TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)
            
            # Commands table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commands (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    command_type VARCHAR(50),
                    command_text TEXT,
                    timestamp DATETIME,
                    successful BOOLEAN
                )
            """)
            
            # Preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    preference_key VARCHAR(50) UNIQUE,
                    preference_value TEXT
                )
            """)
            
            print("\nDatabase setup completed successfully!")
            print("\nNow update the password in db_manager.py with this password")
            print("Then run the main application: python vassist_gui_pyqt.py")
            
    except Error as e:
        print(f"\nError: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("\nMySQL connection closed.")

if __name__ == "__main__":
    setup_database() 