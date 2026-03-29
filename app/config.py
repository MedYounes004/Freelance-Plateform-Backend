from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = "mongodb://localhost:27017/freelance"
    JWT_SECRET_KEY = "super_secret_key_change_in_production"
    JWT_ACCESS_TOKEN_EXPIRES = False