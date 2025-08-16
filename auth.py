"""
User Authentication Module for Novel Diver - Interactive Fanfiction MVP

This module handles user registration, login, and session management
with secure password hashing and local database storage.
"""

import hashlib
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, List
import streamlit as st


class UserAuth:
    """Handles user authentication and account management."""

    def __init__(self, db_path: str = "novel_diver_users.db"):
        self.db_path = Path(db_path)
        self._init_database()

    def _init_database(self):
        """Initialize the user database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT UNIQUE NOT NULL,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)

                # User stories table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_stories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        story_id TEXT UNIQUE NOT NULL,
                        user_id TEXT NOT NULL,
                        story_title TEXT NOT NULL,
                        character_name TEXT NOT NULL,
                        world_type TEXT NOT NULL,
                        story_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)

                # User sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        user_id TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)

                conn.commit()

        except Exception as e:
            print(f"Database initialization error: {e}")

    def _hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt."""
        if salt is None:
            salt = uuid.uuid4().hex

        password_hash = hashlib.pbkdf2_hmac('sha256',
                                            password.encode('utf-8'),
                                            salt.encode('utf-8'),
                                            100000)
        return password_hash.hex(), salt

    def register_user(self, username: str, email: str, password: str) -> Tuple[bool, str]:
        """
        Register a new user.

        Args:
            username: User's chosen username
            email: User's email address
            password: User's password

        Returns:
            tuple: (success, message)
        """
        # Validate input
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"

        if len(password) < 6:
            return False, "Password must be at least 6 characters long"

        if "@" not in email:
            return False, "Please enter a valid email address"

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if username or email already exists
                cursor.execute("""
                    SELECT username, email FROM users 
                    WHERE username = ? OR email = ?
                """, (username, email))

                existing = cursor.fetchone()
                if existing:
                    if existing[0] == username:
                        return False, "Username already exists"
                    else:
                        return False, "Email already registered"

                # Create new user
                user_id = str(uuid.uuid4())
                password_hash, salt = self._hash_password(password)
                full_hash = f"{salt}:{password_hash}"

                cursor.execute("""
                    INSERT INTO users (user_id, username, email, password_hash)
                    VALUES (?, ?, ?, ?)
                """, (user_id, username, email, full_hash))

                conn.commit()
                return True, f"Account created successfully! Welcome, {username}!"

        except Exception as e:
            return False, f"Registration failed: {str(e)}"

    def login_user(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Authenticate user login.

        Args:
            username: Username or email
            password: User's password

        Returns:
            tuple: (success, message, user_data)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Find user by username or email
                cursor.execute("""
                    SELECT user_id, username, email, password_hash, is_active
                    FROM users 
                    WHERE (username = ? OR email = ?) AND is_active = TRUE
                """, (username, username))

                user = cursor.fetchone()
                if not user:
                    return False, "Invalid username/email or password", None

                user_id, db_username, email, stored_hash, is_active = user

                # Verify password
                if ":" in stored_hash:
                    salt, password_hash = stored_hash.split(":", 1)
                    computed_hash, _ = self._hash_password(password, salt)

                    if computed_hash == password_hash:
                        # Update last login
                        cursor.execute("""
                            UPDATE users SET last_login = CURRENT_TIMESTAMP
                            WHERE user_id = ?
                        """, (user_id,))

                        # Create session
                        session_id = self.create_session(user_id)

                        user_data = {
                            "user_id": user_id,
                            "username": db_username,
                            "email": email,
                            "session_id": session_id
                        }

                        conn.commit()
                        return True, f"Welcome back, {db_username}!", user_data

                return False, "Invalid username/email or password", None

        except Exception as e:
            return False, f"Login failed: {str(e)}", None

    def create_session(self, user_id: str, duration_days: int = 30) -> str:
        """Create a new user session."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                session_id = str(uuid.uuid4())
                expires_at = datetime.now() + timedelta(days=duration_days)

                cursor.execute("""
                    INSERT INTO user_sessions (session_id, user_id, expires_at)
                    VALUES (?, ?, ?)
                """, (session_id, user_id, expires_at))

                conn.commit()
                return session_id

        except Exception as e:
            print(f"Session creation error: {e}")
            return ""

    def validate_session(self, session_id: str) -> Optional[Dict]:
        """Validate a user session and return user data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT u.user_id, u.username, u.email, s.expires_at
                    FROM users u
                    JOIN user_sessions s ON u.user_id = s.user_id
                    WHERE s.session_id = ? AND s.is_active = TRUE
                    AND s.expires_at > CURRENT_TIMESTAMP
                """, (session_id,))

                result = cursor.fetchone()
                if result:
                    user_id, username, email, expires_at = result
                    return {
                        "user_id": user_id,
                        "username": username,
                        "email": email,
                        "session_id": session_id,
                        "expires_at": expires_at
                    }

        except Exception as e:
            print(f"Session validation error: {e}")

        return None

    def logout_user(self, session_id: str) -> bool:
        """Logout user by deactivating their session."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE user_sessions 
                    SET is_active = FALSE 
                    WHERE session_id = ?
                """, (session_id,))

                conn.commit()
                return True

        except Exception as e:
            print(f"Logout error: {e}")
            return False

    def save_user_story(self, user_id: str, story_data: str, story_title: str,
                        character_name: str, world_type: str) -> Tuple[bool, str]:
        """Save a story for a specific user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                story_id = str(uuid.uuid4())

                cursor.execute("""
                    INSERT INTO user_stories 
                    (story_id, user_id, story_title, character_name, world_type, story_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (story_id, user_id, story_title, character_name, world_type, story_data))

                conn.commit()
                return True, f"Story '{story_title}' saved successfully!"

        except Exception as e:
            return False, f"Failed to save story: {str(e)}"

    def get_user_stories(self, user_id: str) -> List[Dict]:
        """Get all stories for a specific user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT story_id, story_title, character_name, world_type, 
                           created_at, last_updated
                    FROM user_stories 
                    WHERE user_id = ? AND is_active = TRUE
                    ORDER BY last_updated DESC
                """, (user_id,))

                stories = []
                for row in cursor.fetchall():
                    stories.append({
                        "story_id": row[0],
                        "story_title": row[1],
                        "character_name": row[2],
                        "world_type": row[3],
                        "created_at": row[4],
                        "last_updated": row[5]
                    })

                return stories

        except Exception as e:
            print(f"Error fetching stories: {e}")
            return []

    def load_user_story(self, user_id: str, story_id: str) -> Optional[str]:
        """Load a specific story for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT story_data FROM user_stories 
                    WHERE user_id = ? AND story_id = ? AND is_active = TRUE
                """, (user_id, story_id))

                result = cursor.fetchone()
                return result[0] if result else None

        except Exception as e:
            print(f"Error loading story: {e}")
            return None

    def update_user_story(self, user_id: str, story_id: str, story_data: str) -> bool:
        """Update an existing user story."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE user_stories 
                    SET story_data = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND story_id = ? AND is_active = TRUE
                """, (story_data, user_id, story_id))

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            print(f"Error updating story: {e}")
            return False

    def delete_user_story(self, user_id: str, story_id: str) -> bool:
        """Delete a user story (soft delete)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE user_stories 
                    SET is_active = FALSE 
                    WHERE user_id = ? AND story_id = ? AND is_active = TRUE
                """, (user_id, story_id))

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            print(f"Error deleting story: {e}")
            return False


# Global auth instance
auth = UserAuth()