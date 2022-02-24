import datetime
from flask import Flask, request, jsonify, make_response, Response,  render_template
from flask_restful import Api, Resource
import datetime
import pandas as pd
from backend.backend import *
from apscheduler.schedulers.background import BackgroundScheduler
from collections import OrderedDict
import atexit
import jwt
from functools import wraps
from urllib.parse import urlparse

"""
    Define blacklist flushing function:
        If token in blacklist has not yet expired, decoding is successful and token stays in blacklist.
        Else token is removed from blacklist
"""

blacklist=[]

def token_cleaner():
    global blacklist
    temp = []
    for token in blacklist:
        try:
            jwt.decode(token, app.config['SECRET_KEY'])
            temp.append(token)
        except:
            continue
    blacklist=temp.copy()

"""
    Initialise & Start Scheduler:
        Initialise scheduler as a BackroundScheduler, using a separate deamon thread.
        Add two jobs on scheduler, one for grouping charges by month and provider (scheduled once every 30 days), and one for
        flushing expired tokens from blacklist (scheduled once every 2 minutes).
        Start Scheduler and register scheduler shutdown to be executed at termination.
             
"""    

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=refresh, trigger='interval', days=30)
scheduler.add_job(func=token_cleaner, trigger='interval', minutes = 2)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

"""
    Initialise app as an object of Flask class.
    Initialise API as RESTful.
"""

app = Flask(__name__)
api = Api(app)
path = '/interoperability/api/'

"""
    Config Flask object:
        Disable alphabetical sorting of keys in JSON objects in order to set specified order.
        Set SECRET_KEY value used to encrypt and decrypt tokens.
"""
app.config['JSON_SORT_KEYS'] = False
app.config['SECRET_KEY'] = 'se2125'

"""
    Define wrapper function token_required:
    (adds argument current_user to function f)
        Take token from request headers
        If token is in blacklist, user has logged out.
        Else decode token and extract current_user info.

"""

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        global blacklist
        token = None
        if 'access-token' in request.headers:
            token = request.headers['access-token']

        if not token:
            return make_response(jsonify({'message' : 'Token is missing!'}), 401)
        try:
            if (token in blacklist): 
                return make_response(jsonify({'message' : 'User has logged out!'}), 401)
            else:
                data = jwt.decode(token, app.config['SECRET_KEY'])
                current_user = data['user']

        except:
            return make_response(jsonify({'message' : 'Token is invalid!'}), 401)

        return f(current_user, *args, **kwargs)
        
    return decorated

"""
    Function to check if dateFrom and dateTo are valid dates and consist a valid time period.
"""
def checkdate(dateFrom, dateTo):
        if (
            (not dateFrom.isnumeric()) or\
            (not dateTo.isnumeric()) or\
            (len(dateTo)!=8) or\
            (len(dateFrom)!=8) or\
            (not('01' <= dateFrom[4:6] and dateFrom[4:6] <= '12')) or\
            (not('01' <=dateTo[4:6] and dateTo[4:6] <= '12')) or\
            (not (dateTo[6:] <= '31')) or\
            (not (dateTo[6:] <= '31')) or\
            (dateFrom > dateTo)):
                return False
        else: 
            return True
"""
    Define Resource healthcheck:
    (confirms end-to-end connectivity between user and database)
        Call healthcheckB function from backend and based on its result return respective JSON object.

"""
class healthcheck(Resource):
    def get(self):
        try:
            dbconnection = " host: 'localhost',port : '3306', user : 'root', password : 'softeng', database : 'softeng'"
            if(healthcheckB()):    
                status = 'ok'
                statusCode = 200
            else:
                status = 'failed'
                statusCode = 500
        except:
                status = 'failed'
                statusCode = 500
        finally:
            return make_response(jsonify(OrderedDict({'status': status,'dbconnection': dbconnection})), statusCode)

@app.route('/interoperability/api/createUser.html', methods = ['GET'])
def gotocreateuser():
    return render_template('./createUser.html')

@app.route('/interoperability/api/PassesPerStation.html', methods = ['GET'])
def gotopassesperstation():
    return render_template('./PassesPerStation.html')

@app.route('/interoperability/api/PassesAnalysis.html', methods = ['GET'])
def gotopassesanalysis():
    return render_template('./PassesAnalysis.html')

