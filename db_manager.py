import datetime
import json
import os
from typing import Dict, List, Optional

class DatabaseManager:
    def __init__(self):
        """Initialize database manager"""
        self.connection = True  # Simulated connection
        self.current_user_id = 1
        self.current_conversation_id = None
        self.preferences_file = "preferences.json"
        self.history_file = "conversation_history.json"
        self.stats_file = "command_stats.json"
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Initialize JSON files if they don't exist"""
        files = [self.preferences_file, self.history_file, self.stats_file]
        for file in files:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump({}, f)
    
    def _read_json(self, file: str) -> dict:
        """Read JSON file"""
        try:
            with open(file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _write_json(self, file: str, data: dict):
        """Write JSON file"""
        with open(file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def start_conversation(self) -> int:
        """Start a new conversation"""
        history = self._read_json(self.history_file)
        conversation_id = len(history) + 1
        self.current_conversation_id = conversation_id
        return conversation_id
    
    def end_conversation(self, conversation_id: int):
        """End a conversation"""
        pass  # No need to do anything in file-based storage
    
    def log_message(self, speaker: str, text: str, conversation_id: int):
        """Log a message to the conversation history"""
        history = self._read_json(self.history_file)
        if str(conversation_id) not in history:
            history[str(conversation_id)] = []
        
        message = {
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Store as formatted string
            'speaker': speaker,
            'message_text': text
        }
        history[str(conversation_id)].append(message)
        self._write_json(self.history_file, history)
    
    def log_command(self, command_type: str, command: str, success: bool = True, error: str = None):
        """Log a command execution"""
        stats = self._read_json(self.stats_file)
        if command_type not in stats:
            stats[command_type] = {'count': 0, 'successful': 0}
        
        stats[command_type]['count'] += 1
        if success:
            stats[command_type]['successful'] += 1
        
        self._write_json(self.stats_file, stats)
    
    def get_conversation_history(self, limit: int = 50) -> List[Dict]:
        """Get conversation history"""
        history = self._read_json(self.history_file)
        all_messages = []
        
        for conv_id, messages in history.items():
            all_messages.extend(messages)
        
        # Sort by timestamp and limit
        all_messages.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_messages[:limit]
    
    def get_command_statistics(self, days: int = 7) -> List[Dict]:
        """Get command statistics"""
        stats = self._read_json(self.stats_file)
        result = []
        
        for cmd_type, data in stats.items():
            result.append({
                'command_type': cmd_type,
                'count': data['count'],
                'successful': data['successful']
            })
        
        return result
    
    def get_user_preference(self, key: str, default: str = None) -> str:
        """Get a user preference"""
        prefs = self._read_json(self.preferences_file)
        return prefs.get(key, default)
    
    def set_user_preference(self, key: str, value: str):
        """Set a user preference"""
        prefs = self._read_json(self.preferences_file)
        prefs[key] = value
        self._write_json(self.preferences_file, prefs)

# Create a global instance
db = DatabaseManager()