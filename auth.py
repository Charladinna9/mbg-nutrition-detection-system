import bcrypt
from db import get_connection
import streamlit as st

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def login_user(username: str, password: str):
    conn = get_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password(password, user['password_hash']):
            return user
        return None
    except Exception as e:
        st.error(f"Error saat login: {e}")
        return None

def register_user(username: str, email: str, password: str, role: str = 'user', nama_lengkap: str = ""):
    conn = get_connection()
    if conn is None:
        return False
    
    try:
        hashed = hash_password(password)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, nama_lengkap)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, email, hashed, role, nama_lengkap))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saat register: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()