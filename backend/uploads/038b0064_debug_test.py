
import os
import sqlite3

def test_vulnerability():
    user_input = input("Enter: ")
    os.system("echo " + user_input)
    
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = '" + user_input + "'")
    
    return "Done"
