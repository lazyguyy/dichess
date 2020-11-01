import sqlite3

if __name__=="__main__":
    # create databases for tournament bot
    database = sqlite3.connect("tournament.db")
    cursor = database.cursor()
    cursor.execute("""CREATE TABLE active_channels
                        (server text, channel text)""")
    cursor.execute("""CREATE TABLE tournaments
                        (id int primary key, name text, message_id int)""")
    cursor.execute("""CREATE TABLE players
                        (discord_name text unique, lichess_name text unique)""")
    database.commit()
    database.close()
