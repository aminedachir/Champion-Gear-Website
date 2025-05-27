from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import os
from flask import request, jsonify

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

def recreate_referees_table():
    """Recreate the referees table with the correct schema"""
    conn = sqlite3.connect('karate_dojo.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referees'")
    table_exists = c.fetchone()
    
    if table_exists:
        c.execute("PRAGMA table_info(referees)")
        columns = [col[1] for col in c.fetchall()]
        required_columns = ['user_type', 'club_name', 'wilaya', 'role_option']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"Missing columns: {missing_columns}. Recreating table...")
            c.execute("SELECT * FROM referees")
            existing_data = c.fetchall()
            c.execute("DROP TABLE referees")
            
            c.execute('''CREATE TABLE referees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_type TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                club_name TEXT,
                wilaya TEXT,
                role_option TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            for row in existing_data:
                try:
                    c.execute('''INSERT INTO referees 
                               (id, user_type, username, email, password, full_name, created_at) 
                               VALUES (?, ?, ?, ?, ?, ?, ?)''',
                            (row[0], 'referee', row[1], row[2], row[3], row[4], 
                             row[5] if len(row) > 5 else datetime.now()))
                except Exception as e:
                    print(f"Error restoring data: {e}")
            
            print("Table recreated successfully!")
    else:
        c.execute('''CREATE TABLE referees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_type TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            club_name TEXT,
            wilaya TEXT,
            role_option TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        print("New referees table created!")
    
    conn.commit()
    conn.close()

def init_db_organizations():
    """Update organizations table to handle new structure"""
    conn = sqlite3.connect('karate_dojo.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='organizations'")
    table_exists = c.fetchone()
    
    if table_exists:
        c.execute("PRAGMA table_info(organizations)")
        columns = [col[1] for col in c.fetchall()]
        
        required_columns = ['wilaya', 'president_name', 'president_phone']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"Missing columns in organizations table: {missing_columns}. Recreating table...")
            c.execute("SELECT * FROM organizations")
            existing_data = c.fetchall()
            c.execute("DROP TABLE organizations")
            c.execute('''CREATE TABLE organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password TEXT,
                org_name TEXT NOT NULL,
                org_type TEXT NOT NULL,
                wilaya TEXT,
                president_name TEXT,
                president_phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            for row in existing_data:
                try:
                    c.execute('''INSERT INTO organizations 
                               (id, username, email, password, org_name, org_type, created_at) 
                               VALUES (?, ?, ?, ?, ?, ?, ?)''',
                            (row[0], row[1], row[2], row[3], row[4], row[5], 
                             row[6] if len(row) > 6 else datetime.now()))
                except Exception as e:
                    print(f"Error restoring organization data: {e}")
            
            print("Organizations table recreated successfully!")
    else:
        c.execute('''CREATE TABLE organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT,
            org_name TEXT NOT NULL,
            org_type TEXT NOT NULL,
            wilaya TEXT,
            president_name TEXT,
            president_phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        print("New organizations table created!")
    
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect('karate_dojo.db')
    c = conn.cursor()
    conn.close() 
    recreate_referees_table()
    init_db_organizations()  
    conn = sqlite3.connect('karate_dojo.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  description TEXT,
                  price REAL NOT NULL,
                  category TEXT NOT NULL,
                  image_url TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS workshops
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  description TEXT,
                  instructor TEXT NOT NULL,
                  date TEXT NOT NULL,
                  time TEXT NOT NULL,
                  duration TEXT NOT NULL,
                  max_participants INTEGER,
                  price REAL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()
    add_sample_products()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/shop')
def shop():
    conn = sqlite3.connect('karate_dojo.db')
    c = conn.cursor()
    c.execute('SELECT id, name, description, price, category, image_url FROM products')
    products = c.fetchall()
    conn.close()

    categories = {}
    for product in products:
        category = product[4] 
        if category not in categories:
            categories[category] = []
        categories[category].append(product)
    
    return render_template('shop.html', categories=categories)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = sqlite3.connect('karate_dojo.db')
    c = conn.cursor()
    c.execute('SELECT id, name, description, price, category, image_url FROM products WHERE id = ?', (product_id,))
    product = c.fetchone()
    conn.close()

    if product:
        return render_template('product_detail.html', product=product)
    else:
        return "المنتج غير موجود", 404

@app.route('/workshops')
def workshops():
    conn = sqlite3.connect('karate_dojo.db')
    c = conn.cursor()
    c.execute('SELECT * FROM workshops ORDER BY date, time')
    workshops = c.fetchall()
    conn.close()
    return render_template('workshops.html', workshops=workshops)

@app.route('/login/referee')
def referee_login():
    return render_template('referee_login.html')

@app.route('/login/referee', methods=['POST'])
def referee_login_post():
    username = request.form['username']
    password = request.form['password']
    
    conn = sqlite3.connect('karate_dojo.db')
    c = conn.cursor()
    c.execute('SELECT * FROM referees WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    
    if user and check_password_hash(user[4], password): 
        session['user_id'] = user[0]
        session['user_type'] = 'referee'
        session['username'] = user[2]  
        flash('تم تسجيل الدخول بنجاح!', 'success')
        return redirect(url_for('home'))
    else:
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
        return redirect(url_for('referee_login'))

@app.route('/signup/referee')
def referee_signup():
    return render_template('referee_signup.html')

@app.route('/signup/referee', methods=['POST'])
def referee_signup_post():
    full_name = request.form['full_name']
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    user_type = request.form['user_type']
    club_name = request.form['club_name']
    wilaya = request.form['wilaya']
    role_option = request.form['role_option']

    if password != confirm_password:
        flash('كلمة المرور غير متطابقة', 'error')
        return redirect(url_for('referee_signup'))

    hashed_password = generate_password_hash(password)

    try:
        conn = sqlite3.connect('karate_dojo.db')
        c = conn.cursor()
        c.execute('''INSERT INTO referees (
                        user_type, username, email, password,
                        full_name, club_name, wilaya, role_option
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (user_type, username, email, hashed_password,
                   full_name, club_name, wilaya, role_option))
        conn.commit()
        conn.close()
        flash('تم إنشاء الحساب بنجاح!', 'success')
        return redirect(url_for('referee_login'))
    except sqlite3.IntegrityError:
        flash('اسم المستخدم أو البريد الإلكتروني مستخدم بالفعل', 'error')
        return redirect(url_for('referee_signup'))

@app.route('/login/organization')
def organization_login():
    return render_template('organization_login.html')

@app.route('/login/organization', methods=['POST'])
def organization_login_post():
    username = request.form['username']
    password = request.form['password']
    
    conn = sqlite3.connect('karate_dojo.db')
    c = conn.cursor()
    c.execute('SELECT * FROM organizations WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    
    if user and check_password_hash(user[3], password):
        session['user_id'] = user[0]
        session['user_type'] = 'organization'
        session['username'] = user[1]
        flash('تم تسجيل الدخول بنجاح!', 'success')
        return redirect(url_for('home'))
    else:
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
        return redirect(url_for('organization_login'))

@app.route('/signup/organization')
def organization_signup():
    return render_template('organization_signup.html')

@app.route('/signup/organization', methods=['POST'])
def organization_signup_post():
    org_type = request.form['org_type']
    
    if org_type == 'رابطة':
        org_name = request.form['rabita_name']
        username = request.form['rabita_username']
        password = request.form['rabita_password']
        confirm_password = request.form['rabita_confirm_password']
        email = None
        wilaya = None
        president_name = None
        president_phone = None
        
        if password != confirm_password:
            flash('كلمة المرور غير متطابقة', 'error')
            return redirect(url_for('organization_signup'))
            
    elif org_type == 'نادي':
        org_name = request.form['nadi_name']
        wilaya = request.form['wilaya']
        president_name = request.form['president_name']
        email = request.form['club_email']
        president_phone = request.form['president_phone']
        username = None
        password = None
        
        import re
        phone_pattern = r'^[0-9]{10}$'
        if not re.match(phone_pattern, president_phone):
            flash('رقم الهاتف غير صحيح. يجب أن يكون 10 أرقام', 'error')
            return redirect(url_for('organization_signup'))
            
        if not (president_phone.startswith('05') or president_phone.startswith('06') or president_phone.startswith('07')):
            flash('رقم الهاتف يجب أن يبدأ بـ 05 أو 06 أو 07', 'error')
            return redirect(url_for('organization_signup'))
    
    else:
        flash('نوع المنظمة غير صحيح', 'error')
        return redirect(url_for('organization_signup'))
    
    hashed_password = generate_password_hash(password) if password else None
    
    try:
        conn = sqlite3.connect('karate_dojo.db')
        c = conn.cursor()
        c.execute('''INSERT INTO organizations 
                     (username, email, password, org_name, org_type, wilaya, president_name, president_phone) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (username, email, hashed_password, org_name, org_type, wilaya, president_name, president_phone))
        conn.commit()
        conn.close()
        
        if org_type == 'رابطة':
            flash('تم إنشاء حساب الرابطة بنجاح!', 'success')
        else:
            flash('تم تسجيل النادي بنجاح! سيتم مراجعة طلبكم والتواصل معكم قريباً', 'success')
            
        return redirect(url_for('organization_login'))
        
    except sqlite3.IntegrityError as e:
        if 'username' in str(e):
            flash('اسم المستخدم مستخدم بالفعل', 'error')
        elif 'email' in str(e):
            flash('البريد الإلكتروني مستخدم بالفعل', 'error')
        else:
            flash('خطأ في إنشاء الحساب. يرجى المحاولة مرة أخرى', 'error')
        return redirect(url_for('organization_signup'))
    except Exception as e:
        flash('حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى', 'error')
        return redirect(url_for('organization_signup'))
    
@app.route('/cart')
def cart():
    if 'cart' not in session:
        session['cart'] = {}
    
    cart_items = []
    subtotal = 0
    
    conn = sqlite3.connect('karate_dojo.db')
    c = conn.cursor()
    
    for product_id, quantity in session['cart'].items():
        c.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        product = c.fetchone()
        if product:
            print("Product Data:", product)  
            item = {
                'id': product[0],
                'name': product[1],
                'description': product[2],
                'price': product[3],
                'image': product[5],
                'quantity': quantity
            }
            cart_items.append(item)
            subtotal += product[3] * quantity
    
    conn.close()
    
    shipping = 10.00 if subtotal > 0 else 0
    total = subtotal + shipping
    
    return render_template('cart.html', 
                         cart_items=cart_items,
                         subtotal=subtotal,
                         shipping=shipping,
                         total=total,
                         today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/update_cart', methods=['POST'])
def update_cart():
    data = request.get_json()
    product_id = str(data['product_id'])
    quantity_change = data['quantity_change']
    
    if 'cart' not in session:
        session['cart'] = {}
    
    if product_id in session['cart']:
        new_quantity = session['cart'][product_id] + quantity_change
        if new_quantity > 0:
            session['cart'][product_id] = new_quantity
        else:
            session['cart'].pop(product_id)
    else:
        if quantity_change > 0:
            session['cart'][product_id] = quantity_change
    
    session.modified = True
    return jsonify({
        'success': True,
        'count': sum(session['cart'].values())
    })

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    product_id = str(data['product_id'])
    
    if 'cart' in session and product_id in session['cart']:
        session['cart'].pop(product_id)
        session.modified = True
    
    return jsonify({
        'success': True,
        'count': sum(session.get('cart', {}).values())
    })

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'message': 'You need to be logged in to add items to your cart',
            'login_required': True
        })
    
    data = request.get_json()
    product_id = str(data['product_id'])
    
    if 'cart' not in session:
        session['cart'] = {}
    
    if product_id in session['cart']:
        session['cart'][product_id] += 1
    else:
        session['cart'][product_id] = 1
    
    session.modified = True
    total_items = sum(session['cart'].values())
    
    return jsonify({
        'success': True,
        'count': total_items
    })

@app.route('/get_cart')
def get_cart():
    cart = session.get('cart', {})
    total_items = sum(cart.values())
    return jsonify({
        'success': True,
        'count': total_items,
        'cart': cart
    })

def add_sample_products():
    conn = sqlite3.connect('karate_dojo.db')
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM products')
    count = c.fetchone()[0]
    
    if count == 0:
        products = [
            (1, 'تلفاز حجم كبير', 'Professional large screen display for VAR review - الكمية: 16', 1299.99, 'VAR Equipment', 'large-tv.png'),
            (2, 'تلفاز حجم متوسط', 'Medium size display for referee stations - الكمية: 8', 899.99, 'VAR Equipment', 'medium-tv.png'),
            (3, 'لوحات إلكترونية', 'Digital scoreboard systems for competitions - الكمية: 40', 699.99, 'VAR Equipment', 'scoreboard.png'),
            (4, 'أجهزة تحكم احمر', 'Specialized red referee control units (غير متوفرة في السوق المحلي) - الكمية: 32', 299.99, 'VAR Equipment', 'red-control.png'),
            (5, 'أجهزة تحكم ازرق', 'Specialized blue referee control units (غير متوفرة في السوق المحلي) - الكمية: 32', 299.99, 'VAR Equipment', 'blue-control.png'),
            (6, 'كاميرات خاصة VAR', 'Professional VAR cameras for match recording (غير متوفرة في السوق المحلية) - الكمية: 32', 1899.99, 'VAR Equipment', 'var-camera.png'),
            (7, 'برنامج', 'Professional VAR analysis software (غير متوفر في السوق المحلية) - Custom licensing', 4999.99, 'Software & Accessories', 'software.png'),
            (8, 'حاسوب', 'High-performance computer for VAR operations - الكمية: 8', 1499.99, 'Software & Accessories', 'computer.png'),
            (9, 'سماعات رأس', 'Communication headsets for referees - الكمية: 8', 199.99, 'Software & Accessories', 'headset.png'),
            (10, 'أجهزة ربط بين العتاد (كابل)', 'Professional connection cables for VAR equipment - الكمية: 46', 49.99, 'Software & Accessories', 'cables.png'),
            (11, 'أجهزة ربط مع الكهرباء', 'Electrical connection adapters for equipment - الكمية: 20', 79.99, 'Software & Accessories', 'power-adapter.png'),
            (12, 'طاولة', 'Referee station tables - الكمية: 8', 299.99, 'Referee Furniture', 'table.png'),
            (13, 'كراسي', 'Ergonomic chairs for referee stations - الكمية: 56', 149.99, 'Referee Furniture', 'chair.png')
        ]
        
        for product in products:
            c.execute('INSERT OR REPLACE INTO products (id, name, description, price, category, image_url) VALUES (?, ?, ?, ?, ?, ?)', product)
    
    conn.commit()
    conn.close()
    

@app.route('/process_order', methods=['POST'])
def process_order():
    if 'user_id' not in session or 'user_type' not in session:
        flash('يجب تسجيل الدخول لإتمام الطلب', 'error')
        return redirect(url_for('referee_login'))

    shipping_address = request.form.get('shipping_address')
    phone = request.form.get('phone')
    alternative_phone = request.form.get('alternative_phone')
    delivery_notes = request.form.get('delivery_notes')
    payment_method = request.form.get('payment_method')

    if not all([shipping_address, phone]):
        flash('يرجى ملء جميع الحقول المطلوبة', 'error')
        return redirect(url_for('checkout'))

    try:
        conn = sqlite3.connect('karate_dojo.db')
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS orders
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER NOT NULL,
                     user_type TEXT NOT NULL,
                     order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     shipping_address TEXT NOT NULL,
                     phone TEXT NOT NULL,
                     alternative_phone TEXT,
                     delivery_notes TEXT,
                     payment_method TEXT NOT NULL,
                     subtotal REAL NOT NULL,
                     shipping REAL NOT NULL,
                     total REAL NOT NULL,
                     status TEXT DEFAULT 'pending')''')  

        c.execute('''CREATE TABLE IF NOT EXISTS order_items
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     order_id INTEGER NOT NULL,
                     product_id INTEGER NOT NULL,
                     product_name TEXT NOT NULL,
                     quantity INTEGER NOT NULL,
                     price REAL NOT NULL)''')

        subtotal = 0
        cart_items = []

        if 'cart' in session:
            for product_id, quantity in session['cart'].items():
                c.execute('SELECT id, name, price FROM products WHERE id = ?', (product_id,))
                product = c.fetchone()
                if product:
                    item_total = product[2] * quantity
                    subtotal += item_total
                    cart_items.append({
                        'id': product[0],
                        'name': product[1],
                        'price': product[2],
                        'quantity': quantity
                    })

        shipping = 10.00 if subtotal > 0 else 0
        total = subtotal + shipping

        print("=== Preparing to insert order ===")
        print(f"user_id: {session['user_id']}")
        print(f"user_type: {session['user_type']}")
        print(f"subtotal: {subtotal}, shipping: {shipping}, total: {total}")
        print(f"Address: {shipping_address}, Phone: {phone}, Payment: {payment_method}")

        c.execute('''INSERT INTO orders 
                    (user_id, user_type, shipping_address, phone, alternative_phone, 
                     delivery_notes, payment_method, subtotal, shipping, total)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (session['user_id'], session['user_type'], shipping_address, phone, 
                  alternative_phone, delivery_notes, payment_method, subtotal, shipping, total))

        order_id = c.lastrowid

        for item in cart_items:
            c.execute('''INSERT INTO order_items 
                        (order_id, product_id, product_name, quantity, price)
                        VALUES (?, ?, ?, ?, ?)''',
                     (order_id, item['id'], item['name'], item['quantity'], item['price']))

        conn.commit()
        session.pop('cart', None)
        return redirect(url_for('order_confirmation', order_id=order_id))

    except Exception as e:
        conn.rollback()
        flash('حدث خطأ أثناء معالجة الطلب. يرجى المحاولة مرة أخرى', 'error')
        print("=== Error during order processing ===")
        traceback.print_exc()
        return redirect(url_for('checkout'))
    finally:
        conn.close()

