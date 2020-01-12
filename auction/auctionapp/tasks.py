from background_task import background
from django.contrib.auth.models import User
import pymongo
from .models import *


@background()
def notify_user(user_id, item_type=None):
    print("Watch added for user:",user_id, " with item type:",item_type)
    user = User.objects.get(id=user_id)
    if (item_type is None):
        pipeline = [{"$match": {"operationType": "insert"}}]
    else:
        pipeline = [
            {"$match": {"operationType": "insert", "fullDocument.itemtype": item_type}}]
    try:
        with item_collection.watch(pipeline)as stream:
            for change in stream:
                returnstring = ""
                returnstring += "New Item Added: Title: {0} Item Type: {1} Bid Type: {2} Starting: {3}".format(
                    change["fullDocument"]["title"], change["fullDocument"]["itemtype"], change["fullDocument"]["bidtype"], change["fullDocument"]["starting"])
                Notification.objects.create(
                    userid=user.id, message=returnstring)
    except pymongo.errors.PyMongoError:
        print("Failure during ChangeStream initialization.")


@background()
def notify_user_item(user_id, item_id):
    print("Watch added for user:",user_id, " with item id:",item_id)
    user = User.objects.get(id=user_id)
    item = Item.objects.get(id=item_id)
    pipeline = [{"$match": {"operationType": "update",
                            "fullDocument.id": item_id}}]
    try:
        with item_collection.watch(pipeline, full_document='updateLookup')as stream:
            for change in stream:
                returnstring = ""
                returnstring += "Change in Watching Item: Title: {0} Change: {1} ".format(
                    change["fullDocument"]["title"], change["updateDescription"]["updatedFields"])
                Notification.objects.create(
                    userid=user.id, message=returnstring)
    except pymongo.errors.PyMongoError:
        print("Failure during ChangeStream initialization.")


@background
def decrementer(item_id):
    print("decrementer with item id:",item_id)
    item = Item.objects.get(id=item_id)
    if(item.state == "active"):
        item.decremented -= item.delta
        if item.decremented <= item.stop:
            item.state = "onhold"
            item.decremented = item.starting
        item.save()


client = pymongo.MongoClient("mongodb://localhost:27017")
db = client.get_database("bidding")
item_collection = db.get_collection("auctionapp_item")
