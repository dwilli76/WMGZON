from flask import Flask, render_template, flash, request, abort, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import random
import string

# Create flask app
app = Flask(__name__)

#Set Secret Key
app.config['SECRET_KEY'] = "b'r\xca0\xd3Q\x80\x7f\x1ah\x14\xb9\xe3"

# Tells flask-sqlalchemy what database to connect to for user profiles
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"

# Initialize flask-sqlalchemy extension for the user database
userDB = SQLAlchemy()

# Setup login manager to handle logging in/out users
login_manager = LoginManager()
login_manager.init_app(app)

# Create SQLAlchemy user model
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

    # Check if default Admin user exists and add it if not
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

# Setup the inventory database
connectInvDb = sqlite3.connect('inventory_database.db')
# If the products table doesn't exist then create
connectInvDb.execute(
    'CREATE TABLE IF NOT EXISTS TECHNOLOGY_PRODUCTS \
    (id INTEGER PRIMARY KEY NOT NULL, name TEXT, brand TEXT, original_price REAL, current_price REAL, \
    stock INT, subcategory TEXT, preview BLOB, description BLOB, specs BLOB, options BLOB, image_name TEXT)')
# Drop any existing stored basket information then re-create the basket table
connectInvDb.execute(
    'DROP TABLE technology_basket')
connectInvDb.execute(
    'CREATE TABLE IF NOT EXISTS TECHNOLOGY_BASKET \
    (id INTEGER PRIMARY KEY NOT NULL, productID INTEGER NOT NULL, quantity INTEGER NOT NULL, \
    options STRING, FOREIGN KEY(productID) REFERENCES technology_products(id) )')
connectInvDb.close()

# Function to return a connection to the inventory database
def get_inventory_database():
    database = sqlite3.connect('inventory_database.db')
    database.row_factory = sqlite3.Row
    return database

# Function to take in a technology product ID and return the product details
def get_product(productId):
    database = get_inventory_database()
    product = database.execute('SELECT * FROM technology_products WHERE id = ?', (productId,)).fetchone()
    database.close()
    return product

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

# Define where to redirect the user to if they attempt to access a restricted page while not logged in
login_manager.login_view = "login"


#------------ROUTES------------

# Define the home route
@app.route('/')
@app.route('/index/')
@app.route('/home/')
def home():
    return render_template('index.html')

# Define the login route
@app.route('/login/', methods=['GET','POST'])
def login():
    # If the user is already logged in then redirect them to 'home'
    if current_user.is_authenticated:
        return redirect (url_for('home'))

    # If the request is posting the login details
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
                return redirect(url_for("home"))
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
                return redirect(url_for("home"))
            else:
                # Return error message & reload page
                flash('Incorrect password','error')
                return redirect(url_for("login"))
            
        # If no user found, return error & reload page
        flash('Incorrect email/phone number','error')
        return redirect(url_for("login"))
    else:
        return render_template('login.html')
    
# Define the signup route
@app.route('/signup/', methods=['GET','POST'])
def signup():
    # If the user is already logged in then redirect them to 'home'
    if current_user.is_authenticated:
        return redirect (url_for('home'))
    
    # If the request is posting the signup details
    if request.method == 'POST':
        # Create a new user object from the model
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

        # Display a confirmation message & redirect to 'login' page
        flash('User added!')
        return redirect(url_for('login'))
    else:
        return render_template('signup.html')

# Define the logout route
@app.route("/logout/")
@login_required
def logout():
    # Logout the current user and redirect them to 'home'
    logout_user()
    return redirect(url_for("home"))

# Define the profile route
@app.route('/profile/', methods=('GET','POST'))
@login_required
def profile():

    # If the request is posting the updated user details
    if request.method == 'POST':
        # Get ID of current user
        id = current_user.id
        user = Users.query.get_or_404(id)

        user = current_user

        # Update the details to match the submitted data
        user.forename = request.form['forename']
        user.surname = request.form['surname']
        user.email = request.form['email']
        user.phone = request.form['phone']

        # If a new password was submitted then use that
        if(request.form['pword']):
            user.password = generate_password_hash(request.form['pword'])

        # Commit the changes
        userDB.session.commit()

        # Display a confirmation message and redirect to 'profile'
        flash('Profile updated!')
        return redirect(url_for("profile"))

    return render_template("profile.html")