@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    try:
        if 'user_id' not in session:
            flash('يجب تسجيل الدخول لعرض تأكيد الطلب', 'error')
            return redirect(url_for('referee_login'))

        conn = sqlite3.connect('karate_dojo.db')
        c = conn.cursor()
        c.execute('''SELECT o.* FROM orders o 
                    WHERE o.id = ? AND o.user_id = ?''', 
                 (order_id, session['user_id']))
        order = c.fetchone()
        if not order:
            print(f"الطلب {order_id} غير موجود أو لا ينتمي للمستخدم")
            flash('الطلب غير موجود أو ليس لديك صلاحية لعرضه', 'error')
            return redirect(url_for('home'))
        c.execute('SELECT * FROM order_items WHERE order_id = ?', (order_id,))
        items = c.fetchall()
        return render_template('order_confirmation.html', 
                            order=order,
                            items=items,
                            order_id=order_id)
    except Exception as e:
        print(f"خطأ في عرض تأكيد الطلب: {str(e)}")
        flash('حدث خطأ في عرض تفاصيل الطلب', 'error')
        return redirect(url_for('home'))
    finally:
        conn.close()

@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        flash('يجب تسجيل الدخول لإتمام الطلب', 'error')
        return redirect(url_for('referee_login'))
    
    if 'cart' not in session or not session['cart']:
        flash('سلة التسوق فارغة', 'error')
        return redirect(url_for('shop'))
    conn = sqlite3.connect('karate_dojo.db')
    c = conn.cursor()
    if session['user_type'] == 'referee':
        c.execute('SELECT * FROM referees WHERE id = ?', (session['user_id'],))
        user = c.fetchone()
        user_dict = {
            'id': user[0],
            'user_type': user[1],
            'username': user[2],
            'email': user[3],
            'full_name': user[5],
            'club_name': user[6],
            'wilaya': user[7]
        }
    else:
        c.execute('SELECT * FROM organizations WHERE id = ?', (session['user_id'],))
        user = c.fetchone()
        user_dict = {
            'id': user[0],
            'user_type': user[5],  
            'username': user[1],
            'email': user[2],
            'org_name': user[4],
            'wilaya': user[6],
            'president_name': user[7],
            'president_phone': user[8]
        }
    conn.close()
    subtotal = 0
    cart_items = []
    conn = sqlite3.connect('karate_dojo.db')
    c = conn.cursor()
    for product_id, quantity in session['cart'].items():
        c.execute('SELECT id, name, price, image_url FROM products WHERE id = ?', (product_id,))
        product = c.fetchone()
        if product:
            item_total = product[2] * quantity
            subtotal += item_total
            cart_items.append({
                'id': product[0],
                'name': product[1],
                'price': product[2],
                'image': product[3],
                'quantity': quantity
            })
    conn.close()
    shipping = 10.00 if subtotal > 0 else 0
    total = subtotal + shipping
    return render_template('checkout.html',
                         user=user_dict,
                         user_type=session['user_type'],
                         cart_items=cart_items,
                         subtotal=subtotal,
                         shipping=shipping,
                         total=total)
@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0",debug=True)