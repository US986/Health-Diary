import pymysql

def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='ZSD_voin123',
        database='health_diary',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.Cursor
    )