import datetime

from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import mysql.connector

app = Flask(__name__, template_folder="templates", static_folder='static')
# Configure MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/db1'

db = SQLAlchemy(app)


class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=False)


class Itinerary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    destination_id = db.Column(db.Integer, db.ForeignKey('destination.id'), nullable=False)
    activity = db.Column(db.String(200), nullable=False)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)


app.app_context().push()
db.create_all()


@app.route('/', methods=['GET', 'POST'])
def main_page():
    return render_template('index.html')


@app.route('/add_destination', methods=['GET', 'POST'])
def add_destination():
    if request.method == 'GET':
        return '''
            <form method="POST">
                <label for="name">Name:</label><br>
                <input type="text" id="name" name="name"><br>
                <label for="description">Description:</label><br>
                <input type="text" id="description" name="description"><br>
                <label for="location">Location:</label><br>
                <input type="text" id="location" name="location"><br><br>
                <input type="submit" value="Submit">
            </form>
        '''
    elif request.method == 'POST':
        new_destination = Destination(
            name=request.form['name'],
            description=request.form['description'],
            location=request.form['location']
        )
        db.session.add(new_destination)
        db.session.commit()
        return jsonify({'message': 'New destination added!'})


@app.route('/destinations', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_destinations():
    if request.method == 'GET':
        all_destinations = Destination.query.all()
        result = []
        for destination in all_destinations:
            result.append({
                'id': destination.id,
                'name': destination.name,
                'description': destination.description,
                'location': destination.location
            })
        return jsonify(result)

    elif request.method == 'POST':
        new_destination = Destination(
            name=request.form['name'],
            description=request.form['description'],
            location=request.form['location']
        )
        db.session.add(new_destination)
        db.session.commit()
        return jsonify({'message': 'New destination added!'})


@app.route('/destinations/<int:destination_id>', methods=['PUT', 'DELETE'])
def manage_single_destination(destination_id):
    destination = Destination.query.get(destination_id)

    if not destination:
        return jsonify({'error': 'Destination not found!'})

    if request.method == 'PUT':
        data = request.get_json()
        destination.name = data['name']
        destination.description = data['description']
        destination.location = data['location']
        db.session.commit()
        return jsonify({'message': 'Destination updated!'})

    elif request.method == 'DELETE':
        # Delete related records in the itinerary table
        itineraries = Itinerary.query.filter_by(destination_id=destination_id).all()
        for itinerary in itineraries:
            db.session.delete(itinerary)

        # Delete the destination record
        db.session.delete(destination)
        db.session.commit()
        return jsonify({'message': 'Destination deleted!'})


@app.route('/add_itinerary', methods=['GET'])
def render_add_itinerary():
    return render_template('itineraries.html')


# Routes for managing itineraries
@app.route('/itineraries', methods=['GET', 'POST'])
def itineraries():
    if request.method == 'GET':
        all_itineraries = Itinerary.query.all()
        result = []
        for itinerary in all_itineraries:
            result.append({
                'destination_id': itinerary.destination_id,
                'activity': itinerary.activity
            })
        return jsonify(result)

    elif request.method == 'POST':
        data = request.form
        destination_id = data['destination_id']
        activity = data['activity']
        # Check if the destination with the provided ID exists
        destination = Destination.query.get(destination_id)
        if destination:
            new_itinerary = Itinerary(destination_id=destination_id, activity=activity)
            db.session.add(new_itinerary)
            db.session.commit()
            return jsonify({'message': 'New itinerary added!'})
        else:
            return jsonify({'error': 'Destination not found!'})


@app.route('/exp', methods=['GET', 'POST'])
def expences_page():
    return render_template('expense.html')


@app.route('/expenses', methods=['POST'])
def add_expense():
    data = request.get_json()
    itinerary_id = data.get('itinerary_id')

    # Check if the itinerary with the given ID exists
    itinerary = Itinerary.query.get(itinerary_id)
    if not itinerary:
        return jsonify({'error': 'Itinerary with the provided ID does not exist'}), 404

    new_expense = Expense(
        itinerary_id=itinerary_id,
        amount=data['amount'],
        category=data['category']
    )
    db.session.add(new_expense)
    db.session.commit()
    return jsonify({'message': 'Expense added successfully'})


@app.route('/expenses', methods=['GET'])
def get_expenses():
    expenses = Expense.query.all()
    result = []
    for expense in expenses:
        itinerary_id = expense.itinerary_id
        itinerary = Itinerary.query.filter_by(id=itinerary_id).first()
        if itinerary:
            result.append({
                'id': expense.id,
                'itinerary_id': itinerary_id,
                'amount': expense.amount,
                'category': expense.category,
                'date': expense.date.strftime('%Y-%m-%d %H:%M:%S')
            })
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
