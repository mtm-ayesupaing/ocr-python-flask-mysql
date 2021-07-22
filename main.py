import os
import pymysql
from flask_bcrypt import Bcrypt
from app import app
from db import mysql
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from werkzeug.security import generate_password_hash, check_password_hash
from tesserocr import PyTessBaseAPI, RIL, iterate_level
from PIL import Image
import datetime
import re
import os

bcrypt = Bcrypt(app)
UPLOAD_FOLDER = '/uploads/'
		
@app.route('/add', methods=['POST'])
def add_user():
	try:
		_json = request.json
		_name = _json['name']
		_email = _json['email']
		_password = _json['pwd']		
		# validate the received values
		if _name and _email and _password and request.method == 'POST':
			conn = mysql.connect()
			cursor = conn.cursor()
			# check duplicate email
			cursor.execute("SELECT user_id id, user_name name, user_email email, user_password pwd FROM tbl_user WHERE user_email=%s", _email)
			userRow = cursor.fetchone()
			conn.commit()
			if userRow:
				resp = jsonify('Duplicate Email!')
				return resp				
			else:
				# do not save password as a plain text
				_hashed_password = generate_password_hash(_password)
				# save edits
				sql = "INSERT INTO tbl_user(user_name, user_email, user_password) VALUES(%s, %s, %s)"
				data = (_name, _email, _hashed_password,)				
				cursor.execute(sql, data)
				conn.commit()
				resp = jsonify('User added successfully!')
				resp.status_code = 200
				return resp
		else:
			return not_found()
	except Exception as e:
		print(e)
	finally:
		cursor.close() 
		conn.close()
		
@app.route('/users')
def users():
	try:
		conn = mysql.connect()
		cursor = conn.cursor(pymysql.cursors.DictCursor)
		cursor.execute("SELECT user_id id, user_name name, user_email email, user_password pwd FROM tbl_user")
		rows = cursor.fetchall()
		resp = jsonify(rows)
		resp.status_code = 200
		return resp
	except Exception as e:
		print(e)
	finally:
		cursor.close() 
		conn.close()
		
@app.route('/user/<int:id>')
def user(id):
	try:
		conn = mysql.connect()
		cursor = conn.cursor(pymysql.cursors.DictCursor)
		cursor.execute("SELECT user_id id, user_name name, user_email email, user_password pwd FROM tbl_user WHERE user_id=%s", id)
		row = cursor.fetchone()
		resp = jsonify(row)
		resp.status_code = 200
		return resp
	except Exception as e:
		print(e)
	finally:
		cursor.close() 
		conn.close()

@app.route('/update', methods=['PUT'])
def update_user():
	try:
		_json = request.json
		_id = _json['id']
		_name = _json['name']
		_email = _json['email']
		_password = _json['pwd']		
		# validate the received values
		if _name and _email and _password and _id and request.method == 'PUT':
			#do not save password as a plain text
			_hashed_password = generate_password_hash(_password)
			# save edits
			sql = "UPDATE tbl_user SET user_name=%s, user_email=%s, user_password=%s WHERE user_id=%s"
			data = (_name, _email, _hashed_password, _id,)
			conn = mysql.connect()
			cursor = conn.cursor()
			cursor.execute(sql, data)
			conn.commit()
			resp = jsonify('User updated successfully!')
			resp.status_code = 200
			return resp
		else:
			return not_found()
	except Exception as e:
		print(e)
	finally:
		cursor.close() 
		conn.close()
		
@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_user(id):
	try:
		conn = mysql.connect()
		cursor = conn.cursor()
		cursor.execute("DELETE FROM tbl_user WHERE user_id=%s", (id,))
		conn.commit()
		resp = jsonify('User deleted successfully!')
		resp.status_code = 200
		return resp
	except Exception as e:
		print(e)
	finally:
		cursor.close() 
		conn.close()

@app.route('/searchUser', methods=['POST'])
def searchUser():
	try:
		_json = request.json	
		name = _json['name']
		email = _json['email']
		query = 'SELECT user_id id, user_name name, user_email email FROM tbl_user WHERE '
		if (name and email == ''):
			query += 'user_name like "%' + name + '%"'
		elif (name and email):
			query += 'user_name like "%' + name + '%" AND '
		else:
			query += ''
		
		if (email):
			query += 'user_email like "%' + email + '%"'
		else:
			query += ''

		print(query)
		conn = mysql.connect()
		cursor = conn.cursor(pymysql.cursors.DictCursor)
		cursor.execute(query)
		row = cursor.fetchall()
		resp = jsonify(row)
		resp.status_code = 200
		return resp
	except Exception as e:
		print(e)
	finally:
		cursor.close() 
		conn.close()		

