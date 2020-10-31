import asyncio
import discord

class Basic_bot:
    def __init__(self):
        print(f"[{self.name}]: is ready")

    def create_background_tasks(self):
        pass

    def initiate_shutdown(self):
        print(f"[{self.name}]: preparing for shutdown")


    # define the bots behaviour on specific commands
    async def on_command(self, message, content):
        pass

    # define the bots behaviour on general messages
    async def on_message(self, message):
        pass

    async def on_member_update(self, before, after):
        pass
