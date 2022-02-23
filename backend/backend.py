import mysql.connector
import pandas as pd
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

"""
    MySql db info
    Used to connect to database
"""

standard = {
    'host': 'localhost', 
    'database': 'softeng', 
    'user': 'root', 
    'password': '#1*killed*PC', 
    'port': 3306, 
    'auth_plugin': 'mysql_native_password'
}

"""
   Define login function: 
        Get tupple from table user of db with username=username
        Return dictionary with tupple and indicator of existance of user. 
"""

def loginB(username):
    try:   
        connection = mysql.connector.connect(**standard)
        cursor = connection.cursor() 
        cursor.execute(f'''
                             SELECT * FROM user 
                             WHERE username = '{username}'
        ''')
        data = cursor.fetchone()
        return  {"data": data, "count": len(data)}
    except Exception as e:
        print(e)
        return None
    finally:
        cursor.close()

"""
    Define database loading function:
        Open and execute db dump file
"""
def createDb():
    try:
        connection = mysql.connector.connect(**standard)
        cursor = connection.cursor()
        fd = open('softeng.sql','r')
        for row in fd:  
            cursor.execute(row)
        connection.commit()
        cursor.close()
        connection.close()  
        fd.close()
    except Exception as e:
        print(e)

"""
    Define function insertPassesB:
    (fills table pass of db with data from "source" file)
        Read csv file.
        For every row of csv file, format date and time to be SQL DATETIME compatible and insert tupple in table pass of db.            
"""
def insertPassesB(source):
    try:
        connection = mysql.connector.connect(**standard)
        print("Connected")
        cursor = connection.cursor()
        file_path= "data"+"\\" +source
        print(file_path)
        csvdata = pd.read_csv(file_path, sep=";")
        df = pd.DataFrame(csvdata)
        for row in df.itertuples():
            (date,time) = (row.timestamp).split()
            (day, month, year) = date.split('/')
            month = '0' + month
            month = month[-2:]
            day = '0' + day
            day = day[-2:]
            if ((month =='03') and (time[:2] == '03') and ((year == '2019' and day == '31') or (year == '2021' and day == '28'))):
                time = '04:00'
            date = year + '-' + month + '-' + day + ' ' + time + ":00"
            cursor.execute(f'''
                             INSERT INTO pass
                             VALUES (CAST('{date}' AS DATETIME),'{row.charge}','{ row.stationRef}','{row.vehicleRef}','{row.passID}')
            ''')
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        print(e)
        return False

month = 1
year = 19