# Define the basket route
@app.route('/basket/', methods=['GET','POST'])
def basket():
    # If the request is posting a product to the basket
    if request.method == 'POST':
        # Get the product ID from the request
        productID = request.form['productID']
        # Set a predefined quantity for the product (temporary functionality)
        productQuantity = 1
        # Declare a string for the product options and append each selected option
        productOptions = ""
        for value in request.form:
            print(value)
            if value.startswith("option_"):
                productOptions = productOptions + request.form[value] + ", "

        # Get the database connection
        database = get_inventory_database()
        with database:
            # Insert the product selection into the technology_basket table
            cursor = database.cursor() 
            cursor.execute("INSERT INTO TECHNOLOGY_BASKET (productID, quantity, options) VALUES (?,?,?)", 
                           (productID, productQuantity,productOptions,)) 
            # Commit changes to the database
            database.commit()
        # Display a confirmation message and redirect to the 'basket' page      
        flash('Product added to basket!')
        return redirect(url_for('basket'))
    else:
        # Get the database connection
        database = get_inventory_database()
        cursor = database.cursor() 
        # Fetch all of the product data & basket data for each product in the technology_basket table
        cursor.execute('SELECT technology_basket.id, technology_basket.quantity, technology_products.name, technology_products.brand, technology_products.current_price, technology_products.image_name, technology_basket.options FROM TECHNOLOGY_BASKET INNER JOIN TECHNOLOGY_PRODUCTS ON technology_basket.productID=technology_products.ID')
        data = cursor.fetchall() 
        # Render the basket template with the data
        return render_template('basket.html', data=data)

# Define the search route
@app.route('/search/', methods=['GET','POST'])
def search():
    # If the request is posting search query
    if request.method == 'POST':     
        # Get the subcategory and search term from the request
        category = request.form['category']
        search_text = request.form['search_text']
        # Append character to the search text to allow for non-exact results
        search_text = "%" + search_text + "%"

        # Uses a function to query the database and return the results
        data = get_search_results(category, search_text)
        # Render the results using the search template
        return render_template('search.html', data=data)
    else:
        # If a user navigates to '/search' then redirect them to home
        return redirect(url_for('home'))

# Define the technology homepage route
@app.route('/categories/technology/')
def categories_technology_home():
    # Establish connection with the database
    database = get_inventory_database()
    cursor = database.cursor() 
    # Select all products from the database
    cursor.execute('SELECT * FROM TECHNOLOGY_PRODUCTS') 
    data = cursor.fetchall() 
    # Render the results using the technology homepage template
    return render_template('categories_technology_home.html', data=data)

# Define the technology subcategory browse route
# Route endpoint contains a variable to utilise a single route for multiple pages
# (One page for each subcategory)
@app.route('/categories/technology/subcategory/<string:subcategory>/', methods=['GET','POST'])
def categories_technology_subcategory(subcategory):
    # Set pre-defined sort/filter parameters
    filters = ['popular',0,1000000,'no']

    # If the request is posting sort/filter information then update the parameters
    if request.method=='POST':
        filters[0] = request.form['sort']
        filters[1] = request.form['min_price']
        filters[2] = request.form['max_price']
        if request.form.get('in_stock'):
            filters[3] = 'yes'
        else:
            filters[3] = 'no'

    # If filtering for in stock then set a min-stock variable to 1
    if filters[3] == 'yes':
        min_stock = 1
    else:
        min_stock = 0

    # Get an SQL query based on the sort selected
    if filters[0] == "popular":
        db_query = "SELECT * FROM TECHNOLOGY_PRODUCTS WHERE \
            subcategory=? AND current_price>? AND current_price<? AND stock >=? ORDER BY stock DESC"
    elif filters[0] == "price_low_high":
        db_query = "SELECT * FROM TECHNOLOGY_PRODUCTS WHERE \
            subcategory=? AND current_price>? AND current_price<? AND stock >=? ORDER BY current_price ASC"
    elif filters[0] == "price_high_low":
        db_query = "SELECT * FROM TECHNOLOGY_PRODUCTS WHERE \
            subcategory=? AND current_price>? AND current_price<? AND stock >=? ORDER BY current_price DESC"

    # Execute the query and fetch all results
    database = get_inventory_database()
    cursor = database.cursor() 
    cursor.execute(db_query, (subcategory, filters[1], filters[2], min_stock,))
    data = cursor.fetchall() 

    # Return the results in the subcategory template
    return render_template('categories_technology_subcategory.html', data=data, filters=filters)

