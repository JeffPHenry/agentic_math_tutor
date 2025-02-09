import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class DatabaseManager:
    def __init__(self, db_path: str = "user_data.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database with schema"""
        with open('schema.sql', 'r') as f:
            schema = f.read()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema)

    def get_user(self, name: str) -> Optional[Tuple[int, str]]:
        """Get user by name or create if doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM users WHERE name = ?", (name,))
            user = cursor.fetchone()
            
            if not user:
                cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
                conn.commit()
                return cursor.lastrowid, name
            
            return user

    def log_attempt(self, user_id: int, problem_number: int, answer: str, is_correct: bool):
        """Log a problem attempt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update or insert user stats
            cursor.execute("""
                INSERT INTO user_stats (user_id, problem_number, total_attempts, correct_attempts, last_attempt_at)
                VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, problem_number) DO UPDATE SET
                    total_attempts = total_attempts + 1,
                    correct_attempts = correct_attempts + CASE WHEN ? THEN 1 ELSE 0 END,
                    last_attempt_at = CURRENT_TIMESTAMP
            """, (user_id, problem_number, int(is_correct), is_correct))
            
            # Log the attempt
            cursor.execute("""
                INSERT INTO problem_attempts (user_id, problem_number, answer, is_correct)
                VALUES (?, ?, ?, ?)
            """, (user_id, problem_number, answer, is_correct))
            
            conn.commit()

    def log_chat(self, user_id: int, problem_number: int, role: str, content: str):
        """Log chat message"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_history (user_id, problem_number, role, content)
                VALUES (?, ?, ?, ?)
            """, (user_id, problem_number, role, content))
            conn.commit()

    def get_user_stats(self, user_id: int) -> List[Dict]:
        """Get user's problem statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT problem_number, total_attempts, correct_attempts
                FROM user_stats
                WHERE user_id = ?
                ORDER BY total_attempts DESC
            """, (user_id,))
            
            stats = []
            for row in cursor.fetchall():
                stats.append({
                    "problem_number": row[0],
                    "total_attempts": row[1],
                    "correct_attempts": row[2],
                    "success_rate": row[2] / row[1] if row[1] > 0 else 0
                })
            
            return stats

    def get_chat_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recent chat history for RAG context"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT problem_number, role, content, created_at
                FROM chat_history
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    "problem_number": row[0],
                    "role": row[1],
                    "content": row[2],
                    "created_at": row[3]
                })
            
            return history

    def get_challenging_problems(self, user_id: int, limit: int = 3) -> List[int]:
        """Get problems with lowest success rate"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT problem_number
                FROM user_stats
                WHERE user_id = ? AND total_attempts > 0
                ORDER BY CAST(correct_attempts AS FLOAT) / total_attempts ASC
                LIMIT ?
            """, (user_id, limit))
            
            return [row[0] for row in cursor.fetchall()]
