import argparse, requests
import urllib3
import csv
import sys
import pickle
import json
from termcolor import colored
urllib3.disable_warnings()
 #pip3 install urllib3==1.23

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        print(colored("Invalid Parameters!", 'red'))
        print(colored("Required parameters for every scope:", 'red'))
        print("")

        print(colored("healthckeck", 'blue'))
        print("\t No parameters")
        print("")

        print(colored("resetpasses", 'blue'))
        print("\t No parameters")
        print("")

        print(colored("resetstations", 'blue'))
        print("\t No parameters")
        print("")

        print(colored("resetvehicles", 'blue'))
        print("\t No parameters")
        print("")

        print(colored("passesperstation", 'blue'))
        print("\t --station --datefrom --dateto --format={json, csv}")
        print("")

        print(colored("passesanalysis", 'blue'))
        print("\t --op1 --op2 --datefrom --dateto --format={json, csv}")
        print("")

        print(colored("passescost", 'blue'))
        print("\t --op1 --op2 --datefrom --dateto --format={json, csv}")
        print("")

        print(colored("chargesby", 'blue'))
        print("\t --op1 --datefrom --dateto --format={json, csv}")
        print("")

        print(colored("admin", 'blue'))
        print("\t --passesupd --source")
        #self.print_help()
        sys.exit(2)

def main():
    
    parser = MyParser()
    subparsers = parser.add_subparsers()
    
    login_parser = subparsers.add_parser('login')
    login_parser.set_defaults(func=login)
    login_parser.add_argument('--username', type=str, required=True)
    login_parser.add_argument('--password', type=str, required=True)

    logout_parser = subparsers.add_parser('logout')
    logout_parser.set_defaults(func=logout)

    healthcheck_parser = subparsers.add_parser('healthcheck')
    healthcheck_parser.set_defaults(func=healthcheck)

    resetpasses_parser = subparsers.add_parser('resetpasses')
    resetpasses_parser.set_defaults(func=resetpasses)

    resetstations_parser = subparsers.add_parser('resetstations')
    resetstations_parser.set_defaults(func=resetstations)

    resetvehicles_parser = subparsers.add_parser('resetvehicles')
    resetvehicles_parser.set_defaults(func=resetvehicles)
    
    passesPerStation_parser = subparsers.add_parser('passesperstation')
    passesPerStation_parser.set_defaults(func=passesPerStation)
    passesPerStation_parser.add_argument('--station', type=str,required=True)
    passesPerStation_parser.add_argument('--datefrom', type=str,required=True)
    passesPerStation_parser.add_argument('--dateto', type=str,required=True)
    passesPerStation_parser.add_argument('--format', type=str,required=True)
    
    passesAnalysis_parser = subparsers.add_parser('passesanalysis')
    passesAnalysis_parser.set_defaults(func=passesAnalysis)
    passesAnalysis_parser.add_argument('--op1', type=str,required=True)
    passesAnalysis_parser.add_argument('--op2', type=str,required=True)
    passesAnalysis_parser.add_argument('--datefrom', type=str,required=True)
    passesAnalysis_parser.add_argument('--dateto', type=str,required=True)
    passesAnalysis_parser.add_argument('--format', type=str,required=True)


    passesCost_parser = subparsers.add_parser('passescost')
    passesCost_parser.set_defaults(func=passesCost)
    passesCost_parser.add_argument('--op1', type=str,required=True)
    passesCost_parser.add_argument('--op2', type=str,required=True)
    passesCost_parser.add_argument('--datefrom', type=str,required=True)
    passesCost_parser.add_argument('--dateto', type=str,required=True)
    passesCost_parser.add_argument('--format', type=str,required=True)
 
    chargesBy_parser = subparsers.add_parser('chargesby')
    chargesBy_parser.set_defaults(func=chargesBy)
    chargesBy_parser.add_argument('--op1', type=str,required=True)
    chargesBy_parser.add_argument('--datefrom', type=str,required=True)
    chargesBy_parser.add_argument('--dateto', type=str,required=True)
    chargesBy_parser.add_argument('--format', type=str,required=True)

    admin_parser = subparsers.add_parser('admin')
    admin_parser.set_defaults(func=admin)
    admin_parser.add_argument('--passesupd', action="store_true")
    admin_parser.add_argument('--source', type=str,required=True)



    try:
       args = parser.parse_args()
       args.func(args)
    except Exception as e:
        print("**")
        print(e)   


def read_token():
    try:
        with open('token.to','r') as f:
           return f.read()
    except:
        return None

