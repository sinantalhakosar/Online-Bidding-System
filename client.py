import socket
import sys

import auction as au

import pymongo
import time
from passlib.context import CryptContext
## MongoDB Configurations
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    default="pbkdf2_sha256",
    pbkdf2_sha256__default_rounds=30000
)
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client.get_database("bidding")
user_collection = db.get_collection("users")
item_collection = db.get_collection("items")


soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = "127.0.0.1"
port = 8007
try:
   soc.connect((host, port))
except:
   print("Connection Error")
   sys.exit()
print("Please enter 'quit' to exit")
message = input("email:")
while message != 'quit':
    soc.send(message.encode("ascii"))
    data = soc.recv(1024)
    if data.decode('ascii') == '200':
        print('User Login Successfull')
    else:
        print(data.decode('ascii'))
    message = input("action:")
soc.send(b'--quit--')