@app.route('/interoperability/api/PassesCost.html', methods = ['GET'])
def gotopassescost():
    return render_template('./PassesCost.html')

@app.route('/interoperability/api/ChargesBy.html', methods = ['GET'])
def gotochargesby():
    return render_template('./ChargesBy.html')

@app.route('/interoperability/api/operator.html')
def gotooperator():
    return render_template('./operator.html')

@app.route('/interoperability/api/administrator.html')
def gotoadministrator():
    return render_template('./administrator.html')

@app.route('/interoperability/api/ministry.html')
def gotoministry():
    return render_template('./ministry.html')

@app.route('/interoperability/api/')
def gotohtml():
    return render_template('./loginForm.html')

"""
    Define Resource resetPasses:
    (deletes tupples of table passes of db and initialises default admin accoun)
        Call resetPassesB function from backend and based on its result return respective JSON object.

"""

class resetPasses(Resource):
    def post(self):
        try:
            if(resetPassesB()):    
                status = 'ok'
                statusCode = 200
            else:
                status = 'failed'
                statusCode = 500
        except:
                status = 'failed'
                statusCode = 500
        finally:
            return make_response(jsonify({'status': status}), statusCode)

"""
    Define Resource resetStations:
    (initialise station table of db with default data)
        Call resetStationsB function from backend and based on its result return respective JSON object.

"""

class resetStations(Resource):
    def post(self):
        try:
            if(resetStationsB()):    
                status = 'ok'
                statusCode = 200
            else:
                status = 'failed'
                statusCode = 500
        except:
                status = 'failed'
                statusCode = 500
        finally:
            return make_response(jsonify({'status': status}), statusCode)

"""
    Define Resource resetVehicles:
    (initialise vehicle table of db with default data)
        Call resetVehiclesB function from backend and based on its result return respective JSON object.

"""

class resetVehicles(Resource):
    def post(self):
        try:
            if(resetVehiclesB()):    
                status = 'ok'
                statusCode = 200
            else:
                status = 'failed'
                statusCode = 500
        except:
                status = 'failed'
                statusCode = 500
        finally:
            return make_response(jsonify({'status': status}), statusCode)


"""
    Define Resource passesPerStation:
    (returns list of passes for the specified station and time period, using the specified format (json or csv))
        Check if current_user has access to this data and arguments are valid.
        Get return list format and check its validity.
        Call passesPerStationB function from backend.
        If passesPerStationB return value indicates unavailable or nonexistant data, return corresponding error.
        For every row of data return, differentiate between home and visitor passes.
        Compose result according to given format.
        If format is "csv", create list of dictionaries, in which every dictionary represents a csv row. 
        Then convert list to a csv form string of data with ";" as the delimeter. Return string as JSON object accompanied by the successful HTTP status code.         
        If format is "json", attach list of dictionaries as the field "PassesList" of the output dictionary, fill the other fields as needed 
        and return said dict. as a JSON object accompanied by the successful HTTP status code. 

"""
timeFrmt = '%Y-%m-%d %H:%M:%S'

