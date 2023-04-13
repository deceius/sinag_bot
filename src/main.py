
from datetime import datetime
from battle_data import BattleData
import discord
import os
from dotenv import load_dotenv
from discord import app_commands
from discord.utils import get
from discord.ext import tasks
from constants import keywords
from constants import file_path
import logging
from cta_points import cta_points
from database_clients.GuildDb import GuildDb
from database_clients.UserDb import UserDb

load_dotenv()

guilds = []

serverIds = str(os.getenv('SERVER_IDS')).split(',')
activity = discord.Activity(type=discord.ActivityType.listening, name=f"{ keywords.listening_activity }")

logging.basicConfig(filename=f"{ file_path.logs }", level=logging.INFO, format="%(asctime)s %(message)s")

for serverId in serverIds:
    guilds.append(discord.Object(id = serverId))


class PlumaClient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.all()
        intents.message_content = True
        super().__init__(intents=intents, activity=activity)
        self.synced = False    
    
    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            for guild in guilds:
                print("`Bot`: Commands synced to server")
                try:            
                    await tree.sync(guild = guild)
                except Exception as e:
                    print(f"`Bot` Error: { e }")
            self.synced = True

    async def setup_hook(self) -> None:
        self.purge_perms.start()
        pass

    def validate_registration_channel(self, channel_id):
        return channel_id == 1095615035600023623
    
    def validate_botspam_channel(self, channel_id):
        return channel_id == 1083981576016248842

    @tasks.loop(minutes = 300)
    async def purge_perms(self):
        sinagServer = self.get_guild(1067373452618637402)
        channel = await sinagServer.fetch_channel(1087546048714645636)
        with open(f"{ file_path.logs }", 'w'):
            pass
        logging.info("`Purge`: Task Started.")
        guildData = GuildDb().get_guild_data()
        for guild in guildData:
            guildRole = get(sinagServer.roles, id = guild['roleId'])
            logging.info(f"`Purge`: Role { guildRole.name } has {len(guildRole.members)} members.")
            for member in guildRole.members:
                memberData = UserDb().get_member_data(member.id)
                if not memberData:
                    logging.info(f"`Purge`: Member { member.display_name } is not registered... Purging perms...")
                    await self.remove_perms(member.id, guild['roleId'], True)
                else:
                    charData = battle_data.lookupCharacter(memberData['charId'])
                    logging.info(f"`Purge`: Checking Member { charData['Name'] } [{ charData['GuildName']}]...")
                    if not charData['GuildId'] in GuildDb().get_guilds():
                        logging.info(f"`Purge`: Member { member['userId'] } is not found in-game as a guild member. Purging perms...")
                        await self.remove_perms(memberData['userId'], guild['roleId'], True)
                    else:
                        logging.info(f"`Purge`: Member { charData['Name'] } is a guild member in-game.")
        await channel.send(file=discord.File(file_path.logs))


    @purge_perms.before_loop
    async def before_purge_perms(self):
        await self.wait_until_ready()

    async def remove_perms(self, userId, roleId, enabled = True):
        if enabled:
            UserDb().remove_user(userId)
            sinagServer = self.get_guild(1067373452618637402)
            sinagMember = sinagServer.get_member(userId)
            if sinagMember:
                guildRole = get(sinagServer.roles, id = roleId)
                await sinagMember.remove_roles(guildRole)
        else:
            logging.info(f"**** `Purge`: Purge not enabled. This is for validation only.")

battle_data = BattleData()
client = PlumaClient() 
tree = app_commands.CommandTree(client)

# wait until the bot logs in 

@tree.command(name="add_guild", description="[Admin / Council Command] Add a guild in the database with its corresponding role.", guilds = guilds)
@app_commands.checks.has_any_role("Admin", "Council")
async def add_guild(interaction: discord.Interaction, guild_id: str, guild_role: discord.Role):
    await interaction.response.defer(ephemeral = True)
    guild_data = await battle_data.validate_guild(guild_id)
    if guild_data:
        GuildDb().add_guild(guildId = guild_id, roleId = guild_role.id)
        await interaction.followup.send(f"`{guild_data['Name']}` has been bound to {guild_role.mention}.")

@tree.command(name="remove_guild", description="[Admin / Council Command] Remove a guild in the database with its corresponding role.", guilds = guilds)
@app_commands.checks.has_any_role("Admin", "Council")
async def remove_guild(interaction: discord.Interaction, guild_role: discord.Role):
    await interaction.response.defer(ephemeral = True)
    GuildDb().remove_guild(roleId = guild_role.id)
    await interaction.followup.send(f"{guild_role.mention} has been removed.")
        
 
