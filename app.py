from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
from flask_session import Session
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from forms import SignupForm, LoginForm, UpdateProfileForm, UpdateAddressForm, BulkEnquiryForm
from models import db, User, WishlistItem, CartItem, Profile, Billing
from database import db, migrate, init_db
from firebase_helper import create_user, add_user_to_db, add_bulk_enquiry, add_subscription
import json
import uuid
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
import paypalrestsdk

app = Flask(__name__)
app.config.from_object(Config)

# Configure PayPal
paypalrestsdk.configure({
  "mode": "live",  # Change to "live" for production
  "client_id": "",
  "client_secret": "" 
})

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize the database and migrations
init_db(app)

# Function to create tables
def create_tables():
    with app.app_context():
        db.create_all()

# Apply migrations and create tables when the app starts
def setup_database():
    create_tables()


Session(app)

def send_email(firstname, lastname, email, mobile, company, product, quantity, message):
    try:
        msg = MIMEMultipart()
        msg['From'] = Config.SMTP_USERNAME
        msg['To'] = Config.SMTP_USERNAME
        msg['Subject'] = "Bulk Enquiry Form Submission"

        body = f"""
        First Name: {firstname}
        Last Name: {lastname}
        Email: {email}
        Mobile: {mobile}
        Company: {company}
        Product: {product}
        Quantity: {quantity}
        Message: {message}
        """
        msg.attach(MIMEText(body, 'plain'))

        server = SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
        server.starttls()
        server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(Config.SMTP_USERNAME, Config.SMTP_USERNAME, text)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

def cart_to_dict(user):
    return {
        "id": user.id,
        "user_id": user.user_id,
        "product_id": user.product_id,
        "quantity": user.quantity,
        "number": user.number
    }

@app.route("/", methods=["GET", "POST"])
def home():
    with open('products.json') as file:
        ex_product = json.load(file)
    with open('blog.json') as file_blog:
        blog_post = json.load(file_blog)

    # Pass the user's email if authenticated
    user_email = current_user.email if current_user.is_authenticated else ""

    return render_template('index-2.html', ex_product=ex_product, blog_post=blog_post, user_email=user_email)

@app.route('/shop')
def shop():
    item = request.args.get('item')
    with open('products.json') as file:
        ex_product = json.load(file)
    
    if item == 'all':
        context = {'ex_product': ex_product}
        
    elif item == 'palm':
        palm_product = [i for i in ex_product if i['tag'] == 'palm']
        context = {'ex_product': palm_product}
        
    elif item == 'sugar':
        sugar_product = [i for i in ex_product if i['tag'] == 'sugar']
        context = {'ex_product': sugar_product}
    
    return render_template('shop.html', **context)

@app.route("/product/<int:product_id>")
def product(product_id):
    with open('products.json') as file:
        ex_product = json.load(file)
        
    product = next((item for item in ex_product if item["id"] == product_id), None)

    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    related_tag = product["tag"]

    if related_tag == 'palm':
        related_product = [i for i in ex_product if i['tag'] == 'palm']
    elif related_tag == 'sugar':
        related_product = [i for i in ex_product if i['tag'] == 'sugar']
    else:
        related_product = []

    context = {'product': product, 'related_product': related_product}
    return render_template("product-details.html", **context)

@app.route('/blog')
def blog():
    with open('blog.json') as file:
        blog_details = json.load(file)
    return render_template('blog.html', blog_details=blog_details)

@app.route('/blogdetail')
def blogdetail():
    id = request.args.get('id')
    with open('blog.json') as file:
        blog_details = json.load(file)
    blog_ex = blog_details[int(id) - 1]
    return render_template('blog-details.html', blog_ex=blog_ex)

@app.route('/bulkenquiry', methods=['GET'])
def bulk():
    return render_template("bulk_enquiry.html")