class passesPerStation(Resource):
    @token_required
    def get(current_user,self,stationID, dateFrom, dateTo):
      try:  
            current_user_type = getUserTypeB(current_user)
            if(current_user_type != 'ministry' and current_user_type != 'admin'):
                return make_response(jsonify({'message' : 'Operation not allowed for current user'}), 401)
            #debug?
            print([stationID, dateFrom, dateTo])
            RequestTimestamp = datetime.datetime.now().strftime(timeFrmt)
            datatype = request.args.get('format')
            if (datatype and datatype !='json' and datatype != 'csv'):
                return make_response(jsonify({'status': 'failed'}), 400)
            if (not(len(stationID) == 4) or (not(checkdate(dateFrom, dateTo)))):
                return make_response(jsonify({'status': 'failed'}), 400)
            dateFrom = dateFrom[:4] + '-' + dateFrom[4:6] + '-' + dateFrom[6:]+' 00:00:00'
            dateTo = dateTo[:4] + '-' + dateTo[4:6] + '-' + dateTo[6:] +' 23:59:59'
            ret = passesPerStationB(stationID, dateFrom, dateTo)
            if (ret == None):
                return make_response(jsonify({'status': 'failed'}), 500)
            count = ret['count']
            if (not count):
                return make_response(jsonify({'status': 'failed'}), 402)
            data = ret['data']
            passlist= []
            for i, row in enumerate(data,1):
                PassType = 'visitor'
                TagProvider = row[5]
                if stationID[:2] == TagProvider:
                    PassType = 'home'
                listObj = OrderedDict()
                if datatype == 'csv':
                    listObj = {'Station':stationID, 'StationOperator': stationID[:2], 'RequestTimestamp':RequestTimestamp, 'PeriodFrom' : dateFrom[:10], 'PeriodTo' : dateTo[:10], 'NumberOfPasses' : count ,'PassIndex': i, 'PassID': row[4],'PassTimeStamp': row[0].strftime(timeFrmt), 'VehicleID': row[3], 'TagProvider':TagProvider  ,'PassType': PassType, 'PassCharge': row[1]}
                else:    
                    listObj = {'PassIndex': i, 'PassID': row[4],'PassTimeStamp': row[0].strftime(timeFrmt), 'VehicleID': row[3], 'TagProvider':TagProvider  ,'PassType': PassType, 'PassCharge': row[1]}
                passlist.append(listObj)                  
            if datatype == 'csv':
                pdObjR = pd.DataFrame.from_records(passlist)
                csvData = pdObjR.to_csv(index=False, sep = ';')
                return make_response(csvData, 200)
            else:
                d = OrderedDict()
                d = {'Station':stationID, 'StationOperator': stationID[:2], 'RequestTimestamp':RequestTimestamp, 'PeriodFrom' : dateFrom[:10], 'PeriodTo' : dateTo[:10], 'NumberOfPasses' : count , 'PassesList':passlist}
                return make_response(jsonify(d), 200)
      except Exception as e:
            print(e)
            return make_response(jsonify({'status': 'failed'}), 500)

"""
    Define Resource passesAnalysis:
    (returns list of passes involving tags of operator op2_ID and stations of operator op1_ID for the specified time period, using the specified format (json or csv))
        Follow the same steps as passesPerStation, calling passesAnalysisB instead of passesPerStationB.

"""

class passesAnalysis(Resource):
    @token_required
    def get(current_user, self, op1ID, op2ID, dateFrom, dateTo):
        try:
            RequestTimestamp = datetime.datetime.now().strftime(timeFrmt)
            datatype = request.args.get('format')
            if (datatype and datatype !='json' and datatype != 'csv'):
                return make_response(jsonify({'status': 'failed'}), 400)
            if (not(len(op1ID) == 2) or not(len(op2ID) == 2) or (not(checkdate(dateFrom, dateTo)))):
                return make_response(jsonify({'status': 'failed'}), 400)    
            dateFrom = dateFrom[:4] + '-' + dateFrom[4:6] + '-' + dateFrom[6:]+' 00:00:00'
            dateTo = dateTo[:4] + '-' + dateTo[4:6] + '-' + dateTo[6:]+' 23:59:59'
            
            current_user_type = getUserTypeB(current_user)
            if(current_user_type != op1ID and current_user_type != op2ID and current_user_type!='admin'):
                return make_response(jsonify({'message' : 'Retrieving data for other users is not allowed!'}), 401)
            
            ret = passesAnalysisB(op1ID, op2ID, dateFrom, dateTo)
            #print(ret)

            if (ret == None):
                return make_response(jsonify({'status': 'failed'}), 500)
            count = ret['count']
            if (not count):
                return make_response(jsonify({'status': 'failed'}), 402)
            data = ret['data']
            passlist= []
            for i, row in enumerate(data,1):
              listObj = OrderedDict()
              if datatype == 'csv':
                  listObj = {'op1_ID': op1ID, 'op2_ID': op2ID, 'RequestTimestamp': RequestTimestamp, 'PeriodFrom': dateFrom[:10], 'PeriodTo': dateTo[:10], 'NumberOfPasses' : count, 'PassIndex': i, 'PassID': row[4],'StationID':row[2], 'TimeStamp': row[0].strftime(timeFrmt), 'VehicleID': row[3], 'Charge': row[1]}
              else:
                  listObj = {'PassIndex': i, 'PassID': row[4],'StationID':row[2], 'TimeStamp': row[0].strftime(timeFrmt), 'VehicleID': row[3], 'Charge': row[1]}
              passlist.append(listObj)               
            
            if datatype == 'csv':
                pdObjR = pd.DataFrame.from_records(passlist)
                csvData = pdObjR.to_csv(index=False, sep = ';')
                return make_response(csvData, 200)  
                        
            else:
                d = OrderedDict()
                d = {'op1_ID': op1ID, 'op2_ID': op2ID, 'RequestTimestamp': RequestTimestamp, 'PeriodFrom': dateFrom[:10], 'PeriodTo': dateTo[:10], 'NumberOfPasses' : count, 'PassesList': passlist }
                return make_response(jsonify(d), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'status': 'failed'}), 500)