@tree.command(name = "register", description = "Bind your SINAG / LAKAN character to your discord.", guilds = guilds)
async def register(interaction: discord.Interaction, ign: str):
    await interaction.response.defer()
    if not client.validate_registration_channel(interaction.channel_id):
        await interaction.followup.send(f"`/register` command only works on <#1095615035600023623> channel.")
        return
    characterData = await battle_data.validateIGN(ign)
    if characterData:
        successRegistered = battle_data.registerIGN(ign, interaction.user, characterData['Id'], characterData['GuildId'])
        if successRegistered:
            guildRole = get(interaction.guild.roles, id = GuildDb().get_guild_role(characterData['GuildId'])['roleId'])
            applicantRole = get(interaction.guild.roles, id = 1084904105203466312)
            await interaction.user.add_roles(guildRole)
            await interaction.user.remove_roles(applicantRole)
            characterData = battle_data.lookupCharacter(characterData['Id'])
            img = battle_data.infoImage(characterData)
            await interaction.followup.send(content=f"{interaction.user.mention} is now bound to `{ characterData['Name'] }`. Guild: `{ characterData['GuildName'] }`", file = img[0], view = img[1])
 
        else:
            await interaction.followup.send(f"Characters / Accounts entered are already bound.")
    else:
        await interaction.followup.send(f"Albion character was not found in the guild.")


@tree.command(name = "unbind", description = "[Admin / Council Command] Unbind your SINAG / LAKAN character to your discord.", guilds = guilds)
@app_commands.checks.has_any_role("Admin", "Council")
async def register(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer()
    
    characterData = battle_data.lookupUser(member.id)
    if characterData:
        await client.remove_perms(member.id, characterData['guildId'])
        await interaction.followup.send(f"Characters / Accounts entered are already bound.")
    else:
        await interaction.followup.send(f"Albion character was not found in the guild.")


@tree.command(name = "kb", description = "View K/D stats of a member.", guilds = guilds)
async def register(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer()
    if not client.validate_botspam_channel(interaction.channel_id):
        await interaction.followup.send(f"`/kb` command only works on <#1083981576016248842> channel.")
        return
    
    userData = battle_data.lookupUser(member.id)
    if userData:
        characterData = battle_data.lookupCharacter(userData['charId'])
        img = battle_data.infoImage(characterData, userData['cta'])
        await interaction.followup.send(file = img[0], view = img[1])
    else:
        await interaction.followup.send(f"Albion character was not found in the guild.")

@tree.command(name = "lookup", description = "[Admin / Council Command] View K/D stats of an IGN.", guilds = guilds)
@app_commands.checks.has_any_role("Admin", "Council")
async def register(interaction: discord.Interaction, ign: str):
    await interaction.response.defer(ephemeral=True)
    characterData = await battle_data.searchIGN(ign)
    print(characterData)
    if characterData:
        img = battle_data.infoImage(characterData)
        await interaction.followup.send(file = img[0], view = img[1])
    else:
        await interaction.followup.send(f"Albion character was not found.")

@tree.command(name = "give_points", description = "[Admin / Council Command] Give CTA Points to a member.", guilds = guilds)
@app_commands.checks.has_any_role("Admin", "Council")
async def register(interaction: discord.Interaction, member: discord.Member, points: int):
    await interaction.response.defer(ephemeral=True)
    userData = battle_data.lookupUser(member.id)
    if userData:
        UserDb().give_cta(userData['userId'], points)
        await interaction.followup.send(f"{points} CTA Points are given to {member.mention}")
    else:
        await interaction.followup.send(f"Albion character was not found in the guild.")

@tree.command(name = "give_role_points", description = "[Admin / Council Command] Give CTA Points to role members.", guilds = guilds)
@app_commands.checks.has_any_role("Admin", "Council")
async def register(interaction: discord.Interaction, role: discord.Role, points: int):
    await interaction.response.defer(ephemeral=True)
    message = ""
    for member in role.members:
        userData = battle_data.lookupUser(member.id)
        if userData:
            UserDb().give_cta(userData['userId'], points)
            message += f"{points} CTA Points are given to {member.mention}\n"
        else:
            message += f"{member.mention}'s Albion character was not registered.\n"
    await interaction.followup.send(message)

@tree.command(name = "fetch_cta_points", description = "[Admin / Council Command] View CTA Points Leaderboard.", guilds = guilds)
@app_commands.checks.has_any_role("Admin", "Council")
async def fetch_cta_points(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    csv_file = cta_points().generate_csv_file()
    await interaction.followup.send(file=csv_file)
        
@tree.command(name = "bottom_cta", description = "[Admin / Council Command] View Bottom 15 CTA Point Leaderboard", guilds = guilds)
@app_commands.checks.has_any_role("Admin", "Council")
async def bottom_cta(interaction: discord.Interaction, guild_role: discord.Role):
    await interaction.response.defer()
    cta = cta_points().generate_top_cta(guild_role, False)
    if cta:
        await interaction.followup.send(embed=cta) 
    else:
        await interaction.followup.send(f"Guild Role not setup.")


@tree.command(name = "top_cta", description = "[Admin / Council Command] View Bottom 15 CTA Point Leaderboard", guilds = guilds)
@app_commands.checks.has_any_role("Admin", "Council")
async def top_cta(interaction: discord.Interaction, guild_role: discord.Role):
    await interaction.response.defer()
    cta = cta_points().generate_top_cta(guild_role)
    if cta:
        await interaction.followup.send(embed=cta) 
    else:
        await interaction.followup.send(f"Guild Role not setup.")

token = str(os.getenv("BOT_TOKEN"))
client.run(token)
