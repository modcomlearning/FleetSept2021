# we will use to trigger HTML files
from flask import *
app = Flask(__name__)
from functions import *
import pymysql
app.secret_key = "5_$H#8Mh-*Lg28_#" # Used to secure the session key

connection = pymysql.connect(host='localhost', user='root', password='', database='FleetDB')
@app.route('/login', methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        #check if email provided is in DB
        sql = "select * from users where email = %s"  # %s is a placeholder.
        cursor = connection.cursor()
        cursor.execute(sql, (email))  # This is email goes to placeholder

        # After executing sql, how many rows were found
        if cursor.rowcount == 0:
            return render_template('login.html', message1 = "Invalid Email")
        else:
            row = cursor.fetchone()
            if row[5] == "inactive":
                return render_template('login.html', message1="Account is Inactive")
            else:
                # Check plain password provided matches the hased password from DB
                hashed_password = row[6]  # get hashed password from db
                result = hash_verify(password, hashed_password)
                if result==True:
                     phone = row[8] #this number is encrypted
                     decrypted_phone = decrypt(phone)  # decrypt it
                     otp = gen_random()  # call function to get an otp

                     # save this otp in the database
                     sql = "update users set otp = %s, otptime = %s where email = %s"
                     cursor = connection.cursor()

                     from datetime import datetime
                     date = datetime.now()
                     # we hash otp and save it to database alongside time
                     cursor.execute(sql, (hash_password(otp), date, email))
                     connection.commit()

                     send_sms(decrypted_phone, "Your OTP is {}, Don't share with anyone!".format(otp)) # send sms
                     # ACtivate user sessions
                     session['email'] = email # store email to session
                     return redirect('/confirm_otp') # Naiviage to another route

                else:
                    return render_template('login.html', message1="Wrong Credentials")

    else:
        return render_template('login.html')


@app.route('/confirm_otp', methods = ['POST', 'GET'])
def confirm_otp():
    if request.method == 'POST':
        if 'email' in session:
            otp = request.form['otp']
            email = session['email']
            # Confirm that OTP user provided is same as one in the DB/text sent
            sql = "select * from users  where email = %s"
            cursor = connection.cursor()
            cursor.execute(sql, (email))
            row = cursor.fetchone()
            hashed_otp = row[11] # This is the OTP from the DB
            result = hash_verify(otp, hashed_otp)
            if result:
                return render_template('confirm_otp.html', message2 = "OTP Valid")
            else:
                return render_template('confirm_otp.html' , message1 = "Your OTP is Invalid")
        else:
            return redirect('/login')
    else:
        return render_template('confirm_otp.html')


app.run(debug=True)