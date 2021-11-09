import sys;
import subprocess;
import json;
import csv;
import pymysql.cursors;


key = None;
date = "1990-01-01"

#   get the key if not present
if key == None:
    #   terminate if no credentials given
    if len(sys.argv) != 3:
        print("Improper call. Module requires key or credentials.");
        print("Key format \"get-sales-orders.py active_key");
        print("credentials format \"get-sales-orders.py your_username your_password");
        print("Module will now terminate");
        sys.exit();
    #   get app data
    appDataF = open("application-data.dat", "r");
    appDataDict = json.loads(appDataF.read());
    #   generate the login message with encrypted password
    loginMsg = subprocess.check_output(
        [sys.executable, "login-msg.py", appDataDict["IAID"], appDataDict["IADesc"],
        appDataDict['IAName'], sys.argv[2], sys.argv[1]]
    ).decode().strip().replace("\'", "\"");
    #   generate fishbowl ready com packet in string form
    loginComm = subprocess.check_output(
        [sys.executable, "comm-builder.py", "", loginMsg]).decode().replace("\'", "\"");
    response = subprocess.check_output(
        [sys.executable, "communicate.py", loginComm]).decode();
    loginStat = json.loads(subprocess.check_output(
        [sys.executable, "login-ver.py", response]).decode().replace("'", "\""));
    key = loginStat['key'];
    if loginStat['statusCode'] != 1000:
        print("Server response " + str(loginStat['statusCode']));
        print("login failed.");
        sys.exit();
    query = ":\"SELECT so.num AS orderID, so.billToName AS customer, so.shipToAddress AS address, so.shipToCity as city, so.shipToStateId AS state, so.shipToZip AS zip, so.shipToCountryId AS country, so.dateCreated AS ordDate, so.dateFirstShip AS reqDate, so.dateCompleted AS shipDate, so.subTotal as value FROM so WHERE so.dateCreated > "
    query += "'" + date + "';\"}}";
    query = "{\"ExecuteQueryRq\": {\"Query\"" + query;
    queryMsg = subprocess.check_output(
        [sys.executable, "comm-builder.py", key, query]).decode();
    dataDump = subprocess.check_output(
        [sys.executable, "communicate.py", queryMsg]).decode();
    dataDump = json.loads(dataDump);
    dataRaw = dataDump['FbiJson']['FbiMsgsRs']['ExecuteQueryRs']['Rows']['Row'];
    index = []
    for pos in dataRaw[0].split(","):
        index += [pos.replace("\"", "")];
    index[4] = 'region';
    del dataRaw[0];
    orderData = [];
    for row in dataRaw:
        temp = {}
        i = 0
        row = row.replace(", ", " ");
        for pos in row.split(","):
            temp[index[i]] = pos.replace("\"", "");
            try:
                temp[index[i]] = float(temp[index[i]])
            except :
                None;
            i += 1
        try:
            temp[index[5]] = str(int(temp[index[5]]));
        except:
            None;
        try:
            temp[index[0]] = str(int(temp[index[0]]));
        except:
            None;
        try:
            temp[index[4]] = str(int(temp[index[4]]));
            temp[index[6]] = str(int(temp[index[6]]));
            temp[index[7]] = temp[index[7]][0:10]
            temp[index[8]] = temp[index[8]][0:10]
            temp[index[9]] = temp[index[9]][0:10]
            if temp[index[9]] == '':
                temp[index[9]] = None;
        except:
            None;
        orderData += [temp]
    print("Data imported, " + str(len(dataRaw)) + " records imported.");
    new = 0
    old = 0
    for row in orderData:
        print(row);
        connection = pymysql.connect(host='localhost',
                                        user='xanosite',
                                        password='Sr-71-Blackbird',
                                        database='fishbowl',
                                        charset='utf8mb4',
                                        cursorclass=pymysql.cursors.DictCursor)
        with connection.cursor() as cursor:
            sql = "SELECT orderID FROM salesOrders WHERE orderID = %s;";
            cursor.execute(sql, (row[index[0]]));
            SQLresponse = cursor.fetchone();
            if SQLresponse == None:
                with connection:
                    with connection.cursor() as cursor:
                        sql = "INSERT INTO salesOrders (";
                        for item in index:
                            sql += item;
                            sql += ", ";
                        sql = sql[0:len(sql)-2];
                        sql += ") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);";
                        cursor.execute(sql, (row[index[0]], row[index[1]],
                        row[index[2]], row[index[3]], row[index[4]],
                        row[index[5]], row[index[6]], row[index[7]],
                        row[index[8]], row[index[9]], row[index[10]]));
                        connection.commit();
                        new +=1;
            else:
                old += 1;
    print(str(new) + " entries made to salesOrders database.")
    print(str(old) + " existing entries found.")
