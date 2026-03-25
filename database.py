import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",              # your MySQL username
            password="Rahithya@123",  # your MySQL password
            database="notesdb"
        )

        if connection.is_connected():
            return connection

    except Error as e:
        print("Error while connecting to MySQL:", e)
        return None