import mysql.connector
import pandas as pd


def createDb():
    try:
        connection = mysql.connector.connect(host='localhost', database='softeng2', user='root', password='#1*killed*PC')
        cursor = connection.cursor()
        fd = open('softeng.sql','r')
        for row in fd:  
            cursor.execute(row)
        print("done")
        connection.commit()
        cursor.close()
        connection.close()  
        fd.close()
    except Exception as e:
        print(e)

def insertPasses():
    try:
        connection = mysql.connector.connect(host='localhost', database='softeng', user='root',  password='#1*killed*PC')
        cursor = connection.cursor()
        csvdata = pd.read_csv(r'data\sampledata01_passes100_8000.csv', sep=";")
        df = pd.DataFrame(csvdata)
        for row in df.itertuples():
            (date,time) = (row.timestamp).split()
            (day, month, year) = date.split('/')
            month = '0' + month
            month = month[-2:]
            day = '0' + day
            day = day[-2:]
            if ((year == "2019") and (month == "03") and (day == "31") and (time[0] == '0') and (time[1] == '3')):
                time = "04:00"
            if ((year == "2021") and (month == "03") and (day == "28") and (time[0] == '0') and (time[1] == '3')):
                time = "04:00"
            date = year + '-' + month + '-' + day + ' ' + time + ":00"
            cursor.execute(f'''
                             INSERT INTO pass
                             VALUES (CAST('{date}' AS DATETIME),'{row.charge}','{ row.stationRef}','{row.vehicleRef}','{row.passID}')
            ''')
        connection.commit()
        cursor.close()
        connection.close()

    except Exception as e:
        print(e)



month = 1
year = 19

def refresh():
        global month
        global year
        strm = '0'+str(month)
        dateFrom = '20' + str(year) + '-' + strm[-2:] + '-01' + ' 00:00:00'
        month +=1
        if (month == 13):
            month = 1
            year +=1
        strm = '0'+str(month)
        dateTo = '20' + str(year) + '-' + strm[-2:] + '-01' + ' 00:00:00'        
        connection = mysql.connector.connect(host='localhost', database='softeng', user='root', password='#1*killed*PC')
        cursor = connection.cursor()     
        for opID in ['AO', 'MR', 'NE', 'OO', 'EG', 'GF', 'KO']:
            cursor.execute(f"""
                SELECT SUM(Charge), vehicle.operator_ID FROM pass
                INNER JOIN vehicle ON vehicle.vehicle_ID = pass.vehicle_ID
                WHERE LEFT(pass.station_ID,2) = '{opID}' 
                AND pass.timestamp BETWEEN '{dateFrom}' AND '{dateTo}' 
                AND vehicle.operator_ID <> '{opID}'
                GROUP BY vehicle.operator_ID                   
            """)
            data = cursor.fetchall()
            for row in data:
                cursor.execute(f"""
                            INSERT INTO chargesum VALUES
                            ('{row[0]}','{dateTo}',0,'{opID}','{row[1]}')
                """)
        connection.commit()
        cursor.close()



def healthcheckB():
    try:
         mysql.connector.connect(host='localhost', database='softeng', user='root', password='#1*killed*PC')
         return True
    except:
        return False

def resetPassesB():
    try:
        connection = mysql.connector.connect(host='localhost', database='softeng', user='root', password='#1*killed*PC')
        cursor = connection.cursor()
        cursor.execute('DELETE FROM pass')
        connection.commit()
        cursor.execute("UPDATE user SET password = 'freepasses4all' WHERE username = 'admin'")
        connection.commit()
        return True
    except:
        return False
    finally:
        cursor.close() 

def resetStationsB():
    try:
        connection = mysql.connector.connect(host='localhost', database='softeng', user='root', password='#1*killed*PC')
        cursor = connection.cursor()
        cursor.execute('DELETE FROM station')
        connection.commit()
        csvdata = pd.read_csv("data\sampledata01_stations.csv", sep=";")
        df = pd.DataFrame(csvdata)
        for row in df.itertuples():
            stationOp = row.stationID[:2]
            cursor.execute(f"""
                INSERT INTO Station (station_ID, station_name,operator_ID)
                VALUES ('{row.stationID}','{row.stationName}','{stationOp}')
            """)
        connection.commit()
        return True
    except:
        return False
    finally:
        cursor.close()

