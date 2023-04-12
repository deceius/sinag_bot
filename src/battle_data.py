
from inspect import currentframe
from io import BytesIO
from typing import Union
import requests
import discord
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from discord.utils import get
from database_clients.GuildDb import GuildDb
from database_clients.UserDb import UserDb
from constants import request_url
from constants import file_path

class BattleData():
    
    async def searchIGN(self, ign: str):
        response = requests.get(f"{ request_url.search_ign }{ign}")
        if response.status_code == 200:
            playerList =  response.json()['players']
            result = None
            kf = 0
            for player in playerList:
                if kf <= player['KillFame'] and ign.lower() == player['Name'].lower():
                    kf = player['KillFame']
                    result = player
            return result
        else:
            return None
        
    
    async def validateIGN(self, ign: str):
        response = requests.get(f"{ request_url.search_ign }{ign}")
        if response.status_code == 200:
            playerList =  response.json()['players']
            result = None
            kf = 0
            for player in playerList:
                if kf <= player['KillFame'] and ign.lower() == player['Name'].lower() and player['GuildId'] in GuildDb().get_guilds():
                    kf = player['KillFame']
                    result = player
            return result
        else:
            return None
           
    async def validate_guild(self, guildId):
        response = requests.get(f"{ request_url.find_guild }{guildId}")
        if response.status_code == 200:
            guild = response.json()
            return guild
        else:
            return None
        
    async def get_guild_members(self, guildId):
        response = requests.get(f"{ request_url.find_guild }{guildId}/members")
        if response.status_code == 200:
            members = response.json()
            return [r['Id'] for r in members]
        else:
            return None
        
    def registerIGN(self, ign: str, user: Union[discord.User, discord.Member], charId: str, guildId: str):
        if not UserDb().user_exists(user.id) and not UserDb().char_exists(charId):
            UserDb().registerUser(ign, user.id, charId, guildId)
            return True
        else:
            return False

    def lookupUser(self, userId):
        user = UserDb().userExistsByUserId(userId)
        if not user is None:
            return user
        else:
            return None
        
    def lookupCharacter(self, charId):
        response = requests.get(f"{ request_url.lookup_char }{charId}")
        if response.status_code == 200:
            return response.json()
        else:
            return None  


    def infoImage(self, characterData, points = 0):
        resultData = characterData
        sigmaProfile = f"https://app.sigmacomputing.com/embed/2Fb3n6osB7MZ0psRKGqR6?albion-server=EAST&name={resultData['Name']}"
        aoProfile = f"https://albiononline.com/en/killboard/player/{resultData['Id']}"
        image = Image.open(file_path.info_kb)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(file_path.font, 13)
        headerFont = ImageFont.truetype(file_path.font, 25)
        bytes = BytesIO()
        
        vertPosition = 25
        draw.text((112, vertPosition), f"{resultData['Name']}",(200,200,200),font=headerFont)
        allianceName = ""
        if resultData['AllianceName']:
            allianceName = f"[{resultData['AllianceName']}] "
        if resultData['GuildName']:
            vertPosition = vertPosition + 30
            draw.text((112, vertPosition), f"{allianceName}{resultData['GuildName']}",(200,200,200),font=font)
            vertPosition = vertPosition + 15
        vertPosition = 139
        draw.text((169, vertPosition),f"{points:,}",(0,0,0),font=font)
        vertPosition = vertPosition + 28
        draw.text((169, vertPosition),f"{resultData['KillFame']:,}",(0,0,0),font=font)
        vertPosition = vertPosition + 28
        draw.text((169, vertPosition),f"{resultData['DeathFame']:,}",(0,0,0),font=font)
        vertPosition = vertPosition + 28
        draw.text((169, vertPosition),f"{resultData['FameRatio']:,}",(0,0,0),font=font)
        image.save(bytes, format="PNG")
        bytes.seek(0)
        dfile = discord.File(bytes, filename="info.png")
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Sigma",style=discord.ButtonStyle.primary,url=sigmaProfile, emoji="<:active:1027795516911779880>"))
        view.add_item(discord.ui.Button(label="AO Profile",style=discord.ButtonStyle.primary,url=aoProfile, emoji="<:might:1027795519218647080>"))
       
        return [dfile, view]