"""
    Define Resource passesCost:
    (returns amount and total cost of passes involving tags of operator op2_ID and stations of operator op1_ID for the specified time period, that is the amount op2 ows op1, minus the amount op1 ows op2 (if this is negative returns 0), using the specified format (json or csv))
        Check if current_user has access to this data and arguments are valid.
        Get return list format and check its validity.
        Call passesCostB function from backend.
        If passesCostB return value indicates unavailable or nonexistant data, return corresponding error.
        Compose result dictionary. 
        If format is "csv", return result dict. as a csv form string of data with ";" as the delimeter accompanied by the successful HTTP status code.
        If format is "json", return said dict. as a JSON object accompanied by the successful HTTP status code. 

"""

class passesCost(Resource):
    @token_required
    def get(current_user, self, op1ID, op2ID, dateFrom, dateTo):
        try:
            current_user_type = getUserTypeB(current_user)
            if(current_user_type != op1ID and current_user_type != op2ID and current_user_type != 'admin'):
                return make_response(jsonify({'message' : 'Retrieving data for other users is not allowed!'}), 401)
    
            RequestTimestamp = datetime.datetime.now().strftime(timeFrmt)
            datatype = request.args.get('format')
            if (datatype and datatype !='json' and datatype != 'csv'):
                return make_response(jsonify({'status': 'failed'}), 400)
            if (not(len(op1ID) == 2) or not(len(op2ID) == 2) or (not(checkdate(dateFrom, dateTo)))):
                return make_response(jsonify({'status': 'failed'}), 400)
            dateFrom = dateFrom[:4] + '-' + dateFrom[4:6] + '-' + dateFrom[6:]+' 00:00:00'
            dateTo = dateTo[:4] + '-' + dateTo[4:6] + '-' + dateTo[6:]+' 23:59:59'
            
            ret = passesCostB(op1ID, op2ID, dateFrom, dateTo)
            if (ret == None):
                return make_response(jsonify({'status': 'failed'}), 500)
            is_owed_count = ret['is_owed_count']
            ows_count=ret['ows_count']
            if (not is_owed_count or not ows_count):
                return make_response(jsonify({'status': 'failed'}), 402)
            
            is_owed_data = ret['is_owed_data']
            ows_data=ret['ows_data']
            PassesCost = max(round(is_owed_data[0][0]-ows_data[0][0], 2), 0)
            d = OrderedDict()
            d = {'op1_ID': op1ID, 'op2_ID': op2ID, 'RequestTimestamp': RequestTimestamp, 'PeriodFrom': dateFrom[:10], 'PeriodTo': dateTo[:10], 'NumberOfPasses' : is_owed_count,'PassesCost':PassesCost}
            if datatype == 'csv':
                df = pd.DataFrame(d, index=[0])
                csvData = df.to_csv(index=False, sep = ';')
                return make_response(csvData, 200)          
            else:
                return make_response(jsonify(d), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'status': 'failed'}), 500)

"""
    Define Resource chargesBy:
    (returns list of cost of passes involving stations of operator opID and tags of any other operator subtracted by the cost of passes involving tags of operator opID and stations of each other operator, that occured in the specified time period, using the specified format (json or csv))
        Check if current_user has access to this data and arguments are valid.
        Get return list format and check its validity.
        Call chargesByB function from backend.
        If chargesByB return value indicates unavailable or nonexistant data, return corresponding error.
        For every operator x that ows to opID, subtract what opID ows to x, make a dictionary list object and add to result.
        Compose result dictionary. 
"""

