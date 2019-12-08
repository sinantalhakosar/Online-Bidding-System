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
import json

import auction as au

print_lock = threading.Lock()


def watchhelper(pipeline, optype, serverAddressPort):
    if optype == "user":
        try:
            with item_collection.watch(pipeline)as stream:
                for change in stream:
                    returnstring = ""
                    returnstring += "There is an update in your watch list:\n"
                    returnstring += str(change["fullDocument"])
                    print("furkan")
                    UDPClientSocket.sendto(pickle.dumps(
                        {1: 'watch', 2: returnstring}), serverAddressPort)
        except pymongo.errors.PyMongoError:
            print("Failure during ChangeStream initialization.")
    else:
        try:
            with item_collection.watch(pipeline)as stream:
                for change in stream:
                    print(change)
        except pymongo.errors.PyMongoError:
            print("Failure during ChangeStream initialization.")


def threaded(c, user, address):
    serverAddressPort = ("127.0.0.1", address)
    c.send(pickle.dumps({1: 'thread_created', 2: address}))
    while True:
        # data received from client
        data = c.recv(1024)
        if not data:
            print('Bye')

            # lock released on exit
            break
        else:
            func_Name = data.decode('ascii')
            func_Array = func_Name.split(" ")
            if func_Array[0] == 'user':
                if func_Array[1] == 'watch':
                    if len(func_Array) == 2:
                        start_new_thread(watchhelper, (au.User.watch(), "user", serverAddressPort,))
                    else:
                        start_new_thread(watchhelper, (au.User.watch(func_Array[2]), "user", serverAddressPort,))
                else:
                    func = getattr(user, func_Array[1])(*func_Array[2:])
                    c.send(pickle.dumps(func))
            elif func_Array[0] == 'item':
                if func_Array[1] == 'add':
                    au.SellItem(user.email, func_Array[2], func_Array[3],
                                func_Array[4], func_Array[5], func_Array[6], func_Array[7])
                    c.send(pickle.dumps({1: 'New item added'}))
                elif func_Array[1] == 'watch':
                    itemclass = au.SellItem.getitem(func_Array[2], func_Array[3])
                    start_new_thread(watchhelper, (itemclass.watch(), "item", serverAddressPort,))
                else:
                    owner = func_Array[1]
                    title = func_Array[2]
                    try:
                        itemclass = au.SellItem.getitem(owner, title)
                        print(itemclass.title)
                        print(func_Array[3])
                        print(func_Array[4:])
                        itemfunc = getattr(itemclass, func_Array[3])(*func_Array[4:])
                        c.send(pickle.dumps(itemfunc))
                    except:
                        c.send(pickle.dumps({1: 'Item not exists'}))
    # connection closed
    c.close()


# TCP - IP, Socket Configurations
host = "127.0.0.1"
port = 8035  # arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
print("Socket created")
try:
    s.bind((host, port))
    s.listen(5)
    print("Socket now listening")
except:
    print("Bind failed. Error : " + str(sys.exc_info()))
    sys.exit()
# infinite loop- do not reset for every requests

# MongoDB Configurations
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    default="pbkdf2_sha256",
    pbkdf2_sha256__default_rounds=30000
)
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client.get_database("bidding")
user_collection = db.get_collection("users")
item_collection = db.get_collection("items")

# Capturing first data and passing it to the threads
while True:
    c, address = s.accept()
    ip, port = str(address[0]), str(address[1])
    print("Connected with " + ip + ":" + port)
    while True:
        data = c.recv(1024)
        user = au.User.getUser(data.decode('ascii'))
        if user is not None:
            try:
                start_new_thread(threaded, (c, user, address[1],))
                break
            except:
                print("Unable to open thread")
        else:
            time.sleep(2)
            c.send(pickle.dumps({1: '404'}))
            newuserinfo = c.recv(1024)
            newuser = pickle.loads(newuserinfo)
            if newuser[1] == 'continue':
                continue
            newuserclass = au.User(
                newuser[1], newuser[2], newuser[3], newuser[4])
            start_new_thread(threaded, (c, newuserclass,address[1],))
            break


s.close()
