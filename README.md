# OutfitsProject
The backend database and route implementation for a theoretical app that allows users to visualize outfits by mixing and matching clothing items that they found on the internet.


## Tools Used

Database: SQLite

ORM: SQLAlchemy

Backend Language: Python

Backend Framework: Flask

Image File Storage: AWS S3 Bucket


The database includes three tables: users, outfits, and clothes. The users table is a list of users using this application, the outfits table is a list of outfits, each with a foreign key attributed to a user and secondary keys associated with a top and a bottom from the clothes table, and the clothes table is a list of either tops or bottoms, all of which are .jpeg or .png files simultaneously stored in an AWS bucket. 

## 21 routes implemented:

POST /api/register/
Pass in "username" and "password" fields to register a new user. Success response returns a unique base64 session token, session token expiration datetime, and base64 update token attributed to new user. Hashes password and stores password in database.
Returns error if fields are missing or username already exists.

POST /api/login/
Pass in "username" and "password" fields to login to account. Success response returns existing session token, session token expiration datetime, and update token attributed to user.
Returns error if username or password fields are invalid.

POST /api/session/
Pass update token into "Authorization" header. Success response returns an updated session token, session token expiration datetime, and update token.
Returns error if "Authorization" header does not exist or if token in header is not the same as update token field in database.  

GET /api/secret/
Pass session token into "Authorization" header. Success response returns 'hello world'. 
Returns error if "Authorization" header does not exist or if token in header is not the same as session token field in database.

GET /api/users/
Success response returns all users.

GET /api/users/<int:id>/
Success response returns user by id.
Returns error if user does not exist.

DELETE /api/users/<int:id>/
Success response removes user by id from database and returns user.
Returns error if user does not exist.

GET /api/users/<int:id>/outfits/
Success response returns all outfits of specified user. If user does not have any outfits, returns "User does not have any outfits yet". 
Returns error if user does not exist.

GET /api/outfits/
Success response returns all outfits.

GET /api/outfits/<int:id>/
Success response returns outfit by id.
Returns error if outfit does not exist.

POST /api/outfits/
Pass in user_id, top_id, and bottom_id fields. Success response returns serialized outfit with id, user_id, top_id, and bottom_id fields. 
Returns error if any fields are empty or are the wrong type. 

DELETE /api/outfits/<int:id>/
Success response removes specified outfit from database and returns outfit. 
Returns error if outfit does not exist.

GET /api/outfits/<int:id>/users/
Success response returns the user who created specified outfit.
Returns error if outfit does not exist.

GET /api/tops/
Success response returns all tops, serialized by id and url for image stored in AWS bucket.

GET /api/tops/<int:id>/
Success response returns top specified by id. 
Returns error if id does not exist or the clothing item specified by id is not a top.

POST /api/tops/
Pass in base64 image data (.jpeg and .png files only). Generates salt, finds extension, creates AWS url, and uploads image to AWS bucket and simultaneously updates clothing table in database. Success response returns serialized top with id, url, and boolean to identify that item is a top.
Returns error if image data is invalid.

DELETE /api/tops/<int:id>/
Success response removes and returns specified top from database. 
Returns error if id does not exist or if specified clothing item is not a top.

GET /api/bottoms/
Success response returns all bottoms, serialized by id and url for image stored in AWS bucket.

GET /api/bottoms/<int:id>/
Success response returns bottom specified by id.
Returns error if id does not exist or the clothing item specified by id is not a bottom.

POST /api/bottoms/
Pass in base64 image data (.jpeg and .png files only). Generates salt, finds extension, creates AWS url, and uploads image to AWS bucket and simultaneously updates clothing table in database. Success response returns serialized bottom with id, url, and boolean to identify that item is a bottom.
Returns error if image data is invalid.

DELETE /api/bottoms/<int:id>/
Success response removes and returns specified bottom from database. 
Returns error if id does not exist or if specified clothing item is not a bottom.






