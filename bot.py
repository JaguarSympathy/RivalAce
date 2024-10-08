# *******************************************************
# This file is part of the RivalAce project. Please see the README.md file for information.
#  
# This file and its content can not be copied and/or distributed without the express
# permission of JaguarSympathy.
#
# The project is developed solely and indepedently by JaguarSympathy. All rights are reserved.
# *******************************************************

import discord
from discord import app_commands
from dotenv import load_dotenv
import os
import requests
import json
import datetime

load_dotenv()

# -- CONSTANTS -- #
TOKEN = os.getenv("DISCORD_CLIENT_TOKEN")
STAFF = 1290697193652490241
LOG_CHANNEL = 1290697193652490241
INTELLIGENCE_GROUP_CRITERIA =  ["intelligence","intel","investigation","agency"]

# -- Initialisation -- #
client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client=client)

# -- Functions -- #
async def log(entry) -> None:
    channel = await client.fetch_channel(LOG_CHANNEL)
    await channel.send(f"[{datetime.datetime.now().strftime('%d/%m/%Y')}] - {entry}")

async def background_check(rblxId: int, interaction: discord.Interaction, member: discord.Member):
    profile_data = requests.get(f"https://users.roblox.com/v1/users/{rblxId}").json()
    groups_data = requests.get(f"https://groups.roblox.com/v2/users/{rblxId}/groups/roles").json()["data"]

    embed = discord.Embed(title="Background Check")

    embed.add_field(name="Join Date",value=await Checks.joinDate(profile_data,member))
    embed.add_field(name="Groups",value=await Checks.groups(groups_data,member))

    await interaction.followup.send(embed=embed)

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
    
class Checks():
    async def joinDate(profile_data,member: discord.Member) -> str:
        joindate_datetime = datetime.datetime.strptime(profile_data["created"],"%Y-%m-%dT%H:%M:%S.%fZ")
        joindate = joindate_datetime.strftime("%d/%m/%Y")
        joindate_timedelta = datetime.datetime.now() - joindate_datetime

        await log(f"[BACKGROUND CHECK] - `ROBLOX JOIN DATE` for {member.display_name}: `{joindate} ({joindate_timedelta.days} days)`.")
        return f"{joindate} ({joindate_timedelta.days} days)"

    async def groups(groups_data,member: discord.Member) -> str:
        group_count = 0
        ignored_count = 0

        for group in groups_data:
            with open("groupBlacklist.json","r") as f:
                blacklisted_groups = json.load(f)

                for blacklisted_group_id in blacklisted_groups:
                    if group["group"]["id"] == blacklisted_group_id:
                        await log(f"[BACKGROUND CHECK] - `ROBLOX GROUPS` for {member.display_name}: `IN BLACKLISTED GROUP {blacklisted_group_id}.`")
                        await log(f"[KICK] - Kicked {member.display_name} for `GROUP BLACKLISTED: {blacklisted_group_id}`.")
                        await member.kick(reason=f"GROUP BLACKLISTED: {blacklisted_group_id}")
                        return f"BLACKLISTED GROUP MEMBER: {blacklisted_group_id}"

            if group["role"]["rank"] == 255:
                ignored_count += 1
            else:
                for item in INTELLIGENCE_GROUP_CRITERIA:
                    if item in group["group"]["name"].lower():
                        ignored_count += 1
                        await log(f"[BACKGROUND CHECK] - `ROBLOX GROUPS` for {member.display_name}: `FLAGGED INTELLIGENCE GROUP {group['group']['name']} ({group['group']['id']})`.  ")
                        return f"INTELLIGENCE GROUP MEMBER: {group['group']['id']}"

                group_count += 1             

        await log(f"[BACKGROUND CHECK] - `ROBLOX GROUPS` for {member.display_name}: `{group_count} total groups`. `{ignored_count} ignored groups`.")
        return f"{group_count} total groups. {ignored_count} invalid groups."



# -- Events -- #
@client.event
async def on_ready():
    await tree.sync()

@tree.command(name="background-check",description="Run the background check!")
@app_commands.describe(member="Member to run command on")
async def backgroundCheck(interaction: discord.Interaction, member: discord.Member = None):
    await interaction.response.defer()
    if isinstance(member,discord.Member): # non-self submitted
        staff_role = interaction.guild.get_role(STAFF)
        if staff_role not in interaction.user.roles: # Staff only
            await interaction.followup.send("Access denied! Only Staff can select specific members to background check.")
            return
    else: # default case; username left blank - use display name
        member = interaction.user

    rblxId = await fetch_user_id(member.display_name)
    
    await background_check(rblxId,interaction,member)

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