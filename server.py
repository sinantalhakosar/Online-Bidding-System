# import socket programming library 
import socket 
  
# import thread module 
from _thread import *
import threading 
import sys

import pymongo
import time
from passlib.context import CryptContext

import auction as au

print_lock = threading.Lock() 

user_Func = {"deneme":au.User.addbalance}
item_Func = {}
def threaded(c,user):
    try:
        print("mail:",user["email"])
        user_Obj = au.User(user["email"],user["name"],user["surname"],user["password"],True)
    except:
        print("Error creating User Object")
    c.send('200'.encode('ascii'))
    while True: 
        print("--------")
        # data received from client 
        data = c.recv(1024) 
        if not data: 
            print('Bye') 
              
            # lock released on exit 
            break
        else:
            func_Name = data.decode('ascii')
            func_Array = func_Name.split(" ")
            func = getattr(user_Obj,func_Array[0])(*func_Array[1:])
            print(user_Obj.name)
            print(user_Obj.surname)
            c.send(data)
            
    # connection closed 
    c.close() 
## TCP - IP, Socket Configurations
host = "127.0.0.1"
port = 8007 # arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Socket created")
try:
   s.bind((host, port)) 
   s.listen(5) 
   print("Socket now listening")
except:
   print("Bind failed. Error : " + str(sys.exc_info()))
   sys.exit()
# infinite loop- do not reset for every requests

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

## Capturing first data and passing it to the threads
while True:
    print("sadsads")
    c, address = s.accept()
    ip, port = str(address[0]), str(address[1])
    print("Connected with " + ip + ":" + port)
    data = c.recv(1024)
    print("ilk gelen:",data.decode('ascii'))
    user = user_collection.find_one({"email": data.decode('ascii')})
    if user is not None:
        try:
            start_new_thread(threaded, (c,user,)) 
        except:
            print("Unable to open thread")
    else:
        print('User does not exist. Registering...')
        time.sleep(2)
        new_Mail = data.decode('ascii')
        new_Name = input('name:')
        new_Surname = input('surname:')
        new_Password = input('surname:')
        au.User(new_Mail,new_Name,new_Surname,new_Password)
        start_new_thread(threaded, (c,user_collection.find_one({"email": data.decode('ascii')}),))
        print('New User Created.')
        

s.close()