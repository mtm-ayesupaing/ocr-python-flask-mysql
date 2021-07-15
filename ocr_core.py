import pymysql
from flask_bcrypt import Bcrypt
from app import app
from db import mysql
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from tesserocr import PyTessBaseAPI, RIL, iterate_level
from PIL import Image
from flask_cors import CORS, cross_origin
import re
import os

bcrypt = Bcrypt(app)
UPLOAD_FOLDER = '/uploads'

@app.route('/ocr', methods=['GET', 'POST'])
def processFile():
    try:
        if request.method == 'POST':
            file = request.files['file']
            if file:
                data = []
                result = {}
                file.save(os.path.join(os.getcwd() + UPLOAD_FOLDER, file.filename))
                images = ['uploads/' + file.filename]
                resp = jsonify('Image uploaded successfully!')
                with PyTessBaseAPI(path='./tessdata/.', lang='eng') as api:    
                    for img in images:
                        api.SetImageFile(img)
                        result['raw_data'] = api.GetUTF8Text()
                        data = api.GetUTF8Text().split('\n')
                        data = [item for item in data if item != '' and item != ' ' and item != '  ']
                    
                        for i, value in enumerate(data):
                            if i == 0:
                                result['title'] = value                  
                            if re.search('Name', value):
                                nameVal = data[i + 1]
                                result['name'] = nameVal
                            elif re.search('Nation', value):
                                nationVal = data[i + 1]
                                result['nation'] = nationVal
                            elif re.search('Date of birth', value):
                                dobVal = data[i + 1]
                                result['dob'] = dobVal
                            elif re.search('Sex', value):
                                genderVal = data[i + 1]
                                result['gender'] = genderVal
                            elif re.search('Date of issue', value):
                                dateIssueVal = data[i + 1]
                                result['issue_date'] = dateIssueVal
                            elif re.search('Date of expire', value):
                                dateExpireVal = data[i + 1]
                                result['expire_date'] = dateExpireVal
                            elif re.search('Place of', value):
                                pobVal = data[i + 1]
                                result['pob'] = pobVal
                            elif re.search('Authority', value):
                                authVal = data[i + 1]
                                result['authority'] = authVal
                            elif re.search('Passport No', value):
                                passportNoVal = data[i + 1]
                                result['passport_no'] = passportNoVal
                            elif re.search('type', value):
                                passportTypeVal = data[i + 1]
                                result['passport_type'] = passportTypeVal
                            elif re.search('Country Code', value):
                                countryCodeVal = data[i + 1]
                                result['country_code'] = countryCodeVal

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
        'message': 'Not Found: ' + request  .url,
    }
    resp = jsonify(message)
    resp.status_code = 404
    return resp

if __name__ == "__main__":
  app.run(debug=True)
  CORS(app)