@app.route('/bulkenquiry', methods=['POST'])
def bulk_process():
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    email = request.form.get('email')
    mobile = request.form.get('mobile')
    company = request.form.get('company')
    product = request.form.get('product')
    quantity = request.form.get('quantity')
    message = request.form.get('message')

    # Add additional user details to Firestore
    add_bulk_enquiry(firstname, lastname, email, mobile, company, product, quantity, message)

    # Send email with form details
    send_email(firstname, lastname, email, mobile, company, product, quantity, message)

    return render_template("bulk_thanks.html")

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/impressum')
def impressum():
    return render_template('impressum.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.route("/add_to_wishlist/<int:product_id>", methods=["GET"])
def add_to_wishlist(product_id):
    if current_user.is_authenticated:
        user_id = current_user.id

        # Check if the item is already in the wishlist
        existing_item = WishlistItem.query.filter_by(user_id=user_id, product_id=product_id).first()
        if existing_item:
            flash('Item already in your wishlist!', 'info')
        else:
            # Add new item to the wishlist
            new_wishlist_item = WishlistItem(user_id=user_id, product_id=product_id)
            db.session.add(new_wishlist_item)
            db.session.commit()
            flash('Product added to wishlist!', 'success')
    else:
        # Guest user: Store in session
        wishlist = session.get('wishlist', [])
        if product_id not in wishlist:
            wishlist.append(product_id)
            session['wishlist'] = wishlist
            flash('Product added to wishlist!', 'success')
        else:
            flash('Item already in your wishlist!', 'info')

    return redirect(url_for('wishlist'))


@app.route("/wishlist", methods=["GET"])
def wishlist():
    if current_user.is_authenticated:
        user_id = current_user.id
        # Fetch wishlist items for the current user
        wishlist_items_db = WishlistItem.query.filter_by(user_id=user_id).all()
        wish_product_ids = [item.product_id for item in wishlist_items_db]
    else:
        # Guest user: Get wishlist from session
        wish_product_ids = session.get('wishlist', [])

    # Load product data from JSON file
    with open('products.json') as f:
        products = json.load(f)

    # Filter products based on wishlist items
    wishlist_items = [prod for prod in products if prod['id'] in wish_product_ids]
    print(wishlist_items)
    return render_template('wishlist.html', wishlist_items=wishlist_items)

@app.route("/remove_from_wishlist/<int:product_id>", methods=["GET"])
def remove_from_wishlist(product_id):
    if current_user.is_authenticated:
        user_id = current_user.id
        # For logged-in users: Remove the item from the database
        wishlist_item = WishlistItem.query.filter_by(user_id=user_id, product_id=product_id).first()

        if wishlist_item:
            db.session.delete(wishlist_item)
            db.session.commit()
            flash('Item removed from your wishlist!', 'success')
        else:
            flash('Item not found in your wishlist!', 'error')

    else:
        # For guest users: Remove the item from the session
        wishlist = session.get('wishlist', [])
        if product_id in wishlist:
            wishlist.remove(product_id)
            session['wishlist'] = wishlist
            flash('Item removed from your wishlist!', 'success')
        else:
            flash('Item not found in your wishlist!', 'error')

    return redirect(url_for('wishlist'))


@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity')
    number = request.form.get('number')

    if current_user.is_authenticated:
        user_id = current_user.id

        # Check if the item already exists in the cart
        existing_cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()

        # Add or update cart item
        if existing_cart_item:
            existing_cart_item.quantity = quantity
            existing_cart_item.number = number
        else:
            new_cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity, number=number)
            db.session.add(new_cart_item)

        db.session.commit()
    else:
        # For guest users: Store in session
        cart = session.get('cart', {})
        cart[product_id] = {'quantity': quantity, 'number': number}
        session['cart'] = cart
        flash('Product added to cart!', 'success')

    flash('Product added to cart!', 'success')
    return redirect(url_for('cart'))

@app.route("/cart", methods=["GET"])
def cart():
    if current_user.is_authenticated:
        user_id = current_user.id

        # Fetch cart items from the database
        cart_items = CartItem.query.filter_by(user_id=user_id).all()

        # Map cart items to product ids
        cart_product_ids = [item.product_id for item in cart_items]
        cart_item_map = {item.product_id: {'quantity': item.quantity, 'number': item.number} for item in cart_items}
    else:
        # Guest user: Get cart from session
        cart = session.get('cart', {})
        cart_product_ids = list(cart.keys())
        cart_item_map = cart

    # Load product data from JSON file
    with open('products.json') as f:
        products = json.load(f)

    # Filter products based on cart items
    filtered_products = [product for product in products if str(product['id']) in cart_product_ids]

    for product in filtered_products:
        product_id = str(product['id'])
        if product_id in cart_item_map:
            product.update(cart_item_map[product_id])

    return render_template('cart.html', cart_items=filtered_products)


