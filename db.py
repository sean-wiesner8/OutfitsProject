from flask_sqlalchemy import SQLAlchemy

import base64
import boto3
from io import BytesIO
from mimetypes import guess_extension, guess_type
import os
from PIL import Image
import random
import re
import string
import hashlib
import bcrypt
import datetime

db = SQLAlchemy()

EXTENSIONS = ["png", "gif", "jpg", "jpeg", "webp"]
BASE_DIR = os.getcwd()
S3_BUCKET = "hackchallengeimages"
S3_BASE_URL = f"http://{S3_BUCKET}.s3.us-east-2.amazonaws.com"

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password_digest = db.Column(db.String, nullable=False)
    outfits = db.relationship("Outfits", cascade='delete')

    session_token = db.Column(db.String, nullable=False, unique=True)
    session_expiration = db.Column(db.DateTime, nullable=False)
    update_token = db.Column(db.String, nullable=False, unique=True)

    def __init__(self, **kwargs):
        self.username = kwargs.get("username")
        self.password_digest = bcrypt.hashpw(kwargs.get("password").encode("utf8"), bcrypt.gensalt(rounds=13))
        self.renew_session()

    # Used to randomly generate session/update tokens
    def _urlsafe_base_64(self):
        return hashlib.sha1(os.urandom(64)).hexdigest()
    
    # Generates new tokens, and resets expiration time
    def renew_session(self):
        self.session_token = self._urlsafe_base_64()
        self.session_expiration = datetime.datetime.now() + datetime.timedelta(days=1)
        self.update_token = self._urlsafe_base_64()
    
    def verify_password(self, password):
        return bcrypt.checkpw(password.encode("utf8"), self.password_digest)
    
    # Checks if session token is valid and hasn't expired
    def verify_session_token(self, session_token):
        return session_token == self.session_token and datetime.datetime.now() < self.session_expiration

    def verify_update_token(self, update_token):
        return update_token == self.update_token
    
    def full_serialize(self):
        return {
         "id": self.id,
        "username": self.username,
        "password": self.password,
        "outfits": [o.serialize() for o in self.outfits]   
        }

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "outfits": [o.serialize() for o in self.outfits]
        }
    
    def sub_serialize(self):
        return {
            "username": self.username,
            "outfits": [o.serialize() for o in self.outfits]
        }
    
    def username_serialize(self):
        return {
            "username": self.username
        }

def create_user(username, password):
    existing_user = Users.query.filter(Users.username == username).first()
    if existing_user:
        return False, None
    user = Users(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    return True, user

def verify_credentials(username, password):
    existing_user = Users.query.filter(Users.username == username).first()
    if not existing_user:
        return False, None
    
    return existing_user.verify_password(password), existing_user

def renew_session(update_token):
    existing_user = Users.query.filter(Users.update_token == update_token).first()
    if not existing_user:
        return False, None
    
    existing_user.renew_session()
    db.session.commit()
    return True, existing_user

def verify_session(session_token):
    return Users.query.filter(Users.session_token == session_token).first()

class Outfits(db.Model):
    __tablename__ = 'outfits'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    top_id = db.Column(db.Integer, nullable=False)
    bottom_id = db.Column(db.Integer, nullable=False)

    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id")
        self.top_id = kwargs.get("top_id")
        self.bottom_id = kwargs.get("bottom_id")

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "top_id": self.top_id,
            "bottom_id": self.bottom_id
        }

class Clothes(db.Model):
    __tablename__ = 'clothes'
    id = db.Column(db.Integer, primary_key=True)
    base_url = db.Column(db.String, nullable=True)
    salt = db.Column(db.String, nullable=False)
    extension = db.Column(db.String, nullable=False)

    top = db.Column(db.Boolean, nullable=False)

    def __init__(self, **kwargs):
        self.create(kwargs.get("image_data"))
        self.top = kwargs.get("top")

    def serialize(self):
        return {
            "id": self.id,
            "url": f"{self.base_url}/{self.salt}.{self.extension}",
            "top": self.top
        }
    
    def sub_serialize(self):
        return {
            "id": self.id,
            "url": f"{self.base_url}/{self.salt}.{self.extension}"
        }
    
    def create(self, image_data):
        try:
            ext = guess_extension(guess_type(image_data)[0])[1:]
            if ext not in EXTENSIONS:
                raise Exception(f"Extension {ext} not supported")

            salt = "".join(
                random.SystemRandom().choice(
                    string.ascii_uppercase + string.digits
                )
            for _ in range(16)
            )

            img_str = re.sub("^data:image/.+;base64,", "", image_data)
            img_data = base64.b64decode(img_str)
            img = Image.open(BytesIO(img_data))

            self.base_url = S3_BASE_URL
            self.salt = salt
            self.extension = ext

            img_filename = f"{salt}.{ext}"
            self.upload(img, img_filename)
        except Exception as e:
            print(f"Unable to create image due to {e}")

    def upload(self, img, img_filename):
        try:
            img_temploc = f"{BASE_DIR}/{img_filename}"
            img.save(img_temploc)

            s3client = boto3.client("s3")
            s3client.upload_file(img_temploc, S3_BUCKET, img_filename)

            s3_resource = boto3.resource("s3")
            object_acl = s3_resource.ObjectAcl(S3_BUCKET, img_filename)
            object_acl.put(ACL="public-read")
            os.remove(img_temploc)

        except Exception as e:
            print("Unable to open image due to {e}")

