from flask import Flask, flash, render_template, request, abort, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from io import BytesIO
import sqlite3
import os
import random
import string

app = Flask(__name__)


#Set Secret Key
app.config['SECRET_KEY'] = "b'r\xca0\xd3Q\x80\x7f\x1ah\x14\xb9\xe3"




connectInvDb = sqlite3.connect('inventory_database.db')
connectInvDb.execute(
    'CREATE TABLE IF NOT EXISTS TECHNOLOGY_PRODUCTS (id INTEGER PRIMARY KEY NOT NULL,name TEXT, brand TEXT, original_price REAL, current_price REAL, stock INT, subcategory TEXT, preview BLOB, description BLOB, specs BLOB, options BLOB, image_name TEXT)')

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

        

    


@app.route('/')
@app.route('/index/')
def index():
    return render_template('index.html', title='Home')

@app.route('/login/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pword']
        #remember = True if request.form['remember'] else False

        database = get_auth_database()

        user = database.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user is None:
            user = database.execute('SELECT * FROM users WHERE phone = ?', (email,)).fetchone()
            if user is None:
                flash("No user found with that email/phone number")
                return redirect(url_for('login'))
        
        if not check_password_hash(user[5], password):
            flash("Password incorrect")
            return redirect(url_for('login'))

        return redirect(url_for('index'))
    else:
        return render_template('login.html', title='Login')
    
@app.route('/signup/', methods=['GET','POST'])
def signup():
    if request.method == 'POST':     
        forename = request.form['forename']
        surname = request.form['surname']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['pword']

        database = get_auth_database()
        with database:
            cursor = database.cursor() 
            cursor.execute("INSERT INTO users (forename, surname, email, phone, password) VALUES (?,?,?,?,?)", (forename, surname, email, phone, generate_password_hash(password))) 
            database.commit()
        flash('User added!')
        return redirect(url_for('login'))
    
        
    else:
        return render_template('signup.html', title='Signup')

@app.route('/basket/')
def basket():
    return render_template('basket.html', title='Basket')

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
        return render_template('categories_technology_manage.html')




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

    return render_template("categories_technology_product.html", data=product) 

@app.route('/categories/technology/add/', methods=['GET','POST'])
def categories_technology_add():
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
def categories_techology_manage(): 
    database = get_inventory_database()
    cursor = database.cursor() 
    cursor.execute('SELECT * FROM TECHNOLOGY_PRODUCTS') 
    data = cursor.fetchall() 
    return render_template("categories_technology_manage.html", data=data) 

@app.route('/categories/technology/manage/<int:id>/', methods=('GET','POST'))
def categories_techology_manage_id(id):
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

@app.route('/categories/technology/manage/delete/<int:id>', methods=("POST",))
def categories_techology_manage_delete_id(id):
    product = get_product(id)
    database = get_inventory_database()
    database.execute('DELETE FROM technology_products WHERE id = ?', (id,))
    database.commit()
    database.close()
    flash('"{}" was deleted!'.format(product['name']))
    
    return redirect(url_for('categories_techology_manage'))


@app.errorhandler(404) 
  
# inbuilt function which takes error as parameter 
def not_found(e): 
  
# defining function 
  return render_template("404.html") 

if __name__ == '__main__':
    app.run(debug=True)


