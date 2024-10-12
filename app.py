from flask import Flask, render_template, request, redirect, url_for, session, flash
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

#flask
app = Flask(__name__)
app.secret_key = 'Matta'
#cred = credentials.Certificate('C:\\Users\\matta\\PycharmProjects\\CMPSC487W\\cmpsc-487w-b51db-firebase-adminsdk-4hn0f-751faf6f76.json')
#firebase
cred = credentials.Certificate('cmpsc-487w-b51db-19b35edebb22.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

#Home
@app.route('/')
def home():
    return render_template('index.html')

#reserve page code
@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    today = datetime.today().strftime('%Y-%m-%d')

    if request.method == 'POST':
        driver_name = request.form['driver_name']
        vehicle_type = request.form['vehicle_type']
        reservation_start = request.form['reservation_start']
        reservation_end = request.form['reservation_end']

        if reservation_start < today:
            return "Error: Start date cannot be in the past", 400

        #reservation info
        reservation_data = {
            'driver_name': driver_name,
            'vehicle_type': vehicle_type,
            'reservation_start': reservation_start,
            'reservation_end': reservation_end,
            'status': 'pending',
            'created_at': datetime.now()
        }

        #add the reservation to Firebase and get document/reserve code
        reservation_ref = db.collection('reservations').add(reservation_data)
        reservation_code = reservation_ref[1].id #code #fixed

        #show user code
        return render_template('reservation_success.html', reservation_code=reservation_code)

    return render_template('reservation_form.html', today=today)

#extend reservation page
@app.route('/extend', methods=['GET', 'POST'])
def extend_reservation():
    if request.method == 'POST':
        reservation_code = request.form['reservation_code']
        new_end_date = request.form['new_end_date']

        #use code to get reservation
        reservation_ref = db.collection('reservations').document(reservation_code)
        reservation = reservation_ref.get()

        if reservation.exists:
            #update reservation
            reservation_ref.update({
                'reservation_end': new_end_date,
            })
            return f"Reservation with code {reservation_code} extended successfully!"
        else:
            return "Reservation code not found!", 404

    return render_template('extend.html')

#Manager login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        #username and password both "Admin"
        if username == 'Admin' and password == 'Admin':
            session['logged_in'] = True  #fixed login and reservation list issue
            return redirect(url_for('reservations_list'))
        else:
            flash('incorrect, try again.')
            return redirect(url_for('login'))

    return render_template('login.html')

#update status
@app.route('/update_status', methods=['POST'])
def update_status():
    if 'logged_in' in session:
        reservation_id = request.form['reservation_id']
        new_status = request.form['new_status']

        #id to find reservation
        reservation_ref = db.collection('reservations').document(reservation_id)
        reservation = reservation_ref.get()

        if reservation.exists:
            #reservation status
            reservation_ref.update({
                'status': new_status,
            })
            flash(f"Reservation {reservation_id} updated to {new_status}.")
        else:
            flash(f"Reservation {reservation_id} not found.")

        return redirect(url_for('reservations_list'))
    else:
        return redirect(url_for('login'))

#reservation list
@app.route('/reservations')
def reservations_list():
    if 'logged_in' in session:
        reservations = db.collection('reservations').stream()
        reservation_list = []
        for res in reservations:
            reservation_data = res.to_dict()
            reservation_data['id'] = res.id
            reservation_list.append(reservation_data)
        return render_template('reservations_list.html', reservations=reservation_list)
    else:
        #log in page if not
        return redirect(url_for('login'))

#logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
