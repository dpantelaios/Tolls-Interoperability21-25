import datetime
from flask import Flask, request, jsonify, make_response, Response,  render_template
from flask_restful import Api, Resource
import datetime
import pandas as pd
from backend import *
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from collections import OrderedDict
import atexit
import jwt
from functools import wraps
from urllib.parse import urlparse

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
    
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=refresh, trigger='interval', days=30)
scheduler.add_job(func=token_cleaner, trigger='interval', minutes = 2)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

app = Flask(__name__)
api = Api(app)
path = '/interoperability/api/'
app.config['JSON_SORT_KEYS'] = False
app.config['SECRET_KEY'] = 'se2125'

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



timeFrmt = '%Y-%m-%d %H:%M:%S'

class passesPerStation(Resource):
    @token_required
    def get(current_user,self,stationID, dateFrom, dateTo):
      try:
          
            current_user_type = getUserTypeB(current_user)
            if(current_user_type != 'ministry' and current_user_type != 'admin'):
                return make_response(jsonify({'message' : 'Operation not allowed for current user'}), 401)

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

class passesCost(Resource):
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
            if(current_user_type != op1ID and current_user_type != op2ID and current_user_type != 'admin'):
                return make_response(jsonify({'message' : 'Retrieving data for other users is not allowed!'}), 401)
            ret = passesCostB(op1ID, op2ID, dateFrom, dateTo)
            if (ret == None):
                return make_response(jsonify({'status': 'failed'}), 500)
            count = ret['count']
            if (not count):
                return make_response(jsonify({'status': 'failed'}), 402)
            data = ret['data']
            PassesCost = data[0][0]
            d = OrderedDict()
            d = {'op1_ID': op1ID, 'op2_ID': op2ID, 'RequestTimestamp': RequestTimestamp, 'PeriodFrom': dateFrom[:10], 'PeriodTo': dateTo[:10], 'NumberOfPasses' : count,'PassesCost':PassesCost}
            if datatype == 'csv':
                df = pd.DataFrame(d, index=[0])
                csvData = df.to_csv(index=False, sep = ';')
                return make_response(csvData, 200)          
            else:
                return make_response(jsonify(d), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'status': 'failed'}), 500)

class chargesBy(Resource):
    @token_required
    def get(current_user, self, opID, dateFrom, dateTo):
        try:
            RequestTimestamp  = datetime.datetime.now().strftime(timeFrmt)
            datatype = request.args.get('format')
            if (datatype and datatype !='json' and datatype != 'csv'):
                return make_response(jsonify({'status': 'failed'}), 400)
            if (not(len(opID) == 2) or not(checkdate(dateFrom, dateTo))):
                return make_response(jsonify({'status': 'failed'}), 400)
            dateFrom = dateFrom[:4] + '-' + dateFrom[4:6] + '-' + dateFrom[6:] +' 00:00:00'
            dateTo = dateTo[:4] + '-' + dateTo[4:6] + '-' + dateTo[6:] + ' 23:59:59'


            current_user_type = getUserTypeB(current_user)
            if(current_user_type != opID and current_user_type != 'admin'):
                return make_response(jsonify({'message' : 'Retrieving data for other users is not allowed!'}), 401)
            
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

class insertPasses(Resource):
    @token_required
    def get(current_user, self, source):
        try:
            current_user_type = getUserTypeB(current_user)
            #print(current_user_type)
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
            

class login(Resource):
    def post(self):
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            #print(generate_password_hash(password, method='sha256'))
            if not username:
                 return make_response(jsonify({'Authenticate' : 'Login required!'}), 401)
            if not password:
                 return make_response(jsonify({'Authenticate' : 'Login required!'}), 401)
            ret = loginB(username)
            if(ret == None):
                return make_response(jsonify({'status': 'failed'}), 500)
            count = ret['count']
            if (not count):
                return make_response(jsonify({'Authenticate': 'Wrong credentials'}),401)
            data = ret['data']
            if check_password_hash(data[2], password):
                token = jwt.encode({'user' : data[1], 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
                return jsonify({'token' : token.decode('UTF-8'), 'type' : data[0]})
            return make_response(jsonify({'Authenticate':'Wrong Password!'}), 401 )
        except Exception as e:
            print(e)
            return make_response(jsonify({'status': 'failed'}), 500)

class logout(Resource):
    @token_required
    def post(current_user, self):
        #print("Called")
        global blacklist
        token = request.form.get('access-token')
        blacklist.append(token)
        return make_response(jsonify({'Authenticate':'Logged out!'}),200)

class createUser(Resource):
    @token_required
    def post(current_user, self):
        try:
            ##check authentication type==admin
            current_user_type = getUserTypeB(current_user)
            #print(current_user_type)
            if not current_user_type == 'admin':
                return make_response(jsonify({'message' : 'Cannot perform that function!'}), 401)
            username = request.form.get('username')
            password = request.form.get('password')
            user_type = request.form.get('user_type')
            hashed_password = generate_password_hash(password, method='sha256')
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

if __name__ == '__main__':
    app.run(port=9103, ssl_context=('cert.pem', 'key.pem'), debug = True) 

