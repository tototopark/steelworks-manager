import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

conn = sqlite3.connect('f:/pe/public_html/steelworks-manager/data/steelworks.db')
cur = conn.cursor()

hashed_pw = pwd_context.hash("12345678")

cur.execute("""
INSERT INTO tb_login (login, password, firstname, surname, role, right_level, is_active, admin_validation, avatar, date_creation) 
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
""", ("admin", hashed_pw, "System", "Admin", "Admin", 10, 1, 1, "avatar.png"))

conn.commit()
print("Admin user inserted successfully.")
conn.close()
