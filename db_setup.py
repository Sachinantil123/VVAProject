import mysql.connector
from mysql.connector import Error
import getpass

def setup_database():
    """Set up the MySQL database for the voice assistant"""
    print("Voice Assistant Database Setup")
    print("=============================")
    
    # Get database credentials
    host = input("MySQL Host [localhost]: ") or "localhost"
    user = input("MySQL Username [root]: ") or "root"
    password = getpass.getpass("MySQL Password: root")
    
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database
            print("\nCreating database...")
            cursor.execute("CREATE DATABASE IF NOT EXISTS voice_assistant")
            cursor.execute("USE voice_assistant")
            
            # Create tables
            print("Creating tables...")
            
            # Users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Conversations table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)
            
            # Messages table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INT AUTO_INCREMENT PRIMARY KEY,
                conversation_id INT,
                speaker ENUM('USER', 'ASSISTANT', 'SYSTEM') NOT NULL,
                message_text TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
            )
            """)
            
            # Command logs table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_logs (
                log_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                command_type VARCHAR(50) NOT NULL,
                command_text TEXT NOT NULL,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)
            
            # User preferences table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                preference_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                preference_key VARCHAR(50) NOT NULL,
                preference_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE KEY (user_id, preference_key)
            )
            """)
            
            # Insert default user if not exists
            cursor.execute("SELECT user_id FROM users WHERE username = 'default_user'")
            if not cursor.fetchone():
                cursor.execute("INSERT INTO users (username) VALUES ('default_user')")
            
            # Commit changes
            connection.commit()
            
            # Update db_manager.py with credentials
            print("\nUpdating database configuration...")
            with open('db_manager.py', 'r') as file:
                content = file.read()
            
            # Replace database configuration
            import re
            content = re.sub(r"'host': '.*?'", f"'host': '{host}'", content)
            content = re.sub(r"'user': '.*?'", f"'user': '{user}'", content)
            content = re.sub(r"'password': '.*?'", f"'password': '{password}'", content)
            
            with open('db_manager.py', 'w') as file:
                file.write(content)
            
            print("\nDatabase setup completed successfully!")
            print("You can now run the voice assistant application.")
            
    except Error as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    setup_database()