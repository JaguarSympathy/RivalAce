import discord
from discord import app_commands
from dotenv import load_dotenv
import os

load_dotenv()

# -- CONSTANTS -- #
TOKEN = os.getenv("DISCORD_CLIENT_TOKEN")

# -- Initialisation -- #
client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client=client)

# -- Events -- #
@client.event
async def on_ready():
    await tree.sync()

client.run(TOKEN)