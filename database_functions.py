import sqlite3


# Execute function
def execute(querry, fetchall = True):
    connection = sqlite3.connect('files.db', check_same_thread=False)
    cursor = connection.cursor()
    cursor.execute(querry)

    if fetchall:
        result = cursor.fetchall()
    else:
        result = cursor.fetchone()
    cursor.close()
    connection.commit()
    connection.close()
    return result


# Creating database
def create_database():
    # Xp database
    try:
        sqliteConnection = sqlite3.connect('files.db')
        cursor = sqliteConnection.cursor()

        query = """create table DB_XP(
                    Id integer primary key autoincrement,
                    User text not null,
                    XP text not null,
                    Level text not null
                    );"""
        cursor.execute(query)

        sqliteConnection.commit()


        result = cursor.fetchall()
        print(result)

        cursor.close()

    except sqlite3.Error as error:
        print('Error occurred - ', error)


    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print('SQLite Connection closed')



    # Streak database
    try:
        sqliteConnection = sqlite3.connect('files.db')
        cursor = sqliteConnection.cursor()

        query = """create table DB_streak2(
                    User text not null,
                    EarlyRising text not null,
                    DeepWork text not null,
                    Meditation text not null,
                    Journal text not null,
                    ColdShower text not null,
                    Gym text not null,
                    ReadingBook text not null
                    );"""

        cursor.execute(query)

        sqliteConnection.commit()


        result = cursor.fetchall()
        print(result)

        cursor.close()

    except sqlite3.Error as error:
        print('Error occurred - ', error)


    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print('SQLite Connection closed')



    # Habits database
    try:
        sqliteConnection = sqlite3.connect('files.db')
        cursor = sqliteConnection.cursor()

        query = '''CREATE TABLE IF NOT EXISTS habits (
                        user_id INTEGER,
                        username TEXT,
                        habit TEXT,
                        date TEXT
                    )'''
        cursor.execute(query)

        sqliteConnection.commit()


        result = cursor.fetchall()
        print(result)

        cursor.close()

    except sqlite3.Error as error:
        print('Error occurred - ', error)


    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print('SQLite Connection closed')



    # Messages database
    try:
        sqliteConnection = sqlite3.connect('files.db')
        cursor = sqliteConnection.cursor()

        query = '''CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY,
                text TEXT
            )
            '''
        cursor.execute(query)

        sqliteConnection.commit()


        result = cursor.fetchall()
        print(result)

        cursor.close()

    except sqlite3.Error as error:
        print('Error occurred - ', error)


    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print('SQLite Connection closed')



    # King of the hill database
    try:
        sqliteConnection = sqlite3.connect('files.db')
        cursor = sqliteConnection.cursor()

        query = '''CREATE TABLE IF NOT EXISTS leaderboard_history (
                        date TEXT,
                        username TEXT,
                        habit TEXT,
                        PRIMARY KEY (date, habit)
                    )'''
        cursor.execute(query)

        sqliteConnection.commit()


        result = cursor.fetchall()
        print(result)

        cursor.close()

    except sqlite3.Error as error:
        print('Error occurred - ', error)


    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print('SQLite Connection closed')



    # Challenges database
    try:
        sqliteConnection = sqlite3.connect('files.db')
        cursor = sqliteConnection.cursor()
        #cursor.execute('DROP TABLE IF EXISTS challenges;')

        query = '''CREATE TABLE challenges (
                        id INTEGER PRIMARY KEY,
                        chat_id INTEGER,
                        user_id,
                        username TEXT,
                        challenge_text TEXT,
                        xp INTEGER,
                        duration INTEGER,
                        done INTEGER DEFAULT 0
                    )'''
        cursor.execute(query)

        sqliteConnection.commit()


        result = cursor.fetchall()
        print(result)

        cursor.close()

    except sqlite3.Error as error:
        print('Error occurred - ', error)


    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print('SQLite Connection closed')


#create_database()
