from pymongo import MongoClient

# Connexion à MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Choix d'une base de données de test
db = client.test  

# Affiche les collections existantes
print("Collections existantes :", db.list_collection_names())
