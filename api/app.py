import datetime
from flask import Flask, request, jsonify, make_response, Response 
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

scheduler = BackgroundScheduler()
scheduler = AsyncIOScheduler(timezone='Europe/Athens')
scheduler.add_job(func=refresh, trigger='interval', days=30)
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
        token = None
        if 'access-token' in request.headers:
            token = request.headers['access-token']

        if not token:
            return make_response(jsonify({'message' : 'Token is missing!'}), 401)
        try: 
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = data['user']
        except:
            return make_response(jsonify({'message' : 'Token is invalid!'}), 401)

        #return f(*args, **kwargs)
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
    def get(self, stationID, dateFrom, dateTo):
      try:
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
    def get(self, op1ID, op2ID, dateFrom, dateTo):
        try:
            RequestTimestamp = datetime.datetime.now().strftime(timeFrmt)
            datatype = request.args.get('format')
            if (datatype and datatype !='json' and datatype != 'csv'):
                return make_response(jsonify({'status': 'failed'}), 400)
            if (not(len(op1ID) == 2) or not(len(op2ID) == 2) or (not(checkdate(dateFrom, dateTo)))):
                return make_response(jsonify({'status': 'failed'}), 400)    
            dateFrom = dateFrom[:4] + '-' + dateFrom[4:6] + '-' + dateFrom[6:]+' 00:00:00'
            dateTo = dateTo[:4] + '-' + dateTo[4:6] + '-' + dateTo[6:]+' 23:59:59'
            ret = passesAnalysisB(op1ID, op2ID, dateFrom, dateTo)
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
    def get(self, op1ID, op2ID, dateFrom, dateTo):
        try:
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
    def get(self, opID, dateFrom, dateTo):
        try:
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
            count = ret['count']
            if (not count):
                return make_response(jsonify({'status': 'failed'}), 402)
            data = ret['data']
            PPOList = []
            for row in data:            
                listObj = OrderedDict()
                if datatype == 'csv':
                    listObj = {'op_ID': opID, 'RequestTimestamp':RequestTimestamp , 'PeriodFrom': dateFrom[:10], 'PeriodTo': dateTo[:10],'VisitingOperator': row[0],'NumberOfPasses':row[1], 'PassesCost':row[2]}
                else:
                    listObj = {'VisitingOperator': row[0],'NumberOfPasses':row[1], 'PassesCost':row[2]}
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
    def get(self, source):
        try:
            if(insertPassesB(source)):   
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

class login(Resource):
    def post(self):
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
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
                return jsonify({'token' : token.decode('UTF-8')})
            return make_response(jsonify({'Authenticate':'Wrong Password!'}), 401 )
        except Exception as e:
            print(e)
            return make_response(jsonify({'status': 'failed'}), 500)

class createUser(Resource):
    @token_required
    def post(current_user, self):
        try:
            ##check authentication type==admin
            current_user_type=getUserTypeB(current_user)
            print(current_user_type)
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

if __name__ == '__main__':
    app.run(port=9103, ssl_context=('cert.pem', 'key.pem'),debug=True) 