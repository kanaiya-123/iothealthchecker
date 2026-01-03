import MySQLdb

def get_db_connection():
    return MySQLdb.connect(
        host="localhost",
        user="root",
        passwd="",
        db="Do_Name_Checker",
        charset='utf8',
        use_unicode=True
    )