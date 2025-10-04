from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Database Models
class Product(db.Model):
    product_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    movements = db.relationship('ProductMovement', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.product_id}>'

class Location(db.Model):
    location_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    movements_from = db.relationship('ProductMovement', foreign_keys='ProductMovement.from_location', backref='from_loc', lazy=True)
    movements_to = db.relationship('ProductMovement', foreign_keys='ProductMovement.to_location', backref='to_loc', lazy=True)

    def __repr__(self):
        return f'<Location {self.location_id}>'

class ProductMovement(db.Model):
    movement_id = db.Column(db.String(50), primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    from_location = db.Column(db.String(50), db.ForeignKey('location.location_id'), nullable=True)
    to_location = db.Column(db.String(50), db.ForeignKey('location.location_id'), nullable=True)
    product_id = db.Column(db.String(50), db.ForeignKey('product.product_id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<ProductMovement {self.movement_id}>'

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# Product Routes
@app.route('/products')
def products():
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

@app.route('/product/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product_id = request.form['product_id']
        name = request.form['name']
        description = request.form.get('description', '')
        
        if Product.query.get(product_id):
            flash('Product ID already exists!', 'danger')
            return redirect(url_for('add_product'))
        
        new_product = Product(product_id=product_id, name=name, description=description)
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('products'))
    
    return render_template('add_product.html')

@app.route('/product/edit/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form.get('description', '')
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products'))
    
    return render_template('edit_product.html', product=product)

@app.route('/product/view/<product_id>')
def view_product(product_id):
    product = Product.query.get_or_404(product_id)
    movements = ProductMovement.query.filter_by(product_id=product_id).order_by(ProductMovement.timestamp.desc()).all()
    return render_template('view_product.html', product=product, movements=movements)

# Location Routes
@app.route('/locations')
def locations():
    all_locations = Location.query.all()
    return render_template('locations.html', locations=all_locations)

@app.route('/location/add', methods=['GET', 'POST'])
def add_location():
    if request.method == 'POST':
        location_id = request.form['location_id']
        name = request.form['name']
        address = request.form.get('address', '')
        
        if Location.query.get(location_id):
            flash('Location ID already exists!', 'danger')
            return redirect(url_for('add_location'))
        
        new_location = Location(location_id=location_id, name=name, address=address)
        db.session.add(new_location)
        db.session.commit()
        flash('Location added successfully!', 'success')
        return redirect(url_for('locations'))
    
    return render_template('add_location.html')

@app.route('/location/edit/<location_id>', methods=['GET', 'POST'])
def edit_location(location_id):
    location = Location.query.get_or_404(location_id)
    
    if request.method == 'POST':
        location.name = request.form['name']
        location.address = request.form.get('address', '')
        db.session.commit()
        flash('Location updated successfully!', 'success')
        return redirect(url_for('locations'))
    
    return render_template('edit_location.html', location=location)

@app.route('/location/view/<location_id>')
def view_location(location_id):
    location = Location.query.get_or_404(location_id)
    movements = ProductMovement.query.filter(
        (ProductMovement.from_location == location_id) | 
        (ProductMovement.to_location == location_id)
    ).order_by(ProductMovement.timestamp.desc()).all()
    return render_template('view_location.html', location=location, movements=movements)

# ProductMovement Routes
@app.route('/movements')
def movements():
    all_movements = ProductMovement.query.order_by(ProductMovement.timestamp.desc()).all()
    return render_template('movements.html', movements=all_movements)

@app.route('/movement/add', methods=['GET', 'POST'])
def add_movement():
    if request.method == 'POST':
        movement_id = request.form['movement_id']
        product_id = request.form['product_id']
        from_location = request.form.get('from_location') or None
        to_location = request.form.get('to_location') or None
        qty = int(request.form['qty'])
        
        if ProductMovement.query.get(movement_id):
            flash('Movement ID already exists!', 'danger')
            return redirect(url_for('add_movement'))
        
        if not from_location and not to_location:
            flash('At least one location (from or to) must be specified!', 'danger')
            return redirect(url_for('add_movement'))
        
        new_movement = ProductMovement(
            movement_id=movement_id,
            product_id=product_id,
            from_location=from_location,
            to_location=to_location,
            qty=qty
        )
        db.session.add(new_movement)
        db.session.commit()
        flash('Movement added successfully!', 'success')
        return redirect(url_for('movements'))
    
    products = Product.query.all()
    locations = Location.query.all()
    return render_template('add_movement.html', products=products, locations=locations)

@app.route('/movement/edit/<movement_id>', methods=['GET', 'POST'])
def edit_movement(movement_id):
    movement = ProductMovement.query.get_or_404(movement_id)
    
    if request.method == 'POST':
        movement.product_id = request.form['product_id']
        movement.from_location = request.form.get('from_location') or None
        movement.to_location = request.form.get('to_location') or None
        movement.qty = int(request.form['qty'])
        
        if not movement.from_location and not movement.to_location:
            flash('At least one location (from or to) must be specified!', 'danger')
            return redirect(url_for('edit_movement', movement_id=movement_id))
        
        db.session.commit()
        flash('Movement updated successfully!', 'success')
        return redirect(url_for('movements'))
    
    products = Product.query.all()
    locations = Location.query.all()
    return render_template('edit_movement.html', movement=movement, products=products, locations=locations)

@app.route('/movement/view/<movement_id>')
def view_movement(movement_id):
    movement = ProductMovement.query.get_or_404(movement_id)
    return render_template('view_movement.html', movement=movement)

# Report Route
@app.route('/report')
def report():
    # Calculate balance for each product in each location
    movements = ProductMovement.query.all()
    balance = {}
    
    for movement in movements:
        key_product = movement.product_id
        
        # Add to destination location
        if movement.to_location:
            key = (key_product, movement.to_location)
            balance[key] = balance.get(key, 0) + movement.qty
        
        # Subtract from source location
        if movement.from_location:
            key = (key_product, movement.from_location)
            balance[key] = balance.get(key, 0) - movement.qty
    
    # Convert to list for display
    report_data = []
    for (product_id, location_id), qty in balance.items():
        if qty != 0:  # Only show non-zero balances
            product = Product.query.get(product_id)
            location = Location.query.get(location_id)
            report_data.append({
                'product': product.name if product else product_id,
                'location': location.name if location else location_id,
                'qty': qty
            })
    
    # Sort by product name, then location name
    report_data.sort(key=lambda x: (x['product'], x['location']))
    
    return render_template('report.html', report_data=report_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)