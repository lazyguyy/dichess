import sqlite3

if __name__=="__main__":
    # create databases for tournament bot
    database = sqlite3.connect("tournament.db")
    cursor = database.cursor()
    cursor.execute("""CREATE TABLE active_channels
                        (server text, channel text)""")
    cursor.execute("""CREATE TABLE tournaments
                        (id int primary key, name text, message_id int, status text, type text)""")
    cursor.execute("""CREATE TABLE games
                        (tournament_id int, round int, white_id text, black_id text, url text)""")
    cursor.execute("""CREATE TABLE participants
                        (tournament_id int, discord_name text)""")
    cursor.execute("""CREATE TABLE players
                        (discord_id text unique, lichess_name text unique)""")
    database.commit()
    database.close()
