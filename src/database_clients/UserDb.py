from tinydb import TinyDB, Query
from tinydb.operations import add
from constants import file_path

class UserDb:
    def __init__(self) -> None:
        self.db = TinyDB(f"{ file_path.user_database }")
        self.table = self.db.table('users')
        pass

    def user_exists(self, userId):
        q = Query()
        result = self.table.get(q.userId == userId)
        return result
    
    def char_exists(self, charId):
        q = Query()
        result = self.table.get(q.charId == charId)
        return result

    def get_all_member_ids(self):
        result = self.table.all()
        return result

    def userExistsByUserId(self, userId):
        q = Query()
        result = self.table.get(q.userId == userId)
        return result
    
    def get_member_data(self, userId):
        q = Query()
        result = self.table.get(q.userId == userId)
        return result
    
    def get_by_guild_id(self, guild_id):
        q = Query()
        result = self.table.search(q.guildId == guild_id)
        return result

    def registerUser(self, ign, userId, charId, guildId):
        self.table.insert({ 'ign': ign, 'userId': userId, 'charId': charId, 'guildId': guildId, 'cta': 0 })

    def remove_user(self, userId):
        q = Query()
        self.table.remove(q.userId == userId)

    def give_cta(self, userId, points):
        q = Query()
        self.table.update(add('cta', points), q.userId == userId)