@app.route('/login', methods=['POST'])
def login():
	try:
		json_data = request.json
		email = json_data['email']
		password = json_data['password']
		conn = mysql.connect()
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM tbl_user WHERE user_email=%s", email)		
		user = cursor.fetchone()
		if user and check_password_hash(user[3], password):
			# session['logged_in'] = True
			status = True
		else:
			status = False
		return jsonify({'result': status})
	except Exception as e:
		print(e)
	finally:
		cursor.close() 
		conn.close()

@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
	try:
		if request.method == 'POST':
			file = request.files['file']
			filepath = UPLOAD_FOLDER + file.filename
			if file:
				file.save(os.path.join(os.getcwd() + UPLOAD_FOLDER, file.filename))
				extracted_text = ocr_core(filepath)
			resp = jsonify(extracted_text)
			resp.status_code = 200
			return resp
	except Exception as e:
		print(e)

@app.route('/savePassport', methods=['POST'])
def save_passport():
	try:
		_json = request.json
		passportType = _json['passportType']
		countryCode = _json['countryCode']
		passportNo = _json['passportNo']
		name = _json['name']
		nationality = _json['nationality']
		gender = _json['gender']
		dob = datetime.datetime.strptime(_json['dob'], "%Y-%m-%d")
		issueDate = datetime.datetime.strptime(_json['issueDate'], "%Y-%m-%d")
		expiryDate = datetime.datetime.strptime(_json['expiryDate'], "%Y-%m-%d")
		birthPlace = _json['birthPlace']
		authority = _json['authority']		
		# validate the received values
		if name and passportNo and passportType and request.method == 'POST':
			# save edits
			#sql = "INSERT INTO tbl_passport(passport_no, passport_type, country_code, name, nationality, gender, birth_place, authority) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"
			sql = "INSERT INTO tbl_passport(passport_no, passport_type, country_code, name, nationality, dob, gender, issue_date, expiry_date, birth_place, authority) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
			data = (passportNo, passportType, countryCode,  name, nationality, dob, gender, issueDate, expiryDate, birthPlace, authority)
			conn = mysql.connect()
			cursor = conn.cursor()
			cursor.execute(sql, data)
			conn.commit()
			cursor.close()
			resp = jsonify('Passport data added successfully!')
			resp.status_code = 200
			return resp
		else:
			return not_found()
	except Exception as e:
			print(e)
	finally:
		cursor.close()
		conn.close()
		
@app.route('/passports')
def passports():
	try:
		conn = mysql.connect()
		cursor = conn.cursor(pymysql.cursors.DictCursor)
		cursor.execute("SELECT * FROM tbl_passport")
		rows = cursor.fetchall()
		resp = jsonify(rows)
		resp.status_code = 200
		return resp
	except Exception as e:
		print(e)
	finally:
		cursor.close() 
		conn.close()
		
@app.route('/getPassportNo/<string:passport_no>')
def getPassportNo(passport_no):
	try:
		conn = mysql.connect()
		cursor = conn.cursor(pymysql.cursors.DictCursor)
		cursor.execute("SELECT * FROM tbl_passport WHERE passport_no=%s", passport_no)
		row = cursor.fetchall()
		resp = jsonify(row)
		resp.status_code = 200
		return resp
	except Exception as e:
		print(e)
	finally:
		cursor.close() 
		conn.close()


