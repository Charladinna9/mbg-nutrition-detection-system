import mysql.connector
from mysql.connector import Error
import streamlit as st

def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",           # Kosongkan jika belum diubah
            database="mbg_db"
        )
        return conn
    except Error as e:
        st.error(f"❌ Gagal koneksi ke MySQL: {e}")
        return None