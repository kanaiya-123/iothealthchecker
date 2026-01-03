import sqlclient

def get_connection():
    return sqlclient.connect(
        host="localhost",
        user="root",
        password="",
        database="Do_Name_Checker",
        charset="utf8mb4",
        cursorclass=sqlclient.cursors.DictCursor
    )
