import socket
import sys

import auction as au

import pymongo
import time
from passlib.context import CryptContext
import pickle
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
port = 8008
try:
   soc.connect((host, port))
except:
   print("Connection Error")
   sys.exit()
print("Please enter 'quit' to exit")
is_loggedin = False
while True:
    if not is_loggedin:
        message = input("email:")
        if message == 'quit':
            break
    soc.send(message.encode("ascii"))
    data = soc.recv(1024)
    if data.decode('ascii') == 'thread_created':
        is_loggedin = True
        print('User Login Successfull')
    elif data.decode('ascii') == '404':
        print('User not found.')
        ans = input('Do you want to register? (y/n):')
        if ans == 'y':
            newmail = input('email:')
            newname  = input('name:')
            newsurname = input('surname:')
            newpass = input('password:')
            print('Registering...')
            registerinfo = {1:newmail,2:newname,3:newsurname,4:newpass}
            soc.send(pickle.dumps(registerinfo))
        else:
            soc.send(pickle.dumps({1:"continue"})) 
    else:
        print(data.decode('ascii'))
    if is_loggedin:
        message = input("action:")
        if message == 'quit':
            break
soc.send(b'--quit--')