"""
    Define scheduler job function:
    (fills table chargesum of db)
        For every operator, find sum of charges that are owed this month by all the other operators and group by operator. 
        Add tupples to chargesum table of db. 
"""
def refresh():
        global month
        global year
        strm = '0' + str(month)
        dateFrom = '20' + str(year) + '-' + strm[-2:] + '-01' + ' 00:00:00'
        month +=1
        if (month == 13):
            month = 1
            year +=1
        strm = '0'+str(month)
        dateTo = '20' + str(year) + '-' + strm[-2:] + '-01' + ' 00:00:00'        
        connection = mysql.connector.connect(**standard)
        cursor = connection.cursor()     
        for opID in ['AO', 'MR', 'NE', 'OO', 'EG', 'GF', 'KO']:
            cursor.execute(f"""
                SELECT SUM(Charge), vehicle.operator_ID FROM pass
                INNER JOIN vehicle ON vehicle.vehicle_ID = pass.vehicle_ID
                WHERE LEFT(pass.station_ID,2) = '{opID}' 
                AND pass.pass_time BETWEEN '{dateFrom}' AND '{dateTo}' 
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

"""
    Define function healthcheckB:
        Attempt connection to db and return result.
"""
def healthcheckB():
    try:
        mysql.connector.connect(**standard)
        return True
    except:
        return False

"""
    Define function resetPassesB:
        Delete all entries from table pass of db and insert admin user with password freepasses4all to table user of db.
"""
def resetPassesB():
    try:
        connection = mysql.connector.connect(**standard)
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
"""
    Define function resetStationsB:
    (reset entries in station table of db)
        Delete all entries from table station of db.
        Read csv file.
        For every entry of csv file, get needed data and add to table station of db.
"""
def resetStationsB():
    try:
        connection = mysql.connector.connect(**standard)
        cursor = connection.cursor()
        cursor.execute('DELETE FROM station')
        connection.commit()
        csvdata = pd.read_csv( r"..\sampledata01\sampledata01_stations.csv" , sep=";")
        df = pd.DataFrame(csvdata)
        for row in df.itertuples():
            stationOp = row.stationID[:2]
            cursor.execute(f"""
                INSERT INTO station (station_ID, station_name,operator_ID)
                VALUES ('{row.stationID}','{row.stationName}','{stationOp}')
            """)
        connection.commit()
        return True
    except:
        return False
    finally:
        cursor.close()
"""
    Define function resetVehiclesB:
    (reset entries in vehicle table of db)
        Delete all entries from table vehicle of db.
        Read csv file.
        For every entry of csv file, get needed data, initialise balance at value zero and add to table vehicle of db. 
"""
def resetVehiclesB():
    try:
        connection = mysql.connector.connect(**standard)
        cursor = connection.cursor()
        cursor.execute(' DELETE FROM vehicle')
        connection.commit()
        csvdata = pd.read_csv(r"..\sampledata01\sampledata01_vehicles_100.csv", sep=";")
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

"""
    Define function passesPerStationB:
    (Gets passes from stationID that occured between the dates given in function call, from table pass of db)
        Execute query on db.
        Fetch results.
        Return dictionary with results and number of tupples in results.        
"""
def passesPerStationB(stationID, dateFrom, dateTo):
    try:
        connection = mysql.connector.connect(**standard)
        cursor = connection.cursor()
        cursor.execute(f"""
                            SELECT pass.pass_time, pass.charge, pass.station_ID, pass.vehicle_ID, pass.pass_ID, vehicle.operator_ID
							FROM pass
                            INNER JOIN vehicle ON vehicle.vehicle_ID = pass.vehicle_ID
							WHERE station_ID = '{stationID}'
                            AND pass.pass_time BETWEEN '{dateFrom}' AND '{dateTo}' 
                            ORDER BY pass.pass_time
        """)
        data = cursor.fetchall()
        return  {"data": data, "count": len(data)} 
    except Exception as e:
        print(e)
        return None
    finally:
        cursor.close()

"""
    Define function passesAnalysisB:
    (Gets passes involving tags of operator op2ID and stations of operator op1ID that occured between the dates specified in function call)
        Execute query on db. 
        Fetch results.
        Return dictionary with results and number of tupples in results.        
"""
def passesAnalysisB(op1ID, op2ID, dateFrom, dateTo):
    try:
        connection = mysql.connector.connect(**standard)
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT pass.pass_time, pass.charge, pass.station_ID, pass.vehicle_ID, pass.pass_ID, vehicle.operator_ID 
            FROM pass
            INNER JOIN vehicle ON vehicle.vehicle_ID = pass.vehicle_ID
            WHERE LEFT(pass.station_ID,2) = '{op1ID}' and  vehicle.operator_ID  = '{op2ID}'
            AND pass.pass_time BETWEEN '{dateFrom}' AND '{dateTo}' 
            ORDER BY pass.pass_time
        """)
        data = cursor.fetchall()
        return  {"data": data, "count": len(data)} 
    except Exception as e:
        print(e)
        return None
    finally:
        cursor.close()