@app.route("/update_cart", methods=["POST"])
def update_cart():
    form = request.form

    if current_user.is_authenticated:
        user_id = current_user.id

        for key, value in form.items():
            if key.startswith("number_"):
                product_id_str = key.replace("number_", "")
                if product_id_str.isdigit():
                    product_id = int(product_id_str)
                    if value.isdigit():
                        number = int(value)
                        cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
                        if cart_item:
                            cart_item.number = number
                            db.session.commit()
    else:
        # Guest user: Update session cart
        cart = session.get('cart', {})
        for key, value in form.items():
            if key.startswith("number_"):
                product_id_str = key.replace("number_", "")
                if product_id_str.isdigit():
                    product_id = product_id_str
                    if value.isdigit():
                        cart[product_id]['number'] = int(value)
        session['cart'] = cart

    return jsonify({"success": True})

@app.route("/remove_from_cart/<int:product_id>", methods=["GET"])
def remove_from_cart(product_id):
    if current_user.is_authenticated:
        user_id = current_user.id
        # For logged-in users: Remove the item from the database
        cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
        
        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()
            flash('Item removed from your cart!', 'success')
        else:
            flash('Item not found in your cart!', 'error')

    else:
        # For guest users: Remove the item from the session
        cart = session.get('cart', [])
        if str(product_id) in cart:
            del cart[str(product_id)]
            session['cart'] = cart
            flash('Item removed from your cart!', 'success')
        else:
            flash('Item not found in your cart!', 'error')

    return redirect(url_for('cart'))


@app.route("/myaccount", methods=["GET"])
@login_required
def account():
    user = current_user
    print(user)
    if user.is_authenticated:
        profile = Profile.query.filter_by(user_id=user.id).first()
        billing = Billing.query.filter_by(user_id=user.id).first()
        email = current_user.email
        password = current_user.password
        context = {'user': user, 'profile': profile, 'billing': billing, 'email':email, 'password':password}
        return render_template("my-account.html", **context)
    
    return redirect(url_for("auth"))

@app.route("/updateuser", methods=["POST"])
@login_required
def update_user():
    user = current_user
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    # email = request.form.get('email')
    # password = request.form.get('password')
    birthdate = request.form.get('birthdate')
    newsletter = bool(request.form.get('newsletter'))
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    profile = Profile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = Profile(user_id=user.id)
        db.session.add(profile)
    
    profile.first_name = first_name
    profile.last_name = last_name
    # profile.email = email
    # profile.password = generate_password_hash(password)
    profile.birthdate = birthdate
    profile.newsletter = newsletter

    db.session.commit()

    return jsonify({"message": "User profile updated successfully"})

