import random
import pymongo
import time
from passlib.context import CryptContext
import _thread

class User:
    # A new user is created. User is in not verified state. User is send an email with verification number.
    def __init__(self, email, name, surname, password, bring=False):
        self.email = email
        self.name = name
        self.surname = surname
        self.password = password
        self.is_verified = False
        self.verification_code = name+email
        self.balance = 0
        self.reservedbalance = 0
        self.active = False
        if bring == False:
            usertosave = self.__dict__
            usertosave["password"] = encrypt_password(usertosave["password"])
            user_collection.insert_one(usertosave)
            print("User is created but not verified")

    # Static method. Verification number is checked agains stored one and user is enabled.
    @staticmethod
    def verify(email, verification_number):
        user = user_collection.find_one({"email": email})
        if(user):
            if (user["verification_code"] == verification_number):
                user_collection.update_one(
                    {"email": email}, {"$set": {"is_verified": True}})
                return {1:"Verification is ok"}
            else:
                return {1:"Verification code is wrong"}
        else:
                return {1:"User not found."}
    @staticmethod
    def getUser(email):
        user = user_collection.find_one({"email": email})
        if(user):
            authuser = User(user["email"], user["name"],
                            user["surname"], user["password"], True)
            authuser.balance = user["balance"]
            authuser.is_verified = user["is_verified"]
            authuser.reservedbalance = user["reservedbalance"]
            authuser.active = user["active"]
            return authuser
        else:
            print("User not found.")

    # User password is changed. If forgotten, oldpassword is set as None and a reminder with a uniq temporary password is sent. Next call will be with temporary password as oldpassword for changing the password.

    def changepassword(self, newpassword, oldpassword=None):
        if oldpassword is None:
            self.password = self.email + str(time.time())
            return {1:"Your password have been resetted your new password is {0}".format(
                self.password)}
        self.password = newpassword
        user_collection.update_one(
            {"email": self.email}, {"$set": {"password": encrypt_password(self.password)}})
        return {1:"Password change is succesful"}

    # Get item list of the user given as parameter. The state is either of all, onhold, active, sold
    def listitems(self, user, itemtype=None, state='all'):
        items = item_collection.find({"owner": user})
        itemlist = list(items)
        result = []
        if (not len(itemlist)):
            return {1:result}
        if (itemtype is None and state == "all"):
            return {1:itemlist}
        elif(itemtype is not None and state == "all"):
            for item in itemlist:
                if (item["itemtype"] == itemtype):
                    result.append(item)
        elif(itemtype is not None and state != "all"):
            for item in itemlist:
                if (item["itemtype"] == itemtype and item["state"] == state):
                    result.append(item)
        else:
            for item in itemlist:
                if (item["state"] == state):
                    result.append(item)
        return {1:result}

    # Static method watch for new items. User will be notified by calling watchmethod for newly added items and staring bids for given item types. None stands for all types
    @staticmethod
    def watch(itemtype=None):
        if (itemtype is None):
            pipeline = [{"$match": {"operationType": "insert"}}]
        else:
            pipeline = [
                {"$match": {"operationType": "insert", "fullDocument.itemtype": itemtype}}]
        try:
            return pipeline
        except:
            print("Error: unable to start thread")

    # Users virtual balance in system is incremented/decremented by amount
    def addbalance(self, amount):
        self.balance += int(amount)
        user_collection.update_one(
            {"email": self.email}, {"$set": {"balance": self.balance}})
        return {1:"Your new balance is {0}".format(self.balance)}

    # Get financial report for user including items sold, on sale, all expenses and income
    def report(self):
        items = item_collection.find({"owner": self.email})
        itemlist = list(items)
        boughtitems = item_collection.find({"newowner": self.email})
        boughtitemlist = list(boughtitems)
        solditems = []
        onsaleitems = []
        income = 0
        expense = 0
        for item in itemlist:
            if(item["state"] == "sold"):
                solditems.append(item)
                income = income + int(item["price"])
            else:
                onsaleitems.append(item)

        for item in boughtitemlist:
            expense = expense + int(item["price"])
        returnstring = ""
        returnstring += "-----REPORT-----\n"
        returnstring += self.name + " " + self.surname + "\n"
        returnstring += "You sold this items:\n"
        for item in solditems:
            returnstring += "- " + item["title"] + "\n"
        returnstring += "You have this items onsale:\n"
        for item in onsaleitems:
            returnstring += "- " + item["title"] + "\n"
        returnstring += "Your income is {0}$".format(income)
       
        returnstring += "\nYour expense is {0}$".format(expense)
        return {1:returnstring}