@app.route('/searchPassport', methods=['POST'])
def searchPassport():
	try:
		_json = request.json	
		name = _json['name']
		expiryDate = _json['expiryDate']
		passportNo = _json['passportNo']
		query = 'SELECT * FROM tbl_passport WHERE '
		if (name and passportNo == '' and expiryDate == ''):
			query += 'name like "%' + name + '%"'
		elif (name and (passportNo or expiryDate)):
			query += 'name like "%' + name + '%" AND '
		else:
			query += ''
		
		if (passportNo and expiryDate == ''):
			query += 'passport_no like "%' + passportNo + '%"'
		elif (passportNo and expiryDate):
			query += 'passport_no like "%' + passportNo + '%" AND '
		else:
			query += ''

		if (expiryDate):
			expiryDate = datetime.datetime.strptime(_json['expiryDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
			expiryDate = expiryDate.strftime("%Y-%m-%d")
			query += 'expiry_date >= "' + expiryDate + '"'
		else:
			query += ''

		print(query)
		conn = mysql.connect()
		cursor = conn.cursor(pymysql.cursors.DictCursor)
		cursor.execute(query)
		row = cursor.fetchall()
		resp = jsonify(row)
		resp.status_code = 200
		return resp
	except Exception as e:
		print(e)
	finally:
		cursor.close() 
		conn.close()

@app.route('/updatePassport/<string:passport_no>', methods=['PUT'])
def update_passport(passport_no):
	try:
		_json = request.json
		passportType = _json['passportType']
		countryCode = _json['countryCode']
		passportNo = _json['passportNo']
		name = _json['name']
		nationality = _json['nationality']
		dob = _json['dob']
		gender = _json['gender']
		issueDate = _json['issueDate']
		expiryDate = _json['expiryDate']
		birthPlace = _json['birthPlace']
		authority = _json['authority']
		# validate the received values
		if name and passportNo and passportType and request.method == 'PUT':
			# save edits
			sql = "UPDATE tbl_passport SET passport_type=%s, country_code=%s, passport_no=%s, name=%s, nationality=%s, dob=%s, gender=%s, issue_date=%s, expiry_date=%s, birth_place=%s, authority=%s WHERE passport_no=%s"
			data = (passportType, countryCode, passportNo, name, nationality, dob, gender, issueDate, expiryDate, birthPlace, authority, passport_no)
			conn = mysql.connect()
			cursor = conn.cursor()
			cursor.execute(sql, data)
			conn.commit()
			resp = jsonify('Passport updated successfully!')
			resp.status_code = 200
			return resp
		else:
			return not_found()
	except Exception as e:
		print(e)
	finally:
		cursor.close() 
		conn.close()

@app.route('/deletePassport/<string:passport_no>', methods=['DELETE'])
def delete_passport(passport_no):
	try:
		conn = mysql.connect()
		cursor = conn.cursor()
		cursor.execute("DELETE FROM tbl_passport WHERE passport_no=%s", (passport_no,))
		conn.commit()
		resp = jsonify('Passport deleted successfully!')
		resp.status_code = 200
		return resp
	except Exception as e:
		print(e)
	finally:
		cursor.close() 
		conn.close()

@app.route('/ocr', methods=['GET', 'POST'])
def processFile():
    try:
        if request.method == 'POST':
            file = request.files['file']
            if file:
                data = []
                result = {}
                passport_no = ''
                passport_type = ''
                file.save(os.path.join(os.getcwd() + UPLOAD_FOLDER, file.filename))
                images = ['uploads/' + file.filename]
                resp = jsonify('Image uploaded successfully!')
                with PyTessBaseAPI(path='./tessdata/.', lang='eng') as api:    
                    for img in images:
                        api.SetImageFile(img)						
                        result['raw_data'] = api.GetUTF8Text()
                        data = api.GetUTF8Text().split('\n')
                        data = [item for item in data if item != '' and item != ' ' and item != '  ']
                        passport_no = data[-1].split('<')
                        passport_type = data[-2].split('MMR')
                        for i, value in enumerate(data):
                            result['country_code'] = 'MMR'
                            if 0 in range(len(passport_no)):
                                result['passport_no'] = passport_no[0]
                            if 0 in range(len(passport_type)):
                                result['passport_type'] = passport_type[0] 
        
                            if re.search('Name', value):
                                nameVal = data[i + 1]
                                result['name'] = nameVal
                            elif re.search('Nationality', value):
                                nationVal = data[i + 1]
                                result['nationality'] = nationVal
                            elif re.search('Date of birth', value):
                                dobVal = data[i + 1]
                                result['dob'] = dobVal
                            elif re.search('Sex', value):
                                genderVal = data[i + 1]
                                result['gender'] = genderVal
                            elif re.search('Date of issue', value):
                                dateIssueVal = data[i + 1]
                                result['issue_date'] = dateIssueVal
                            elif re.search('Date of expiry', value):
                                dateExpireVal = data[i + 1]
                                result['expiry_date'] = dateExpireVal
                            elif re.search('Place of birth', value):
                                pobVal = data[i + 1]
                                result['birth_place'] = pobVal
                            elif re.search('Authority', value):
                                authVal = data[i + 1]
                                result['authority'] = authVal
                            elif re.search('passport', value):
                                passportVal = data[i + 1]
                                passportArr = passportVal.split()
                                if 0 in range(len(passportArr)):
                                    result['passport_type'] = passportArr[0]
                                if 1 in range(len(passportArr)):
                                    result['country_code'] = passportArr[1]
                                if 2 in range(len(passportArr)):
                                    result['passport_no'] = passportArr[2]
                            elif re.search('Country', value):
                                countryVal = data[i + 1]
                                result['country_code'] = countryVal
                resp = jsonify(result)
                resp.status_code = 200
                return resp
            else :
                return not_found()
    except Exception as e:
            print(e)
		
@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp
		
if __name__ == "__main__":
    app.run()