class chargesBy(Resource):
    @token_required
    def get(current_user, self, opID, dateFrom, dateTo):
        try:
            current_user_type = getUserTypeB(current_user)
            if(current_user_type != opID and current_user_type != 'admin'):
                return make_response(jsonify({'message' : 'Retrieving data for other users is not allowed!'}), 401)
            RequestTimestamp  = datetime.datetime.now().strftime(timeFrmt)
            datatype = request.args.get('format')
            if (datatype and datatype !='json' and datatype != 'csv'):
                return make_response(jsonify({'status': 'failed'}), 400)
            if (not(len(opID) == 2) or not(checkdate(dateFrom, dateTo))):
                return make_response(jsonify({'status': 'failed'}), 400)
            dateFrom = dateFrom[:4] + '-' + dateFrom[4:6] + '-' + dateFrom[6:] +' 00:00:00'
            dateTo = dateTo[:4] + '-' + dateTo[4:6] + '-' + dateTo[6:] + ' 23:59:59'

            ret = chargesByB(opID, dateFrom, dateTo)
            
            if (ret == None):
                return make_response(jsonify({'status': 'failed'}), 500)
            is_owed_count = ret['is_owed_count']
            ows_count=ret['ows_count']
            if (not is_owed_count or not ows_count):
                return make_response(jsonify({'status': 'failed'}), 402)
            
            is_owed_data = ret['is_owed_data']
            ows_data=ret['ows_data']
            PPOList = []
            ows=0
            for row in is_owed_data:
                for find_ows in ows_data:
                    if(row[0]==find_ows[0]):
                        ows=find_ows[2]
                
                is_owed = round(row[2]-ows, 2)
                if is_owed<0:
                    is_owed=0

                listObj = OrderedDict()
                if datatype == 'csv':
                    listObj = {'op_ID': opID, 'RequestTimestamp':RequestTimestamp , 'PeriodFrom': dateFrom[:10], 'PeriodTo': dateTo[:10],'VisitingOperator': row[0],'NumberOfPasses':row[1], 'PassesCost':is_owed}
                else:
                    listObj = {'VisitingOperator': row[0],'NumberOfPasses':row[1], 'PassesCost':is_owed}
                PPOList.append(listObj) 
            if datatype == 'csv':
                pdObjR = pd.DataFrame.from_records(PPOList)
                csvData = pdObjR.to_csv(index=False, sep = ';')
                return make_response(csvData, 200)
            else:
                d = OrderedDict()
                d = {'op_ID': opID, 'RequestTimestamp':RequestTimestamp , 'PeriodFrom': dateFrom[:10], 'PeriodTo': dateTo[:10],'PPOList' : PPOList}
                return make_response(jsonify(d), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'status': 'failed'}), 500)
"""
    Define Resource insertPasses:
    (initialise pass table of db with default data)
        Call insertPassesB function from backend and based on its result return respective JSON object.
"""
class insertPasses(Resource):
    @token_required
    def get(current_user, self, source):
        try:
            current_user_type = getUserTypeB(current_user)
            if not current_user_type == 'admin':
                return make_response(jsonify({'message' : 'Cannot perform that function!'}), 401)
            if(insertPassesB(source)):   
                status = 'ok'
                statusCode = 200
                return make_response(jsonify({'status': status}), statusCode)
            else:
                status = 'failed'
                statusCode = 500
                return make_response(jsonify({'status': status}), statusCode)
        except:
                status = 'failed'
                statusCode = 500
                return make_response(jsonify({'status': status}), statusCode)
