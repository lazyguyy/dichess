import discord
import sqlite3

from basic_bot import Basic_bot


class Tournament():
    def __init__(self, tournament_id, message_id):
        # the id of the tournament. there might be multiple tournaments running at the same time (only one can be active and the id will be used to switch between active tournaments)
        self.tournament_name = tournament_name
        # the id of the message where player reactions and the tournament standings will be shared
        self.message_id = message_id

tournament_creation_message = """To play in this tournament, simply register your lichess username with
``dichess register <username>`` first . Then, react with the :brain: emoji.
Start the tournament with ``dichess start {}``."""

class Tournament_bot(Basic_bot):
    def __init__(self, dichess_frame):
        self.name = "tournament_bot"
        self.dichess_frame = dichess_frame
        self.database = sqlite3.connect('tournament.db')
        self.cursor = self.database.cursor()

        previous_id = self.cursor.execute("SELECT max(id) from tournaments").fetchone()[0]
        self.current_tournament_id = 0 if previous_id == None else previous_id[0] + 1

        # read from file
        self.active_channels_per_server = {}
        self.discord_to_lichess = {}
        self.tournaments = {}


        super().__init__()


    def initiate_shutdown(self):
        super().initiate_shutdown()

        self.database.close()

    async def on_command(self, message, content):
        words = content.split(" ")
        guild = message.channel.guild.id
        if words[0] == "init":

            self.active_channels_per_server[guild] = set(words[1:])
            self.cursor.executemany("INSERT INTO active_channels VALUES (?,?)", [(guild, channel) for channel in words[1:]])
            self.database.commit()
            print(self.active_channels_per_server)
            return

        # if a command is received in a channel the bot is not allowed to talk in
        # print(message.channel.name)
        # if guild in self.active_channels_per_server.keys():
        #     print(self.active_channels_per_server[guild])
        # if guild not in self.active_channels_per_server.keys() or message.channel.name not in self.active_channels_per_server[guild]:
        #     return

        # register a new user. We need to know which lichess username belongs to that discord user 
        # so we can ping and scrape results accordingly
        if words[0] == "register":
            lichess = words[1]
            self.discord_to_lichess[message.author.id] = lichess
            self.cursor.execute("INSERT INTO players VALUES (?,?)", (message.author.name, lichess))
            self.database.commit()
            print(f"registered {message.author.name} as {lichess}")
            return

        if words[0] == "create":
            name = content[7:]
            if name.strip() == "":
                name = tournament_id
            message_content = tournament_creation_message.format(self.current_tournament_id)
            embed = discord.Embed(
                title=f"Chess tournament",
                type="rich",
                description=message_content,
                colour=discord.Colour.dark_teal())
            print("Creating a new tournament.")
            tournament_message = await message.channel.send(embed=embed)
            self.cursor.execute("INSERT INTO tournaments VALUES (?,?,?)", (self.current_tournament_id, name, tournament_message.id))
            self.database.commit()
            self.current_tournament_id += 1
