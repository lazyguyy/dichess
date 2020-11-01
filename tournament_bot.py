import discord
import sqlite3

from basic_bot import Basic_bot
from collections import defaultdict


class Tournament():
    def __init__(self, t_id, name, m_id, status):
        self.name = name
        # the id of the tournament. there might be multiple tournaments running at the same time (only one can be active and the id will be used to switch between active tournaments)
        self.t_id = t_id
        # the id of the message where player reactions and the tournament standings will be shared
        self.m_id = m_id
        self.status = status
        # only tournament type thats currently supported
        self.type = "round robin"

    def start(self, players):
        self.players = players
        if len(self.players) % 2 != 0:
            self.players.append(None)
        self.rounds = len(players) - 1
        self.results = [[] * len(players)]

    # generates the round robin pairing for the specified round
    def rr_pairing(rnd):
        players = self.players[rnd:]


tournament_creation_message = """React with  :brain:  to participate in this tournament.
Link your lichess and discord account with ``dichess link <username>``. 
Start the tournament with ``dichess start {}``."""

class Tournament_bot(Basic_bot):
    def __init__(self, dichess_frame):
        self.name = "tournament_bot"
        self.dichess_frame = dichess_frame
        self.database = sqlite3.connect('tournament.db')
        self.cursor = self.database.cursor()

        previous_id = self.database.execute("SELECT max(id) from tournaments").fetchone()[0]
        self.current_t_id = 0 if previous_id == None else previous_id[0] + 1

        # read from file
        self.active_channels_per_server = defaultdict(set)
        self.discord_to_lichess = {}
        self.tournaments = {}

        super().__init__()


    def read_from_database(self):
        # read active channels
        for server, channel in self.database.execute("SELECT * FROM active_channels GROUP BY server"):
            self.active_channels_per_server[server].add(channel)

        # read discord / lichess aliases
        for d_name, l_name in self.database.execute("SELECT * FROM players"):
            self.discord_to_lichess[d_name] = l_name

        # read tournaments

        # not yet started
        for t_id, name, m_id, status in self.database.execute("SELECT * FROM tournaments WHERE status=created"):
            tournament = Tournament(t_id, name, m_id, status)
            tournaments[t_id] = tournament


    def initiate_shutdown(self):
        super().initiate_shutdown()

        self.database.close()

    async def on_command(self, message, content):
        words = content.split(" ")
        guild = message.channel.guild.id
        if words[0] == "init":

            self.active_channels_per_server[guild].add(message.channel.id)
            self.database.execute("INSERT INTO active_channels VALUES (?,?)", (guild, message.channel.id))
            self.database.commit()
            return

        # if a command is received in a channel the bot is not allowed to talk in
        # print(message.channel.name)
        # if guild in self.active_channels_per_server.keys():
        #     print(self.active_channels_per_server[guild])
        # if guild not in self.active_channels_per_server.keys() or message.channel.name not in self.active_channels_per_server[guild]:
        #     return

        # link a new user. We need to know which lichess username belongs to that discord user 
        # so we can ping and scrape results accordingly
        if words[0] == "link":
            lichess = words[1]
            if (message.author.id in self.discord_to_lichess.keys()):
                self.database.execute("UPDATE players SET lichess_name=? WHERE discord_id=?", (lichess, message.author.id))
            else:   
                self.database.execute("INSERT INTO players VALUES (?,?)", (message.author.id, lichess))
            self.discord_to_lichess[message.author.id] = lichess
            self.database.commit()
            print(f"linked {message.author.name} and {lichess}")
            return

        if words[0] == "create":
            name = content[7:]
            if name.strip() == "":
                name = "Chess tournament #" + (self.current_t_id + 1)

            message_content = tournament_creation_message.format(self.current_t_id)
            embed = discord.Embed(
                title=name,
                type="rich",
                description=message_content,
                colour=discord.Colour.dark_teal())
            print("Creating a new tournament.")
            tournament_message = await message.channel.send(embed=embed)
            tournament = Tournament(self.current_t_id, name, tournament_message.id, "created")
            self.database.execute("INSERT INTO tournaments VALUES (?,?,?,?,?)", (self.current_t_id, name, tournament_message.id, "created", "round robin"))
            self.database.commit()
            self.current_t_id += 1
