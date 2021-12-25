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

scheduler = BackgroundScheduler()
scheduler = AsyncIOScheduler(timezone="Europe/Athens")
scheduler.add_job(func=refresh, trigger="interval", days=30)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

app = Flask(__name__)
api = Api(app)
path = '/interoperability/api/'
app.config['JSON_SORT_KEYS'] = False

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
            return make_response(jsonify({'status': status,'dbconnection': dbconnection}), statusCode)

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

class insertPasses(Resource):
    def post(self):
        try:
            if(insertPassesB()): 
                print("All good")   
                status = 'ok'
                statusCode = 200
            else:
                print("function returned false")
                status = 'failed'
                statusCode = 500
        except:
                print("exception during call")
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
                    PassType = "home"
                listObj = {"PassIndex": i, "PassID": row[4],"PassTimeStamp": row[0].strftime(timeFrmt), "VehicleID": row[3], "TagProvider":TagProvider  ,"PassType": PassType, "PassCharge": row[1]}
                passlist.append(listObj)               
            d = OrderedDict()
            d = {"Station":stationID, "StationOperator": stationID[:2], "RequestTimestamp":RequestTimestamp, "PeriodFrom" : dateFrom[:10], "PeriodTo" : dateTo[:10], "NumberOfPasses" : count }
            if datatype == "csv":
                pdObjS = pd.DataFrame([d])
                pdObjR = pd.DataFrame.from_records(passlist)
                csvDataS = pdObjS.to_csv(index=False, sep = ';')
                csvDataR = pdObjR.to_csv(index=False, sep = ';')
                csvData = csvDataS+csvDataR
                cd = 'attachment; filename=PassesPerStation{}_{}_{}.csv'.format(stationID, dateFrom[:10], dateTo[:10])
                response = make_response(csvData)
                response.headers['Content-Disposition'] = cd
                response.mimetype = "text/csv"
                return response 
            else:
                d["PassesList"] = passlist
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
                listObj = {"PassIndex": i, "PassID": row[4],"StationID":row[2], "TimeStamp": row[0].strftime(timeFrmt), "VehicleID": row[3], "Charge": row[1]}
                passlist.append(listObj)   
            d = OrderedDict()            
            d = {'op1_ID': op1ID, 'op2_ID': op2ID, 'RequestTimestamp': RequestTimestamp, 'PeriodFrom': dateFrom[:10], 'PeriodTo': dateTo[:10], "NumberOfPasses" : count}
            if datatype == "csv":
                pdObjS = pd.DataFrame([d])
                pdObjR = pd.DataFrame.from_records(passlist)
                csvDataS = pdObjS.to_csv(index=False, sep = ';')
                csvDataR = pdObjR.to_csv(index=False, sep = ';')
                csvData = csvDataS+csvDataR
                cd = 'attachment; filename=PassesAnalysis{}_{}_{}_{}'.format(op1ID,op2ID,dateFrom[:10],dateTo[:10])
                response = make_response(csvData)
                response.headers['Content-Disposition'] = cd
                response.mimetype = "text/csv"
                return response 
            else:
                d["PassesList"]= passlist 
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
            d = {'op1_ID': op1ID, 'op2_ID': op2ID, 'RequestTimestamp': RequestTimestamp, 'PeriodFrom': dateFrom[:10], 'PeriodTo': dateTo[:10], "NumberOfPasses" : count,'PassesCost':PassesCost}
            if datatype == "csv":
                df = pd.DataFrame(d, index=[0])
                csvData = df.to_csv(index=False, sep = ';')
                cd = 'attachment; filename=PassesCost{}_{}_{}_{}'.format(op1ID,op2ID,dateFrom[:10],dateTo[:10])
                response = make_response(csvData)
                response.headers['Content-Disposition'] = cd
                response.mimetype = "text/csv"
                return response 
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
                listObj = {'VisitingOperator': row[0],'NumberOfPasses':row[1], 'PassesCost':row[2]}              
                PPOList.append(listObj) 
            d = OrderedDict()
            d = {'op_ID': opID, 'RequestTimestamp':RequestTimestamp , 'PeriodFrom': dateFrom[:10], 'PeriodTo': dateTo[:10]}
            if datatype == "csv":
                pdObjS = pd.DataFrame([d])
                pdObjR = pd.DataFrame.from_records(PPOList)
                csvDataS = pdObjS.to_csv(index=False, sep = ';')
                csvDataR = pdObjR.to_csv(index=False, sep = ';')
                csvData = csvDataS+csvDataR
                cd = 'attachment; filename=ChargesBy{}_{}_{}'.format(opID,dateFrom[:10],dateTo[:10])
                response = make_response(csvData)
                response.headers['Content-Disposition'] = cd
                response.mimetype = "text/csv"
                return response 
            else:
                d['PPOList'] = PPOList
                return make_response(jsonify(d), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'status': 'failed'}), 500)


api.add_resource(healthcheck, '/interoperability/api/admin/healthcheck/')
api.add_resource(passesAnalysis, '/interoperability/api/PassesAnalysis/<op1ID>/<op2ID>/<dateFrom>/<dateTo>/')
api.add_resource(passesPerStation, '/interoperability/api/PassesPerStation/<stationID>/<dateFrom>/<dateTo>/')
api.add_resource(resetPasses, '/interoperability/api/admin/resetpasses/')
api.add_resource(resetStations, '/interoperability/api/admin/resetstations/')
api.add_resource(resetVehicles, '/interoperability/api/admin/resetvehicles/')
api.add_resource(passesCost, '/interoperability/api/PassesCost/<op1ID>/<op2ID>/<dateFrom>/<dateTo>/')
api.add_resource(chargesBy, '/interoperability/api/ChargesBy/<opID>/<dateFrom>/<dateTo>/')
api.add_resource(insertPasses,'/interoperability/api/insertPasses')

if __name__ == '__main__':
    #app.run(host='127.0.0.1',port=9103)
    app.run(port=9103, ssl_context=('cert.pem', 'key.pem'),debug=True)  

