# import socket programming library 
import socket 
  
# import thread module 
from _thread import *
import threading 
import sys

import pymongo
import time
from passlib.context import CryptContext

import pickle

import auction as au

print_lock = threading.Lock() 

user_Func = {"deneme":au.User.addbalance}
item_Func = {}
def threaded(c,user):
    c.send('thread_created'.encode('ascii'))
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
            func = getattr(user,func_Array[0])(*func_Array[1:])
            print(user.name)
            print(user.surname)
            c.send(data)
            
    # connection closed 
    c.close() 
## TCP - IP, Socket Configurations
host = "127.0.0.1"
port = 8008 # arbitrary non-privileged port
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
    while True:
        data = c.recv(1024)
        print("ilk gelen:",data.decode('ascii'))
        user = au.User.getUser(data.decode('ascii'))
        if user is not None:
            try:
                start_new_thread(threaded, (c,user,)) 
            except:
                print("Unable to open thread")
        else:
            time.sleep(2)
            c.send('404'.encode('ascii'))
            newuserinfo = c.recv(1024)
            newuser = pickle.loads(newuserinfo)
            if newuser[1] == 'continue':
                continue
            newuserclass = au.User(newuser[1],newuser[2],newuser[3],newuser[4])
            start_new_thread(threaded, (c,newuserclass,))
            print('New User Created.')
        

s.close()