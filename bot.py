import discord
from discord import app_commands
from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

# -- CONSTANTS -- #
TOKEN = os.getenv("DISCORD_CLIENT_TOKEN")
STAFF = 1146564800797749350 # temporary, Apollo Staff role
LOG_CHANNEL = 1291478810293698615 # temporary, Apollo development channel

# -- Initialisation -- #
client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client=client)

# -- Functions -- #
async def log(entry) -> None:
    channel = await client.fetch_channel(LOG_CHANNEL)
    await channel.send(f"{entry}")

async def background_check(rblxId: int, interaction: discord.Interaction):
    profile_data = requests.get(f"https://users.roblox.com/v1/users/{rblxId}").json()
    groups_data = requests.get(f"https://groups.roblox.com/v2/users/{rblxId}/groups/roles").json()["data"]

    

async def fetch_user_id(username: str) -> int:
    response = requests.post("https://users.roblox.com/v1/usernames/users",json={"usernames": [username]})
    data = response.json()
    if response.status_code == 200 and data["data"]:
        rblxId = data["data"][0]["id"]
        await log(f"[PROFILE] - User ID for {username} retrieved. `{rblxId}`")
        return rblxId
    else:
        await log(f"[PROFILE] - Unable to fetch user ID for `{username}`. Error code `{response.status_code}`.")
        raise Exception(f"Cannot fetch user ID for {username} : Error Code {response.status_code}")
    
    
# -- Events -- #
@client.event
async def on_ready():
    await tree.sync()

@tree.command(name="background-check",description="Run the background check!")
@app_commands.describe(username="Username to run command on")
async def backgroundCheck(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    if isinstance(username,str): # non-self submitted
        staff_role = interaction.guild.get_role(STAFF)
        if staff_role in interaction.user.roles: # Staff only
            rblxId = await fetch_user_id(username)
        else:
            await interaction.followup.send("Access denied! Only Staff can select specific members to background check.")
    else: # default case; username left blank - use display name
        rblxId = await fetch_user_id(interaction.user.display_name)
    
    await background_check(rblxId,interaction)

    await interaction.followup.send("Submitted background check.")

@tree.command(name="blacklist-group",description="Blacklist a group")
@app_commands.describe(group="Group ID to blacklist",name="Group name")
async def blacklistGroup(interaction: discord.Interaction, group: int, name: str):
    staff_role = interaction.guild.get_role(STAFF)
    if staff_role in interaction.user.roles:
        with open("groupBlacklist.json","r") as f:
            groupBlacklists = json.load(f)
        
        for entry in groupBlacklists:
            if int(entry) == group:
                await interaction.response.send_message("Blacklist already submitted!")
                return
        
        groupBlacklists[group] = name
        await log(f"[GROUP BLACKLIST] - {name} ({group}) blacklisted by {interaction.user.display_name}.")
        await interaction.response.send_message("Blacklist submitted.")

        with open("groupBlacklist.json","w") as f:
            json.dump(groupBlacklists,f)


client.run(TOKEN)