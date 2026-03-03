import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = "mongodb+srv://admin:admin123@cluster0.mvut6ch.mongodb.net/freelancehub?retryWrites=true&w=majority&appName=Cluster0"
    JWT_SECRET_KEY = "super_secret_key_change_in_production"
    JWT_ACCESS_TOKEN_EXPIRES = False