"""
    Define Resource login:
    (implement user login)
       Check if username and password are valid.
       Call loginB from backend.
       Based on loginB result either issue a new token and return it in a JSON object or return an error.

"""            
class login(Resource):
    def post(self):
        try:
            
            username = request.form.get('username')
            password = request.form.get('password')
            if not username:
                 return make_response(jsonify({'Authenticate' : 'Login required!'}), 401)
            if not password:
                 return make_response(jsonify({'Authenticate' : 'Login required!'}), 401)
            ret = loginB(username)
            if(ret == None):
                return make_response(jsonify({'status': 'failed'}), 500)
            count = ret['count']
            if (not count):
                return make_response(jsonify({'Authenticate': 'Wrong credentials'}), 401)
            data = ret['data']
            print(data[2])
            if check_password_hash(data[2], password):
                print("hello")
                print(password)
                print(data[2])
                
                token = jwt.encode({'user' : data[1], 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
                return jsonify({'token' : token.decode('UTF-8'), 'type' : data[0]}) 
            return make_response(jsonify({'Authenticate':'Wrong Password!'}), 401 )
        except Exception as e:
            print(e)
            return make_response(jsonify({'status': 'failed'}), 500)
"""
    Define Resource logout:
    (implement user logout)
        Get token from request and add to blacklist.

"""  

class logout(Resource):
    @token_required
    def post(current_user, self):
        global blacklist
        token = request.form.get('access-token')
        blacklist.append(token)
        return make_response(jsonify({'Authenticate':'Logged out!'}),200)

"""
    Define Resource createUser:
    (create new entry in table user of db)
        Check if current_user has access to this opperation.
        Create hashed password.
        Call createUserB from backend and based on its result return respective JSON object.

"""
class createUser(Resource):
    @token_required
    def post(current_user, self):
        try:
            current_user_type = getUserTypeB(current_user)
            if not current_user_type == 'admin':
                return make_response(jsonify({'message' : 'Cannot perform that function!'}), 401)
            username = request.form.get('username')
            password = request.form.get('password')
            user_type = request.form.get('user_type')
            hashed_password = generate_password_hash(password)
            if (createUserB(username, hashed_password, user_type)):
                status = 'ok'
                statusCode = 200
                return make_response(jsonify({'status': status}), statusCode)
            else:
                status = 'failed'
                statusCode = 500
                return make_response(jsonify({'status': status}), statusCode)
        except Exception as e:
                print(e)
                status = 'failed'
                statusCode = 500
                return make_response(jsonify({'status': status}), statusCode)
"""
    Define Resource checkUser:
    (check if user exists in db based on username)
        Check if current_user has access to this opperation.
        Call checkUserB from backend and based on its result return respective JSON object.

"""
class checkUser(Resource):
    @token_required
    def post(current_user, self):
        current_user_type = getUserTypeB(current_user)
        if(current_user_type != 'admin'):
            return make_response(jsonify({'message' : 'Cannot perform that function!'}), 401)
        
        check=checkUserB(request.form.get('username'))
        if(check==0):
            result = 'failure'
            message = 'User does not exist'
            return make_response(jsonify({'result': result, 'message': message}), 200)
        elif(check==1):
            result = 'success'
            message = 'User exists'
            return make_response(jsonify({'result': result, 'message': message}), 200)  
        status = 'failed'
        statusCode = 500
        return make_response(jsonify({'status': status}), statusCode)

"""
    Add resources to the api. Match urls to to recourses defined above.
"""

api.add_resource(healthcheck, '/interoperability/api/admin/healthcheck/')
api.add_resource(passesAnalysis, '/interoperability/api/PassesAnalysis/<op1ID>/<op2ID>/<dateFrom>/<dateTo>/')
api.add_resource(passesPerStation, '/interoperability/api/PassesPerStation/<stationID>/<dateFrom>/<dateTo>/')
api.add_resource(resetPasses, '/interoperability/api/admin/resetpasses/')
api.add_resource(resetStations, '/interoperability/api/admin/resetstations/')
api.add_resource(resetVehicles, '/interoperability/api/admin/resetvehicles/')
api.add_resource(passesCost, '/interoperability/api/PassesCost/<op1ID>/<op2ID>/<dateFrom>/<dateTo>/')
api.add_resource(chargesBy, '/interoperability/api/ChargesBy/<opID>/<dateFrom>/<dateTo>/')
api.add_resource(insertPasses,'/interoperability/api/admin/insertpasses/<source>')
api.add_resource(login, '/interoperability/api/login')
api.add_resource(createUser, '/interoperability/api/admin/createUser')
api.add_resource(logout, '/interoperability/api/logout')
api.add_resource(checkUser, '/interoperability/api/admin/checkUser')

"""
    Run app with specified port over https.
"""
if __name__ == '__main__':
    app.run(port=9103, ssl_context=('api/cert.pem', 'api/key.pem'), debug = True) 

