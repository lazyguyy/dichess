import datetime
import discord
import asyncio
import sys
import random
import os

from tournament_bot import Tournament_bot

class Dichess(discord.Client):

    def __init__(self, subsystems):
        super().__init__()
        self.tasks = 0
        self.name = "dichess"

        self.log(f"booting subystems")
        self.subsystems = [subsystem(self) for subsystem in subsystems]

        for subsystem in self.subsystems:
            subsystem.create_background_tasks()

        self.log(f"all subsystems have been booted")

    def log(self, *args):
        print(f"[{self.name}]: ", end="")
        print(*args)


    async def on_ready(self):
        await client.change_presence(activity=discord.Game(name="dichess is there for you"))
        self.log(f"has been started")

    async def on_message(self, message):
        if message.author == client.user:
            return

        # first, general messages that the bot might interact with

        for subsystem in self.subsystems:
            await subsystem.on_message(message)

        # commands after here

        if not message.content.startswith(self.name):
            return

        content = message.content[8:]
        action = content.split()[0]

        if action == "stop":
            self.log(f"shutting down")

            # make sure each subsystem closes all its background tasks before we halt the bot
            for subsystem in self.subsystems:
                subsystem.initiate_shutdown()

            self.log(f"waiting for all tasks to finish")
            while self.tasks > 0:
                self.log(f"{self.tasks} task(s) remaining")
                await asyncio.sleep(5)
            self.log(f"all tasks have been closed. good bye")
            await self.logout()
            await self.close()

        for subsystem in self.subsystems:
            await subsystem.on_command(message, content)

    async def on_member_update(self, before, after):
        for subsystem in self.subsystems:
            await subsystem.on_member_update(before, after)


with open(os.path.join(sys.path[0], "token"), "r") as f:
    TOKEN = f.read()



client = Dichess([Tournament_bot])

client.run(TOKEN)
