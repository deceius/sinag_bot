

import csv

import discord
from constants import file_path
from database_clients.GuildDb import GuildDb
from database_clients.UserDb import UserDb


class cta_points():

    def __init__(self) -> None:
        self.header = ['ign', 'points']
        self.top = 15
        pass


    def generate_csv_file(self):
        with open(f'{ file_path.cta_points }', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.header)
            users = UserDb().get_all_member_ids()
            for user in users:
                writer.writerow([ user['ign'], user['cta']])
        return discord.File(file_path.cta_points)

    def generate_top_cta(self, role: discord.Role, isDescending = True):
        guildTop15 = ""
        desc = "Bottom"
        guildData = GuildDb().get_by_role_id(role.id)
        if not guildData:
            return None
        guildMembers = UserDb().get_by_guild_id(guildData['guildId'])
        if isDescending:
            desc = "Top"
        guildMembers.sort(key=self.extract_cta, reverse=isDescending)
        
        counter = 0
        for member in guildMembers:
            if counter == 15:
                continue
            guildTop15 += (f"{ member['cta']}: {member['ign']}\n")
            counter += 1

        embed = discord.Embed(title=f"{desc} 15 CTA Points from {role.name}", description=f"{guildTop15}", color=0x00ff00)
        return embed


    def extract_cta(self, json):
        try:
            # Also convert to int since update_time will be string.  When comparing
            # strings, "10" is smaller than "2".
            return int(json['cta'])
        except KeyError:
            return 0