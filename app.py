from flask import Flask, flash, render_template, request, abort, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from io import BytesIO
import sqlite3
import os
import random
import string
import json

app = Flask(__name__)


#Set Secret Key
app.config['SECRET_KEY'] = "b'r\xca0\xd3Q\x80\x7f\x1ah\x14\xb9\xe3"

# Tells flask-sqlalchemy what database to connect to
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
# Enter a secret key
app.config["SECRET_KEY"] = "ENTER YOUR SECRET KEY"
# Initialize flask-sqlalchemy extension
userDB = SQLAlchemy()


# LoginManager is needed for our application 
# to be able to log in and out users
login_manager = LoginManager()
login_manager.init_app(app)

# Create user model
class Users(UserMixin, userDB.Model):
    id = userDB.Column(userDB.Integer, primary_key=True)
    forename = userDB.Column(userDB.String(250),
                         nullable=False)
    surname = userDB.Column(userDB.String(250),
                         nullable=False)
    email = userDB.Column(userDB.String(250), unique=True,
                         nullable=False)
    phone = userDB.Column(userDB.Integer(), unique=True,
                         nullable=False)
    password = userDB.Column(userDB.String(250),
                         nullable=False)
    type = userDB.Column(userDB.String(250), nullable=False)

 
 
# Initialize app with extension
userDB.init_app(app)
# Create database within app context
 
with app.app_context():
    userDB.create_all()

    # Check if Admin user exists and add it if not
    user = Users.query.filter_by(
                email = 'admin@wmgzon.com').first()
    if not user:
        user = Users(forename = 'Admin',
                        surname = 'Admin',
                        email = 'admin@wmgzon.com',
                        phone = 1234567890,
                        password = generate_password_hash('Admin123'),
                        type = "admin")
            
        # Add the user to the database
        userDB.session.add(user)
        # Commit the changes made
        userDB.session.commit()




connectInvDb = sqlite3.connect('inventory_database.db')
connectInvDb.execute(
    'CREATE TABLE IF NOT EXISTS TECHNOLOGY_PRODUCTS (id INTEGER PRIMARY KEY NOT NULL, name TEXT, brand TEXT, original_price REAL, current_price REAL, stock INT, subcategory TEXT, preview BLOB, description BLOB, specs BLOB, options BLOB, image_name TEXT)')
connectInvDb.execute(
   'DROP TABLE technology_basket')
connectInvDb.execute(
    'CREATE TABLE IF NOT EXISTS TECHNOLOGY_BASKET (id INTEGER PRIMARY KEY NOT NULL, productID INTEGER NOT NULL, quantity INTEGER NOT NULL, options STRING, FOREIGN KEY(productID) REFERENCES technology_products(id) )')
connectInvDb.close()

connectAuthDb = sqlite3.connect('auth_database.db')
connectAuthDb.execute(
    'CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY NOT NULL,forename TEXT, surname TEXT, email TEXT, phone INTEGER, password TEXT)')
connectAuthDb.close()


# Function to return a connection to the product database
def get_inventory_database():
    database = sqlite3.connect('inventory_database.db')
    database.row_factory = sqlite3.Row
    return database

# Function to take in a technology product ID and return the product details
def get_product(productId):
    database = get_inventory_database()
    post = database.execute('SELECT * FROM technology_products WHERE id = ?', (productId,)).fetchone()
    database.close()
    return post

# Function to return a connection to the auth database
def get_auth_database():
    database = sqlite3.connect('auth_database.db')
    database.row_factory = sqlite3.Row
    return database

# Function to take in a user ID and return the user details
def get_user(userId):
    database = get_inventory_database()
    post = database.execute('SELECT * FROM users WHERE id = ?', (userId,)).fetchone()
    database.close()
    if post is None:
        abort(404)
    return post

# Function to get the search results for a search query
def get_search_results(category, search_text):
    database = get_inventory_database()
    if(category=="technology" or category=="any_category"):
        data = database.execute('SELECT * FROM technology_products WHERE (name LIKE ?) OR (brand LIKE ?) OR (subcategory LIKE ?)',(search_text, search_text, search_text)).fetchall()
    else:
        data = ()
    return data

