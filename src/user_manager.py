import json
from src.config import Config

class AuthManager:
    def __init__(self, users_file: str = None):
        target_file = users_file or getattr(Config, "USERS_FILE", "users.json")
        with open(target_file, 'r', encoding='utf-8') as f:
            self.users = {u["user_id"]: u for u in json.load(f)}

    def login(self, user_id: str) -> dict:
        if user_id in self.users:
            user = self.users[user_id]
            print(f"[Auth] Logged in successfully: {user['name']} | Dept: {user['dept']} | Level: {user['role_level']}")
            return user
        else:
            raise ValueError("[!] User ID not exist!")