def login (args):
    body={'username': args.username, 'password': args.password}
    response = requests.post("https://127.0.0.1:9103/interoperability/api/login", data=body, verify=False)
    try:
        ret = dict(response.json())
        #print(ret['token'])  
        with open('token.to','w') as f:
            f.write(ret['token'])
        #pip3 install urllib3==1.23
        print(json.dumps({'Authenticate':'Successful login!'}))

    except Exception as e:
        #print(e)
        print(response.json())

def logout(args):
    token = read_token()
    if(token is None):
        print(json.dumps({'Authenticate':'You must login first!'}))
    else:
        our_headers={'access-token': token}
        body={'access-token': token}
        response = requests.post("https://127.0.0.1:9103/interoperability/api/logout", headers=our_headers, data=body, verify=False)
        print(response.json())

def healthcheck(args):
    response = requests.get("https://127.0.0.1:9103/interoperability/api/admin/healthcheck/", verify=False)
    #pip3 install urllib3==1.23
    print(response.json())


def resetpasses(args):
    response = requests.post("https://127.0.0.1:9103/interoperability/api/admin/resetpasses/", verify=False)
    print(response.json())


def resetstations(args):
    response = requests.post("https://127.0.0.1:9103/interoperability/api/admin/resetstations/", verify=False)
    print(response.json())

def resetvehicles(args):
    response = requests.post("https://127.0.0.1:9103/interoperability/api/admin/resetvehicles/", verify=False)
    print(response.json())
    
def passesPerStation(args): #i removed try-except not needed?
    token = read_token()

    if(token is None):
        print(json.dumps({'Authenticate':'You must login first!'}))
    else:
        our_headers={'access-token': token}
        link = "https://127.0.0.1:9103/interoperability/api/PassesPerStation/" + args.station + "/" + args.datefrom + "/" + args.dateto + "?format="+args.format
        response = requests.get(link, headers=our_headers, verify=False)
        
        if (response.status_code==200):
            if args.format == "json":
                print(response.json())
            else:
                decoded_content = response.content.decode('utf-8')
                cr = csv.reader(decoded_content.splitlines(), delimiter=';')
                my_list = list(cr)
                for row in my_list:
                    print(row)
        else:
            print(response.json())


def passesAnalysis(args):
    token = read_token()
    
    if(token is None):
        print(json.dumps({'Authenticate':'You must login first!'}))
    else:
        our_headers={'access-token': token}
        link = "https://127.0.0.1:9103/interoperability/api/PassesAnalysis/" + args.op1 + "/" + args.op2 + "/" + args.datefrom + "/" + args.dateto + "?format="+args.format
        response = requests.get(link, headers=our_headers, verify=False)
        if (response.status_code==200):
            if args.format == "json":
                print(response.json())
            else:
                decoded_content = response.content.decode('utf-8')
                cr = csv.reader(decoded_content.splitlines(), delimiter=';')
                my_list = list(cr)
                for row in my_list:
                    print(row)
        else:
            print(response.json())

def passesCost(args):
    token = read_token()
    if(token is None):
        print(json.dumps({'Authenticate':'You must login first!'}))
    else:
        our_headers={'access-token': token}
        link = "https://127.0.0.1:9103/interoperability/api/PassesCost/" + args.op1 + "/" + args.op2 + "/" + args.datefrom + "/" + args.dateto + "?format="+args.format
        #print(link)
        response = requests.get(link, headers=our_headers, verify=False)
        #print(response.status_code)
        if (response.status_code==200):
            if args.format == "json":
                print(response.json())
            else:
                decoded_content = response.content.decode('utf-8')
                cr = csv.reader(decoded_content.splitlines(), delimiter=';')
                my_list = list(cr)
                for row in my_list:
                    print(row)
        else:
            print(response.json())

def chargesBy(args):
    token = read_token()
    if(token is None):
        print(json.dumps({'Authenticate':'You must login first!'}))
    else:
        our_headers={'access-token': token}
        link = "https://127.0.0.1:9103/interoperability/api/ChargesBy/" + args.op1 + "/" + args.datefrom + "/" + args.dateto + "?format="+args.format
        #print(link)
        response = requests.get(link, headers=our_headers, verify=False)
        #print(response.status_code)
        if (response.status_code==200):
            if args.format == "json":
                print(response.json())
            else:
                decoded_content = response.content.decode('utf-8')
                cr = csv.reader(decoded_content.splitlines(), delimiter=';')
                my_list = list(cr)
                for row in my_list:
                    print(row)
        else:
            print(response.json())

def admin(args):
    if(args.passesupd):
        token = read_token()
        if(token is None):
            print(json.dumps({'Authenticate':'You must login first!'}))
        else:
            our_headers={'access-token': token}
            link="https://127.0.0.1:9103/interoperability/api/admin/insertpasses/"+args.source
            response = requests.get(link, headers=our_headers, verify=False)
            print(response.json())

if __name__ == '__main__':
    main()