#Fetch the quantity of products grouped by product category
def get_product_levels():
    database = get_inventory_database()
    data = database.execute('SELECT subcategory, COUNT(ID) FROM technology_products GROUP BY subcategory').fetchall()
    return data

#Fetch the stock levels grouped by product category
def get_stock_levels():
    database = get_inventory_database()
    data = database.execute('SELECT subcategory, SUM(stock) FROM technology_products GROUP BY subcategory').fetchall()
    return data

#Fetch the stock levels for all products in a subcategory
def get_subcategory_stock_levels(subcategory):
    database = get_inventory_database()
    data = database.execute('SELECT name, stock FROM technology_products WHERE subcategory = ?',(subcategory,)).fetchall()
    return data

# Creates a user loader callback that returns the user object given an id
@login_manager.user_loader
def loader_user(user_id):
    return Users.query.get(user_id) 

# Set the login view to redirect to if user trys to access page while not logged in
login_manager.login_view = "login"



@app.route('/')
@app.route('/index/')
def index():
    return render_template('index.html')

@app.route('/login/', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect (url_for('index'))

    if request.method == 'POST':
        # Check if 'remember me' option was ticked
        if request.form.get('remember'):
            remember = True
        else:
            remember = False


        # Attempt to get matching user by email
        user = Users.query.filter_by(
            email = request.form['email']).first()
        
        # If matching user found then verify password
        if user:
            # Check if entered password matches database
            if check_password_hash(user.password, request.form['pword']):
                # Use the login_user method to log in the user
                login_user(user, remember=remember)
                return redirect(url_for("index"))
            else:
                # Return error message & reload page
                flash('Incorrect password','error')
                return redirect(url_for("login"))

        # Attempt to get matching user by phone
        user = Users.query.filter_by(
        phone = request.form['email']).first()

        # If matching user found then verify password
        if user:
            # Check if entered password matches database
            if check_password_hash(user.password, request.form['pword']):
                # Use the login_user method to log in the user
                login_user(user, remember=remember)
                return redirect(url_for("index"))
            else:
                # Return error message & reload page
                flash('Incorrect password','error')
                return redirect(url_for("login"))
            
        # If no user found, return error & reload page
        flash('Incorrect email/phone number','error')
        return redirect(url_for("login"))
    else:
        return render_template('login.html')
    
@app.route('/signup/', methods=['GET','POST'])
def signup():
    if current_user.is_authenticated:
        return redirect (url_for('index'))
    
    if request.method == 'POST':  
        user = Users(forename = request.form['forename'],
                     surname = request.form['surname'],
                     email = request.form['email'],
                     phone = request.form['phone'],
                     password = generate_password_hash(request.form['pword']),
                     type = "user")
        
        # Add the user to the database
        userDB.session.add(user)
        # Commit the changes made
        userDB.session.commit()

        flash('User added!')
        return redirect(url_for('login'))
    
        
    else:
        return render_template('signup.html')

@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route('/profile/', methods=('GET','POST'))
@login_required
def profile():

    if request.method == 'POST':
        # Get ID of current user
        id = current_user.id
        user = Users.query.get_or_404(id)

        user = current_user
        user.forename = request.form['forename']
        user.surname = request.form['surname']
        user.email = request.form['email']
        user.phone = request.form['phone']

        if(request.form['pword']):
            user.password = generate_password_hash(request.form['pword'])

        userDB.session.commit()

        flash('Profile updated!')
        return redirect(url_for("profile"))

    return render_template("profile.html")


@app.route('/basket/', methods=['GET','POST'])
def basket():
    if request.method == 'POST':
        productID = request.form['productID']
        productQuantity = 1

        basket = get_inventory_database()
        with basket:
            cursor = basket.cursor() 
            cursor.execute("INSERT INTO TECHNOLOGY_BASKET (productID, quantity) VALUES (?,?)", 
                           (productID, productQuantity,)) 
            basket.commit()          
        flash('Product added to basket!')
        return redirect(url_for('basket'))
    else:
        database = get_inventory_database()
        cursor = database.cursor() 
        cursor.execute('SELECT technology_basket.id, technology_basket.quantity, technology_products.name, technology_products.brand, technology_products.current_price, technology_products.image_name FROM TECHNOLOGY_BASKET INNER JOIN TECHNOLOGY_PRODUCTS ON technology_basket.productID=technology_products.ID')
        data = cursor.fetchall() 
        return render_template('basket.html', data=data)

@app.route('/search/', methods=['GET','POST'])
def search():
    if request.method == 'POST':     
        category = request.form['category']
        search_text = request.form['search_text']
        search_text = "%" + search_text + "%"
        print(category, search_text)

        data = get_search_results(category, search_text)
        return render_template('categories_technology_subcategory.html', data=data)
    
    else:
        return redirect(url_for('index'))




@app.route('/categories/technology/')
def categories_technology_home():
    database = get_inventory_database()
    cursor = database.cursor() 
    cursor.execute('SELECT * FROM TECHNOLOGY_PRODUCTS') 
  
    data = cursor.fetchall() 
    return render_template('categories_technology_home.html', data=data)

@app.route('/categories/technology/subcategory/<string:subcategory>/', methods=['GET','POST'])
def categories_technology_subcategory(subcategory):
    if request.method=='POST':
        sort = request.form['sort']
    else:
        sort = 'popularity'
    database = get_inventory_database()
    cursor = database.cursor() 
    print(subcategory)
    cursor.execute('SELECT * FROM TECHNOLOGY_PRODUCTS WHERE subcategory=?', (subcategory,))
    data = cursor.fetchall() 
    return render_template('categories_technology_subcategory.html', data=data, sort=sort)

@app.route('/categories/technology/product/<int:id>/') 
def categories_techology_product(id): 
    product = get_product(id)

    database = get_inventory_database()
    cursor = database.cursor() 
    subcategory = product[6]
    cursor.execute('SELECT * FROM TECHNOLOGY_PRODUCTS WHERE subcategory=?', (subcategory,))
    recommended = cursor.fetchall() 

    return render_template("categories_technology_product.html", data=product, recommended=recommended) 

@app.route('/categories/technology/add/', methods=['GET','POST'])
@login_required
def categories_technology_add():
    # Check user has admin privelages
    if not current_user.type == 'admin':
        flash('You do not have access to view this page')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        brand = request.form['brand']
        original_price = request.form['original_price']
        current_price = request.form['current_price']
        images = request.files['images']
        stock = request.form['stock']
        subcategory = request.form['subcategory']
        preview = request.form['preview']
        description = request.form['description']
        specs = request.form['specs']
        options = request.form['options']


        filename = ''.join(random.choice(string.ascii_letters) for i in range(10)) + ".png"
        images.save(os.path.join(app.root_path, 'static/assets/product_images', filename))

        products = get_inventory_database()
        with products:
            cursor = products.cursor() 
            cursor.execute("INSERT INTO TECHNOLOGY_PRODUCTS (name, brand, original_price, current_price, stock, subcategory, preview, description, specs, options, image_name) VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                           (name, brand, original_price, current_price, stock, subcategory, preview, description, specs, options, filename)) 
            products.commit()

            products.commit()               
        flash('Product added!')
        return redirect(url_for('categories_techology_manage'))
    else:
        return render_template('categories_technology_add.html', title='Add Product - Technology')


@app.route('/categories/technology/manage/') 
@login_required
def categories_techology_manage(): 
    # Check user has admin privelages
    if not current_user.type == 'admin':
        flash('You do not have access to view this page')
        return redirect(url_for('index'))

    database = get_inventory_database()
    cursor = database.cursor() 
    cursor.execute('SELECT * FROM TECHNOLOGY_PRODUCTS') 
    data = cursor.fetchall() 
    return render_template("categories_technology_manage.html", data=data) 

@app.route('/categories/technology/manage/<int:id>/', methods=('GET','POST'))
@login_required
def categories_techology_manage_id(id):
    # Check user has admin privelages
    if not current_user.type == 'admin':
        flash('You do not have access to view this page')
        return redirect(url_for('index'))

    product = get_product(id)

    if request.method == 'POST':
        name = request.form['name']
        brand = request.form['brand']
        original_price = request.form['original_price']
        current_price = request.form['current_price']
        images = request.files['images']
        stock = request.form['stock']
        subcategory = request.form['subcategory']
        preview = request.form['preview']
        description = request.form['description']
        specs = request.form['specs']
        options = request.form['options']

        

        database = get_inventory_database()
        if(images):
            filename = ''.join(random.choice(string.ascii_letters) for i in range(10)) + ".png"
            images.save(os.path.join(app.root_path, 'static/assets/product_images', filename))
            os.remove(os.path.join(app.root_path, 'static/assets/product_images', product[11]))
            database.execute('UPDATE TECHNOLOGY_PRODUCTS SET name=?, brand=?, original_price=?, current_price=?, stock=?, subcategory =?, preview=?, description=?, specs=?, options=?, image_name=? WHERE id = ?',
                            (name, brand, original_price, current_price, stock, subcategory, preview, description, specs, options, filename, id))
        else:
            database.execute('UPDATE TECHNOLOGY_PRODUCTS SET name=?, brand=?, original_price=?, current_price=?, stock=?, subcategory =?, preview=?, description=?, specs=?, options=? WHERE id = ?',
                            (name, brand, original_price, current_price, stock, subcategory, preview, description, specs, options, id))
        database.commit()
        database.close()
        flash('Product updated!')
        return render_template("categories_technology_manage_id.html", title='Edit Product - Technology', data = product)

    return render_template("categories_technology_manage_id.html", title='Edit Product - Technology', data = product)

@app.route('/categories/technology/manage/delete/<int:id>/', methods=("POST",))
@login_required
def categories_techology_manage_delete_id(id):
    # Check user has admin privelages
    if not current_user.type == 'admin':
        flash('You do not have access to view this page')
        return redirect(url_for('index'))

    product = get_product(id)
    database = get_inventory_database()
    os.remove(os.path.join(app.root_path, 'static/assets/product_images', product[11]))
    database.execute('DELETE FROM technology_products WHERE id = ?', (id,))
    database.commit()
    database.close()
    flash('"{}" was deleted!'.format(product['name']))
    
    return redirect(url_for('categories_techology_manage'))

@app.route('/categories/technology/stats/')
@login_required
def categories_technology_stats():
    # Check user has admin privelages
    if not current_user.type == 'admin':
        flash('You do not have access to view this page')
        return redirect(url_for('index'))

    data = get_product_levels()
    graph1Labels = [row[0] for row in data]
    graph1Content = [row[1] for row in data]

    data = get_stock_levels()
    graph2Labels = [row[0] for row in data]
    graph2Content = [row[1] for row in data]

    return render_template('categories_technology_stats.html', graph1Labels=graph1Labels, graph1Content=graph1Content, graph2Labels=graph2Labels, graph2Content=graph2Content)

@app.route('/categories/technology/stats/<string:subcategory>/')
@login_required
def categories_technology_stats_subcategory(subcategory):
    # Check user has admin privelages
    if not current_user.type == 'admin':
        flash('You do not have access to view this page')
        return redirect(url_for('index'))

    data = get_subcategory_stock_levels(subcategory)
    graphLabels = [row[0] for row in data]
    graphContent = [row[1] for row in data]

    return render_template('categories_technology_stats_subcategory.html', subcategory=subcategory, graphLabels=graphLabels, graphContent=graphContent)

@app.errorhandler(404) 
  
# inbuilt function which takes error as parameter 
def not_found(e): 
  
# defining function 
  return render_template("404.html") 

if __name__ == '__main__':
    app.run(debug=True)