# Define the technology product route
# Route endpoint contains a variable to utilise a single route for multiple pages
# (One page for each product)
@app.route('/categories/technology/product/<int:id>/') 
def categories_techology_product(id):
    # Get the product data from the database
    product = get_product(id)

    # Get a list of recommended products (same subcategory) from the database
    database = get_inventory_database()
    cursor = database.cursor() 
    subcategory = product[6]
    cursor.execute('SELECT * FROM TECHNOLOGY_PRODUCTS WHERE subcategory=?', (subcategory,))
    recommended = cursor.fetchall() 

    # Return the product page template
    return render_template("categories_technology_product.html", data=product, recommended=recommended) 

# Define the add technology product route
@app.route('/categories/technology/add/', methods=['GET','POST'])
#@login_required
def categories_technology_add():
    # Check user has admin privelages, if not redirect to 'home' with error
    # if not current_user.type == 'admin':
    #     flash('You do not have access to view this page')
    #     return redirect(url_for('home'))

    # If the request is posting product data
    if request.method == 'POST':
        # Extract the data from the request
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

        # Generate a random filename for the product image & save to the 'product_images' folder
        filename = ''.join(random.choice(string.ascii_letters) for i in range(10)) + ".png"
        images.save(os.path.join(app.root_path, 'static/assets/product_images', filename))

        # Get the product database
        database = get_inventory_database()
        # Insert the product data into the database and commit the changes
        with database:
            cursor = database.cursor() 
            cursor.execute("INSERT INTO TECHNOLOGY_PRODUCTS (name, brand, original_price, current_price, stock, subcategory, preview, description, specs, options, image_name) VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                           (name, brand, original_price, current_price, stock, subcategory, preview, description, specs, options, filename)) 
            database.commit()
        
        # Display confirmation message and redirect to the technology manage page
        flash('Product added!')
        return redirect(url_for('categories_techology_manage'))
    else:
        return render_template('categories_technology_add.html')

# Define the manage technology products route
@app.route('/categories/technology/manage/') 
@login_required
def categories_techology_manage(): 
    # Check user has admin privelages, if not redirect to 'home' with error
    if not current_user.type == 'admin':
        flash('You do not have access to view this page')
        return redirect(url_for('home'))

    # Get connection to the database & fetch all products
    database = get_inventory_database()
    cursor = database.cursor() 
    cursor.execute('SELECT * FROM TECHNOLOGY_PRODUCTS') 
    data = cursor.fetchall() 
    # Return the data in the technology manage template
    return render_template("categories_technology_manage.html", data=data) 

# Define the manage technology product route
# Route endpoint contains a variable to utilise a single route for multiple pages
# (One page for each product)
@app.route('/categories/technology/manage/<int:id>/', methods=('GET','POST'))
@login_required
def categories_techology_manage_id(id):
    # Check user has admin privelages, if not redirect to 'home' with error
    if not current_user.type == 'admin':
        flash('You do not have access to view this page')
        return redirect(url_for('home'))

    # Get the product data using the ID
    product = get_product(id)

    # If request is posting updated product data
    if request.method == 'POST':
        # Extract the data from the request
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

        # Get connection to the database
        database = get_inventory_database()

        # If a new image was uploaded
        if(images):
            # Generate a random filename for the new image and save to product_images folder
            filename = ''.join(random.choice(string.ascii_letters) for i in range(10)) + ".png"
            images.save(os.path.join(app.root_path, 'static/assets/product_images', filename))
            # Delete the previous product image
            os.remove(os.path.join(app.root_path, 'static/assets/product_images', product[11]))
            # Update all parameters including image name
            database.execute('UPDATE TECHNOLOGY_PRODUCTS SET name=?, brand=?, original_price=?, current_price=?, stock=?, subcategory =?, preview=?, description=?, specs=?, options=?, image_name=? WHERE id = ?',
                            (name, brand, original_price, current_price, stock, subcategory, preview, description, specs, options, filename, id))
        else:
            # Update all parameters excluding image name
            database.execute('UPDATE TECHNOLOGY_PRODUCTS SET name=?, brand=?, original_price=?, current_price=?, stock=?, subcategory =?, preview=?, description=?, specs=?, options=? WHERE id = ?',
                            (name, brand, original_price, current_price, stock, subcategory, preview, description, specs, options, id))
        # Commit changes to the database
        database.commit()
        database.close()

        # Diaplay a confirmation message and reload the page
        flash('Product updated!')
        return redirect(url_for('categories_techology_manage_id', id=id))

    # Return product data in manage product template
    return render_template("categories_technology_manage_id.html", data = product)

# Define the delete technology product route
# Route endpoint contains a variable to utilise a single route for multiple pages
# (One page for each product)
@app.route('/categories/technology/manage/delete/<int:id>/', methods=("POST",))
@login_required
def categories_techology_manage_delete_id(id):
    # Check user has admin privelages, if not redirect to 'home' with error
    if not current_user.type == 'admin':
        flash('You do not have access to view this page')
        return redirect(url_for('home'))

    # Fetch the product using its ID
    product = get_product(id)

    # Delete the product image
    os.remove(os.path.join(app.root_path, 'static/assets/product_images', product[11]))

    # Get connection to the database and delete the product
    database = get_inventory_database()
    database.execute('DELETE FROM technology_products WHERE id = ?', (id,))

    # Commit changes to the database
    database.commit()
    database.close()

    # Alert the user and redirect to the manage products page
    flash('"{}" was deleted!'.format(product['name']))
    return redirect(url_for('categories_techology_manage'))

# Define the technology stats route
@app.route('/categories/technology/stats/')
@login_required
def categories_technology_stats():
    # Check user has admin privelages, if not redirect to 'home' with error
    if not current_user.type == 'admin':
        flash('You do not have access to view this page')
        return redirect(url_for('home'))

    # Get the quantity of products by subcategory
    data = get_product_levels()
    # Split the data into an array for graph labels and an array for graph data
    graph1Labels = [row[0] for row in data]
    graph1Content = [row[1] for row in data]

    # Get the overall stock level by subcategory
    data = get_stock_levels()
    # Split the data into an array for graph labels and an array for graph data
    graph2Labels = [row[0] for row in data]
    graph2Content = [row[1] for row in data]

    # Return the data in the technology stats template
    return render_template('categories_technology_stats.html', graph1Labels=graph1Labels, graph1Content=graph1Content, graph2Labels=graph2Labels, graph2Content=graph2Content)

# Define the subcategory stats route
# Route endpoint contains a variable to utilise a single route for multiple pages
# (One page for each subcategory)
@app.route('/categories/technology/stats/<string:subcategory>/')
@login_required
def categories_technology_stats_subcategory(subcategory):
    # Check user has admin privelages, if not redirect to 'home' with error
    if not current_user.type == 'admin':
        flash('You do not have access to view this page')
        return redirect(url_for('home'))

    # Get the stock levels of each product in the subcategory
    data = get_subcategory_stock_levels(subcategory)
    # Split the data into an array for graph labels and an array for graph data
    graphLabels = [row[0] for row in data]
    graphContent = [row[1] for row in data]

    # Return the data in the technology subcategory stats template
    return render_template('categories_technology_stats_subcategory.html', subcategory=subcategory, graphLabels=graphLabels, graphContent=graphContent)

# Create a catch-all route for any unknown endpoints
@app.errorhandler(404) 
# inbuilt function which takes error as parameter 
def not_found(e): 
# defining function 
    return render_template("404.html"), 404 


# Build & run the app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')