@app.route("/updateaddress", methods=["POST"])
@login_required
def update_address():
    user = current_user
    billing_name = request.form.get('billing_name')
    street = request.form.get('street')
    postal = request.form.get('postal')
    city = request.form.get('city')
    
    billing = Billing.query.filter_by(user_id=user.id).first()
    if not billing:
        billing = Billing(user_id=user.id)
        db.session.add(billing)
    
    billing.billing_name = billing_name
    billing.street = street
    billing.postal = postal
    billing.city = city

    db.session.commit()

    return jsonify({"message": "User billing updated successfully"})

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if current_user.is_authenticated:
        # User is logged in
        user_id = current_user.id
        cart_items = CartItem.query.filter_by(user_id=user_id).all()
        cart_dict = [cart_to_dict(item) for item in cart_items]
        profile = Profile.query.filter_by(user_id=user_id).first()
        billing = Billing.query.filter_by(user_id=user_id).first()
        email = current_user.email
    else:
        # Guest user
        cart_dict = session.get('cart', {})
        profile = None
        billing = session.get('billing')
        email = None

    if not cart_dict:
        # If cart is empty, redirect back to cart or show a message
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('cart'))

    # Process cart items based on whether user is logged in or not
    if current_user.is_authenticated:
        # For logged-in users
        cart_product_ids = [i['product_id'] for i in cart_dict]
        cart_product_ids = list(dict.fromkeys(cart_product_ids))
        cart_product_ids.sort()
    else:
        # For guest users
        cart_product_ids = list(cart_dict.keys())
        cart_product_ids.sort()

    with open('products.json') as file:
        ex_product = json.load(file)
    
    filtered_data = [product for product in ex_product if str(product['id']) in cart_product_ids]

    if current_user.is_authenticated:
        cart_item_map = {item['product_id']: {'quantity': item['quantity'], 'number': item['number']} for item in cart_dict}
    else:
        cart_item_map = {int(pid): details for pid, details in cart_dict.items()}

    for product in filtered_data:
        product_id = product['id']
        if product_id in cart_item_map:
            product.update(cart_item_map[product_id])

    # Handle POST request to save billing info for guest users
    if request.method == 'POST' and not current_user.is_authenticated:
        billing_data = {
            'name': request.form.get('billing_name'),
            'address': request.form.get('billing_address'),
            'email': request.form.get('billing_email')
        }
        session['billing'] = billing_data  # Save billing details in session for guest users

    context = {
        'cart_items': filtered_data,
        'profile': profile,
        'billing': billing,
        'email': email
    }

    return render_template("checkout.html", **context)

@app.route('/process_checkout', methods=['POST'])
def process_checkout():
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        user_id = None

    # Extract billing details from the form
    billing_details = {
        'first_name': request.form.get('first_name'),
        'last_name': request.form.get('last_name'),
        'company_name': request.form.get('company_name'),
        'country': request.form.get('country'),
        'street': request.form.get('street'),
        'city': request.form.get('city'),
        'state': request.form.get('state'),
        'phone': request.form.get('phone'),
        'email': request.form.get('email')
    }

    print(billing_details)

    if user_id:
        # Fetch cart items from the database for logged-in users
        cart_items = CartItem.query.filter_by(user_id=user_id).all()
        cart_dict = [cart_to_dict(item) for item in cart_items]
    else:
        # Use session data for guest users
        cart_dict = session.get('cart', {})

    # Load product data from JSON file
    with open('products.json') as f:
        products = json.load(f)

    # Calculate total price
    total_price = 0.00
    for product_id, cart_item in cart_dict.items():  # Iterate over items in cart_dict
        product_id = int(product_id)  # Ensure the product ID is an integer
        product = next((item for item in products if item['id'] == product_id), None)
        if product:
            quantity = int(cart_item['quantity'])
            number = int(cart_item['number'])
            price = float(product['price'][str(quantity)])  # Convert price to float
            total_price += price * number

    # Add fixed shipping cost (5.00 EUR)
    total_price += 5.00

    total_price = "{:.2f}".format(total_price)

    # Check which payment method is selected
    payment_method = request.form.get('check_method')

    if payment_method == 'paypal':
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": url_for('payment_execute', _external=True),
                "cancel_url": url_for('checkout', _external=True)
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "Your Order",
                        "sku": "item",
                        "price": total_price,
                        "currency": "EUR",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": total_price,
                    "currency": "EUR"
                },
                "description": "Your purchase description."
            }]
        })

        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    return redirect(approval_url)
        else:
            flash("An error occurred during the PayPal transaction.", "danger")
            return redirect(url_for('checkout'))

    flash("Payment method not supported.", "danger")
    return redirect(url_for('checkout'))

@app.route('/payment_execute')
def payment_execute():
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        flash("Payment successful!", "success")
        return redirect(url_for('home'))
    else:
        flash("Payment failed.", "danger")
        return redirect(url_for('checkout'))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email address already in use.', 'danger')
            return redirect(url_for('login'))
        try:
            hashed_password = generate_password_hash(form.password.data)
            user = User(email=form.email.data, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            # Assuming you have a create_user function that handles additional logic
            user_record = create_user(form.email.data, form.password.data)
            add_user_to_db(user_record.uid, form.email.data)
            session["user_id"] = user.id
            flash('Account created successfully', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html', form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)  # Use Flask-Login's login_user function
            flash('Login successful', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()  # Properly logout the user using Flask-Login
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    setup_database()
    app.run(debug=True)
