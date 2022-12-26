from flask import jsonify
from passlib.handlers.pbkdf2 import pbkdf2_sha256

from main import db


class User:
    def __init__(self,uid,username ,email, password):
        self.uid = uid
        self.username = username
        self.email = email
        self.password = pbkdf2_sha256.encrypt(password)
    def signup(self):
        if db.users.find_one({'email' : self.email}):
            return jsonify({ "error" : "Email address already in use"}), 400
        db.users.insert_one({'uid':self.uid,'username': self.username,'email': self.email, 'password': self.password})
        return "Registered!", 200
    def follow(self, to_id):
        follower_doc = db.followers.find_one({'following_id': to_id , 'follower_id' : self.uid})
        if follower_doc is None:
            db.followers.insert_one({'following_id': self.to_id,'follower_id': self.uid})

    @classmethod
    def from_dict(cls, doc):
        return cls(uid=doc['uid'],username=doc['username'], email=doc['email'], password=doc['password'])