class SellItem:
    # Create a new item for sale. bidtype is either of increment, decrement, instantincrement. minbid is the minimum bid unit.
    def __init__(self, owner, title, itemtype, description, bidtype, starting, minbid=1.0,bring=False, image=None):
        self.owner = owner
        self.newowner = ""
        self.state = "onhold"
        self.price = 0
        self.title = title
        self.itemtype = itemtype
        self.description = description
        self.bidtype = bidtype
        self.starting = starting
        self.minbid = minbid
        self.image = image
        self.stopbid = 0
        self.currentbid = 0
        self.lastbidder = ""
        self.decremented = starting
        if(not bring):
            itemtosave = self.__dict__
            item_collection.insert_one(itemtosave)

    @staticmethod
    def getitem(owner, title):
        item = item_collection.find_one(
            {"owner": owner, "title": title})
        if(item):
            itemclass = SellItem(owner,title,item["itemtype"],item["description"],item["bidtype"],item["starting"],item["minbid"],True)
            itemclass.newowner = item["newowner"]
            itemclass.state = item["state"]
            itemclass.price = item["price"]
            itemclass.stopbid = item["stopbid"]
            itemclass.currentbid = item["currentbid"]
            itemclass.lastbidder = item["lastbidder"]
            itemclass.decremented =item["decremented"]
            return itemclass

    def decrementer(self):
        while(self.decremented >= self.stopbid):
            time.sleep(10)
            decrementAmount = int((self.starting-self.stopbid)/5)
            self.decremented -= decrementAmount
            history_collection.insert_one({"owner":self.owner,"title":self.title,"bidder":"decrementer","bidAmount":decrementAmount,"isSold":False})
            item = item_collection.find_one_and_update(
                    {"owner": self.owner, "title": self.title}, {"$set": {"decremented": self.decremented}})
            if(self.newowner != ""):
                _thread.exit_thread()

    # Start the bidding for auctions. Auction will stop when stopbid is reached, if there is a bidder at the moment, he/she will win the auction automatically.
    def startauction(self, stopbid=None):
        if (stopbid is None):
            self.state = "active"
            item = item_collection.find_one_and_update(
                {"owner": self.owner, "title": self.title}, {"$set": {"state": "active"}})
            return {1:"The auction had started"}
        else:
            if(stopbid < self.minbid):
                return {1:"Stop bid can not be less than min bid"}
            else:
                if(self.bidtype == "decrement"):
                    _thread.start_new_thread(decrementer,())
                self.state = "active"
                self.stopbid = stopbid
                item = item_collection.find_one_and_update(
                    {"owner": self.owner, "title": self.title}, {"$set": {"state": "active", "stopbid": stopbid}})
                return {1:"The auction had started"}

    # User bids the amount for the item. Auction should be active and users should have a corressponding balance. Users balance is reserved by this amount. He/she cannot spend it until bid is complete. If there is a previous bid, it is updated.
    def bid(self, user, stramount):
        amount = int(amount)
        if(self.state == "active"):
            dbuser = user_collection.find_one({"email": user})
            if (dbuser):
                if(self.bidtype == "increment"):
                    if(int(dbuser["balance"]) - int(dbuser["reservedbalance"]) >= amount):
                        if(self.stopbid != 0 and amount >= self.stopbid):
                            self.price = amount
                            self.newowner = user
                            self.state = "sold"
                            item = item_collection.find_one_and_update(
                                {"owner": self.owner, "title": self.title}, {"$set": self.__dict__})
                            user_collection.find_one_and_update(
                                {"email": user}, {"$set": {"balance": int(dbuser["balance"])-amount}})
                            history_collection.insert_one({"owner":self.owner,"title":self.title,"bidder":user,"bidAmount":amount,"isSold":True,"soldto":self.newowner})
                            return {1:"Item is sold for {0} and the new owner is {1}".format(
                                self.price, dbuser["name"]+" "+dbuser["surname"])}
                        else:
                            if(amount > self.currentbid):
                                self.currentbid = amount
                                if (self.lastbidder != ""):
                                    lastbidder = user_collection.find_one(
                                        {"email": self.lastbidder})
                                    user_collection.find_one_and_update(
                                        {"email": self.lastbidder}, {"$set": {"reservedbalance": int(lastbidder["reservedbalance"])-amount}})
                                self.lastbidder = user
                                newreservedbalance = int(dbuser["reservedbalance"])+amount
                                user_collection.find_one_and_update(
                                    {"email": user}, {"$set": {"reservedbalance": newreservedbalance}})
                                item = item_collection.find_one_and_update(
                                    {"owner": self.owner, "title": self.title}, {"$set": {"currentbid": self.currentbid, "lastbidder": user}})
                                history_collection.insert_one({"owner":self.owner,"title":self.title,"bidder":user,"bidAmount":amount,"isSold":False})
                                return {1:"The new bid for {0} is {1}$".format(
                                    self.title, self.currentbid)}
                            else:
                                return {1:"Your bid need to more than last bid"}
                    else:
                        return {1:"You don't have enough amount to bid to this item"}
                elif(self.bidtype == "decrement"):
                    if(int(dbuser["balance"]) - int(dbuser["reservedbalance"]) >= amount):
                        if(self.stopbid != 0 and amount >= self.decremented):
                            self.price = amount
                            self.newowner = user
                            self.state = "sold"
                            item = item_collection.find_one_and_update(
                                {"owner": self.owner, "title": self.title}, {"$set": self.__dict__})
                            user_collection.find_one_and_update(
                                {"email": user}, {"$set": {"balance": int(dbuser["balance"])-amount}})
                            history_collection.insert_one({"owner":self.owner,"title":self.title,"bidder":user,"bidAmount":amount,"isSold":True,"soldto":self.newowner})
                            return {1:"Item is sold for {0} and the new owner is {1}".format(
                                self.price, dbuser["name"]+" "+dbuser["surname"])}
                        else:
                            if(amount > self.currentbid):
                                self.currentbid = amount
                                if (self.lastbidder != ""):
                                    lastbidder = user_collection.find_one(
                                        {"email": self.lastbidder})
                                    user_collection.find_one_and_update(
                                        {"email": self.lastbidder}, {"$set": {"reservedbalance": int(lastbidder["reservedbalance"])-amount}})
                                self.lastbidder = user
                                newreservedbalance = int(dbuser["reservedbalance"])+amount
                                user_collection.find_one_and_update(
                                    {"email": user}, {"$set": {"reservedbalance": newreservedbalance}})
                                item = item_collection.find_one_and_update(
                                    {"owner": self.owner, "title": self.title}, {"$set": {"currentbid": self.currentbid, "lastbidder": user}})
                                history_collection.insert_one({"owner":self.owner,"title":self.title,"bidder":user,"bidAmount":amount,"isSold":False})
                                return {1:"The new bid for {0} is {1}$".format(
                                    self.title, self.currentbid)}
                            else:
                                return {1:"Your bid need to more than last bid"}
                    else:
                        return {1:"You don't have enough amount to bid to this item"}
                elif(self.bidtype == "instantincrement"):
                    if(int(dbuser["balance"]) - int(dbuser["reservedbalance"]) >= amount):
                        if(self.stopbid != 0 and amount+self.currentbid >= self.stopbid):
                            self.price = amount
                            self.newowner = user
                            self.state = "sold"
                            item = item_collection.find_one_and_update(
                                {"owner": self.owner, "title": self.title}, {"$set": self.__dict__})
                            user_collection.find_one_and_update(
                                {"email": user}, {"$set": {"balance": int(dbuser["balance"])-amount}})
                            history_collection.insert_one({"owner":self.owner,"title":self.title,"bidder":user,"bidAmount":amount,"isSold":True,"soldto":self.newowner})
                            return {1:"Item is sold for {0} and the new owner is {1}".format(
                                self.price, dbuser["name"]+" "+dbuser["surname"])}
                        else:
                            self.currentbid += amount
                            self.lastbidder = user
                            newbalance = int(dbuser["balance"])-amount
                            user_collection.find_one_and_update(
                                {"email": user}, {"$set": {"balance": newbalance}})
                            item = item_collection.find_one_and_update(
                                {"owner": self.owner, "title": self.title}, {"$set": {"currentbid": self.currentbid, "lastbidder": user}})
                            history_collection.insert_one({"owner":self.owner,"title":self.title,"bidder":user,"bidAmount":amount,"isSold":False})
                            return {1:"The new bid for {0} is {1}$".format(
                                self.title, self.currentbid)}
                    else:
                        return {1:"You don't have enough amount to bid to this item"}
            else:
                return {1:"User not found."} 
        else:
            return {1:"This item is not onsale"}

    # Only owner can call this. Item is sold to the last bidder. Auction is closed
    def sell(self):
        self.price = self.currentbid
        newowner = user_collection.find_one({"email": self.lastbidder})
        self.newowner = self.lastbidder
        self.state = "sold"
        item = item_collection.find_one_and_update(
            {"owner": self.owner, "title": self.title}, {"$set": {"state": self.state, "newowner": self.newowner, "price": self.price}})
        user_collection.find_one_and_update(
            {"email": self.newowner}, {"$set": {"balance": int(newowner["balance"])-self.currentbid, "reservedbalance": int(newowner["reservedbalance"])-self.currentbid}})
        history_collection.insert_one({"owner":self.owner,"title":self.title,"isSold":True,"soldto":self.newowner})
        return {1:"Item is sold for {0} and the new owner is {1}".format(
            self.price, newowner)}

    # Give the complete state of the item. Show auction data if available as well.
    def view(self):
        if(self.state == "active"):
            return {1:"{0} is for sale and the last bid is {1}$".format(
                self.title, self.currentbid)}
        elif(self.state == "onhold"):
            return {1:"{0} is ready to sell, you can start the auction".format(self.title)}
        else:
            return {1:"{0}  is sold for {1}$".format(self.title, self.price)}

    # User is notified by calling watchmethod when the auction state of the item changes
    def watch(self):
        pipeline = [{"$match": {"operationType": "update",
                                "fullDocument.owner": self.owner, "fullDocument.title": self.title}}]
        try:
            return pipeline
        except:
            print("Error: unable to start thread")

    # Detailed acivity log for item with creation, auction start, bids and final value
    def history(self):
        returnstring=""
        for x in history_collection.find({"owner":self.owner,"title":self.title}):
            returnstring += str(x)
        return {1:returnstring}


def encrypt_password(password):
    return pwd_context.hash(password)


def check_encrypted_password(password, hashed):
    return pwd_context.verify(password, hashed)


def beautify():
    print()
    print("----------------")
    print()



pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    default="pbkdf2_sha256",
    pbkdf2_sha256__default_rounds=30000
)
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client.get_database("bidding")
user_collection = db.get_collection("users")
item_collection = db.get_collection("items")
history_collection = db.get_collection("history")
