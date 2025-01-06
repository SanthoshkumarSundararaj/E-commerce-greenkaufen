import firebase_admin
from firebase_admin import credentials, auth, firestore
import pyrebase
from config import firebaseConfig

firebase = pyrebase.initialize_app(firebaseConfig)
db_fire = firebase.database()

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
firestore_db = firestore.client()

def create_user(email, password):
    user = auth.create_user(email=email, password=password)
    return user

def add_user_to_db(user_id, email):
    data = {"user_id": user_id, "email": email}
    firestore_db.collection("users").add(data)

def add_bulk_enquiry(firstname, lastname, email, mobile, company, product, quantity, message):
    data = {
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
        "mobile": mobile,
        "company": company,
        "product": product,
        "quantity": quantity,
        "message": message
    }
    firestore_db.collection("bulk_enquiries").add(data)

def add_subscription(email):
    data = {"email": email}
    firestore_db.collection("subscriptions").add(data)
