from tinydb import TinyDB, Query
from tinydb.operations import increment
from constants import file_path

class GuildDb:

    def __init__(self) -> None:
        self.db = TinyDB(f"{ file_path.guild_database }")
        self.table = self.db.table('guilds')
        pass

    def add_guild(self, guildId, roleId):
        self.table.insert({'guildId' : guildId, 'roleId': roleId })

    def get_guilds(self):
        guilds = self.table.all()
        return [str(guild.get('guildId')) for guild in guilds]
    
    def get_guild_data(self):
        return self.table.all()
    
    def get_guild_role(self, guild_id):
        q = Query()
        result = self.table.get(q.guildId == guild_id)
        return result
    
    def get_by_role_id(self, role_id):
        q = Query()
        result = self.table.get(q.roleId == role_id)
        return result

    def remove_guild(self, roleId):
        q = Query()
        self.table.remove(q.roleId == roleId)