def resetVehiclesB():
    try:
        connection = mysql.connector.connect(host='localhost', database='softeng', user='root', password='#1*killed*PC')
        cursor = connection.cursor()
        cursor.execute(' DELETE FROM vehicle')
        connection.commit()
        csvdata = pd.read_csv("data\sampledata01_vehicles_100.csv", sep=";")
        df = pd.DataFrame(csvdata)
        for row in df.itertuples():
            cursor.execute(f""" 
                INSERT INTO Vehicle (tag_ID, vehicle_ID, license_year, balance, operator_ID)
                VALUES ('{row.tagID}','{row.vehicleID}','{row.licenseYear}',0,'{row.providerAbbr}')
            """)
        connection.commit()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        cursor.close()


def passesPerStationB(stationID, dateFrom, dateTo):
    try:
        connection = mysql.connector.connect(host='localhost', database='softeng', user='root', password='#1*killed*PC')
        cursor = connection.cursor()
        cursor.execute(f"""
                            SELECT pass.timestamp, pass.charge, pass.station_ID, pass.vehicle_ID, pass.pass_ID, vehicle.operator_ID
							FROM pass
                            INNER JOIN vehicle ON vehicle.vehicle_ID = pass.vehicle_ID
							WHERE station_ID = '{stationID}'
                            AND pass.timestamp BETWEEN '{dateFrom}' AND '{dateTo}' 
                            ORDER BY pass.timestamp

        """)
        data = cursor.fetchall()
        return  {"data": data, "count": len(data)} 
    except Exception as e:
        print(e)
        return None
    finally:
        cursor.close()


def passesAnalysisB(op1ID, op2ID, dateFrom, dateTo):
    try:
        connection = mysql.connector.connect(host='localhost', database='softeng', user='root', password='#1*killed*PC')
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT pass.timestamp, pass.charge, pass.station_ID, pass.vehicle_ID, pass.pass_ID, vehicle.operator_ID 
            FROM pass
            INNER JOIN vehicle ON vehicle.vehicle_ID = pass.vehicle_ID
            WHERE LEFT(pass.station_ID,2) = '{op1ID}' and  vehicle.operator_ID  = '{op2ID}'
            AND pass.timestamp BETWEEN '{dateFrom}' AND '{dateTo}' 
            ORDER BY pass.timestamp
        """)
        data = cursor.fetchall()
        return  {"data": data, "count": len(data)} 
    except Exception as e:
        print(e)
        return None
    finally:
        cursor.close()


def passesCostB(op1ID, op2ID, dateFrom, dateTo):
    try:
        connection = mysql.connector.connect(host='localhost', database='softeng', user='root', password='#1*killed*PC')
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT ROUND(SUM(pass.charge),2)
            FROM pass
            INNER JOIN vehicle ON vehicle.vehicle_ID = pass.vehicle_ID
            WHERE LEFT(pass.station_ID,2) = '{op1ID}' and  vehicle.operator_ID  = '{op2ID}'
            AND pass.timestamp BETWEEN '{dateFrom}' AND '{dateTo}' 
            ORDER BY pass.timestamp         
        """)
        data = cursor.fetchall()
        return  {"data": data, "count": len(data)} 
    except:
        return None
    finally:
        cursor.close()

def chargesByB(opID, dateFrom, dateTo):
    try:
        connection = mysql.connector.connect(host='localhost', database='softeng', user='root', password='#1*killed*PC')
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT vehicle.operator_ID, COUNT(*), ROUND(SUM(pass.charge),2)
            FROM pass
            INNER JOIN vehicle ON vehicle.vehicle_ID = pass.vehicle_ID
            WHERE LEFT(pass.station_ID,2) = '{opID}' 
            AND pass.timestamp BETWEEN '{dateFrom}' AND '{dateTo}' 
            AND vehicle.operator_ID <> '{opID}'
            GROUP BY vehicle.operator_ID 
        """)
        data = cursor.fetchall()
        return {"data": data, "count": len(data)}
    except:
        return None
    finally:
        cursor.close()