"""
    Define fuction passesCostB:
    (Gets sum (with precision of two decimals) and amount of passes involving tags of operator op2ID and stations of operator op1ID that occured between the dates specified in function call)
        Execute query on db.
        Fetch results.
        Return dictionary with results and number of tupples in results.        
"""
def passesCostB(op1ID, op2ID, dateFrom, dateTo):
    try:
        connection = mysql.connector.connect(**standard)
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT ROUND(SUM(pass.charge),2)
            FROM pass
            INNER JOIN vehicle ON vehicle.vehicle_ID = pass.vehicle_ID
            WHERE LEFT(pass.station_ID,2) = '{op1ID}' and  vehicle.operator_ID  = '{op2ID}'
            AND pass.pass_time BETWEEN '{dateFrom}' AND '{dateTo}' 
            ORDER BY pass.pass_time         
        """)
        data = cursor.fetchall()
        return  {"data": data, "count": len(data)} 
    except:
        return None
    finally:
        cursor.close()
"""
    Define function chargesByB:
    (Gets two sets of data. The first is the sum (with precision of two decimals) and amount of passes involving stations of operator opID and tags of any other opperator that occured between the dates specified in function call.
        The second is the sum (with precision of two decimals) and amount of passes involving tags of operator opID and stations of any other operator, that occur in the specified time period)
        Execute query on db.
        Fetch results.
        Return dictionary with results and number of tupples in results.       
"""
def chargesByB(opID, dateFrom, dateTo):
    try:
        connection = mysql.connector.connect(**standard)
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT vehicle.operator_ID, COUNT(*), ROUND(SUM(pass.charge),2)
            FROM pass
            INNER JOIN vehicle ON vehicle.vehicle_ID = pass.vehicle_ID
            WHERE LEFT(pass.station_ID,2) = '{opID}' 
            AND pass.pass_time BETWEEN '{dateFrom}' AND '{dateTo}' 
            AND vehicle.operator_ID <> '{opID}'
            GROUP BY vehicle.operator_ID 
        """)
        is_owed_data = cursor.fetchall()

        cursor.execute(f"""
            SELECT LEFT(pass.station_ID,2), COUNT(*), ROUND(SUM(pass.charge),2)
            FROM pass
            INNER JOIN vehicle ON vehicle.vehicle_ID = pass.vehicle_ID
            WHERE vehicle.operator_ID = '{opID}' 
            AND pass.pass_time BETWEEN '{dateFrom}' AND '{dateTo}' 
            AND LEFT(pass.station_ID,2) <> '{opID}'
            GROUP BY LEFT(pass.station_ID,2) 
        """)
        ows_data = cursor.fetchall()

        return {"is_owed_data": is_owed_data, "is_owed_count": len(is_owed_data), "ows_data": ows_data, "ows_count": len(ows_data)}
    except:
        return None
    finally:
        cursor.close()
"""
    Define function createUserB:
    (Creates or updates entry of table user with given username, password and type)
        Check if entry of table user with given username exists.
        If it does not, insert new tupple into table.
        Else update tupple.
"""
def createUserB(username, password, type):
    try:
        connection = mysql.connector.connect(**standard)
        cursor = connection.cursor()
        cursor.execute(f""" 
                SELECT* FROM user WHERE username = '{username}'
        """)
        if(len(cursor.fetchall()) == 0):
            cursor.execute(f"""
                INSERT INTO user(username, password, type) VALUES
                ('{username}','{password}','{type}')
            """)
        else:
            cursor.execute(f"""
                UPDATE user SET password = '{password}' WHERE username = '{username}'
            """)
            
        connection.commit()    
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        cursor.close()

"""
    Define function getUserTypeB:
    (Gets type from entry of table user of db with specified username)
        Find entry of table user with given username.
        Return type.
"""
def getUserTypeB(username):
    try:
        connection = mysql.connector.connect(**standard)
        cursor = connection.cursor()
        cursor.execute(f""" 
                SELECT type FROM user WHERE username = '{username}'
        """)   
        data = cursor.fetchone()
        return data[0]
    except Exception as e:
        print(e)
        return None
    finally:
        cursor.close()
"""
    Define function checkUserB:
    (Checks if entry in table user of db with specified username exists)
        Execute query and return result.
"""
def checkUserB(username):
    try:
        connection = mysql.connector.connect(**standard)
        cursor = connection.cursor()
        cursor.execute(f""" 
                SELECT * FROM user WHERE username = '{username}'
        """)   
        data = cursor.fetchone()
        if(data is not None):
            return 1
        else:
            return 0
    except Exception as e:
        print(e)
        return -1
    finally:
        cursor.close()
