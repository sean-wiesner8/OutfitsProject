from db import db
from flask import Flask
from flask import request
import json
import os

from db import Users
from db import Clothes 
from db import Outfits 
from db import create_user
from db import verify_credentials
from db import renew_session
from db import verify_session

app = Flask(__name__)
db_filename = "outFit.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()

def success_response(data, code=200):
    return json.dumps(data), code

def failure_response(message, code=404):
    return json.dumps({"error" : message}), code

def extract_token(request):
    token = request.headers.get("Authorization")
    if token is None:
        return False, "missing authroization header"
    token = token.replace("Bearer", "").strip()
    return True, token


@app.route("/")

# your routes here
#USERS
@app.route("/api/register/", methods=['POST'])
def register_account():
    body = json.loads(request.data)
    username = body.get("username")
    password = body.get("password")
    if username is None or password is None:
        return failure_response("invalid email or password")
    
    created, user = create_user(username, password)

    if not created:
        return failure_response("user already exists", 403)
    
    return success_response({
        "session_token": user.session_token,
        "session_expiration": str(user.session_expiration),
        "update_token": user.update_token
    })

@app.route("/api/login/", methods=['POST'])
def login():
    body = json.loads(request.data)
    username = body.get("username")
    password = body.get("password")
    if username is None or password is None:
        return failure_response("invalid email or password", 400)
    
    valid_creds, user = verify_credentials(username, password)

    if not valid_creds:
        return failure_response("invalid email or password")
    
    return success_response({
        "session_token": user.session_token,
        "session_expiration": str(user.session_expiration),
        "update_token": user.update_token
    })

@app.route("/api/session/", methods=['POST'])
def update_session():
    success, update_token = extract_token(request)

    if not success:
        return failure_response(update_token)
    
    valid, user = renew_session(update_token)

    if not valid:
        return failure_response("invalid update token")
    
    return success_response({
        "session_token": user.session_token,
        "session_expiration": str(user.session_expiration),
        "update_token": user.update_token
    })

@app.route("/api/secret/")
def secret_message():
    success, session_token = extract_token(request)

    if not success:
        return failure_response(session_token)
    
    valid = verify_session(session_token)

    if not valid:
        return failure_response("invalid session token")
    
    return success_response("hello world")

@app.route("/api/users/")
def get_users():
    return success_response({"users": [user.serialize() for user in Users.query.all()]})

@app.route("/api/users/<int:id>/")
def get_user_by_id(id):
    user = Users.query.filter_by(id=id).first()
    if user is None:
        return failure_response("user does not exist")
    return success_response(user.serialize(), 201)

@app.route("/api/users/<int:id>/", methods=['DELETE'])
def del_user_by_id(id):
    user = Users.query.filter_by(id=id).first()
    if user is None:
        return failure_response("user does not exist")
    db.session.delete(user)
    db.session.commit()
    return success_response(user.serialize())

@app.route("/api/users/<int:id>/outfits/")
def get_outfits_by_user_id(id):
    user = Users.query.filter_by(id=id)
    if user is None:
        return failure_response("user does not exist")
    outfits = Outfits.query.filter_by(user_id=id)
    if outfits is None:
        return success_response("User does not have any outfits yet")
    return success_response({"outfits": [o.serialize() for o in outfits]})

#OUTFITS
@app.route("/api/outfits/")
def get_outfits():
    return success_response({"outfits": [o.serialize() for o in Outfits.query.all()]})

@app.route("/api/outfits/<int:id>/")
def get_outfit_by_id(id):
    outfit = Outfits.query.filter_by(id=id).first()
    if outfit is None:
        return failure_response("outfit does not exist")
    return success_response(outfit.serialize())

@app.route("/api/outfits/", methods=['POST'])
def post_outfit():
    body = json.loads(request.data)
    user_id = body.get("user_id", False)
    top_id = body.get("top_id", False)
    bottom_id = body.get("bottom_id", False)
    if not user_id or not top_id or not bottom_id or type(user_id) != int or type(top_id) != int or type(bottom_id) != int:
        return failure_response("user_id, top_id, or bottom_id fields are incorrect", 400)
    else:
        new_outfit = Outfits(user_id=user_id, top_id=top_id, bottom_id=bottom_id)
        db.session.add(new_outfit)
        db.session.commit()
        return success_response(new_outfit.serialize(), 201)

@app.route("/api/outfits/<int:id>/", methods=['DELETE'])
def del_outfit(id):
    outfit = Outfits.query.filter_by(id=id).first()
    if outfit is None:
        return failure_response("outfit does not exist")
    db.session.delete(outfit)
    db.session.commit()
    return success_response(outfit.serialize())

@app.route("/api/outfits/<int:id>/users/")
def get_user_by_outfit_id(id):
    outfit = Outfits.query.filter_by(id=id).first()
    if outfit is None:
        return failure_response("outfit does not exist")
    user_id = outfit.serialize()["user_id"]
    user = Users.query.filter_by(id=user_id).first()
    return success_response(user.username_serialize())


#TOPS
@app.route("/api/tops/")
def get_tops():
    return success_response({"tops": [t.sub_serialize() for t in Clothes.query.filter_by(top=True)]})

@app.route("/api/tops/<int:id>/")
def get_top_by_id(id):
    top = Clothes.query.filter_by(id=id).first()
    if top is None:
        return failure_response("top does not exist")
    if not top.top:
        return failure_response("this item is not a top", 400)
    return success_response(top.sub_serialize())

@app.route("/api/tops/", methods=['POST'])
def post_tops():
    body = json.loads(request.data)
    image_data = body.get("image_data", False)
    if not image_data or type(image_data) != str:
        return failure_response("image_data field is incorrect", 400)
    else:
        new_top = Clothes(image_data=image_data, top=True)
        db.session.add(new_top)
        db.session.commit()
        return success_response(new_top.serialize(), 201)

@app.route("/api/tops/<int:id>/", methods=['DELETE'])
def del_top(id):
    top = Clothes.query.filter_by(id=id).first()
    if top is None:
        return failure_response("top does not exist")
    if not top.top:
        return failure_response("this is not a top")
    db.session.delete(top)
    db.session.commit()
    return success_response(top.sub_serialize())

#BOTTOMS
@app.route("/api/bottoms/")
def get_bottoms():
    return success_response({"bottoms": [b.sub_serialize() for b in Clothes.query.filter_by(top=False)]})

@app.route("/api/bottoms/<int:id>/")
def get_bottom_by_id(id):
    bottom = Clothes.query.filter_by(id=id).first()
    if bottom is None:
        return failure_response("bottom does not exist")
    if bottom.top:
        return failure_response("this item is not a bottom", 400)
    return success_response(bottom.sub_serialize())

@app.route("/api/bottoms/", methods=['POST'])
def post_bottoms():
    body = json.loads(request.data)
    image_data = body.get("image_data", False)
    if not image_data or type(image_data) != str:
        return failure_response("image_data field is incorrect", 400)
    else:
        new_bottom = Clothes(image_data=image_data, top=False)
        db.session.add(new_bottom)
        db.session.commit()
        return success_response(new_bottom.serialize(), 201)

@app.route("/api/bottoms/<int:id>/", methods=['DELETE'])
def del_bottoms(id):
    bottom = Clothes.query.filter_by(id=id).first()
    if bottom is None:
        return failure_response("bottom does not exist")
    if bottom.top:
        return failure_response("this is not a bottom")
    db.session.delete(bottom)
    db.session.commit()
    return success_response(bottom.sub_serialize())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)