import sys
import pandas as pd
import socket
import re
import pickle
import threading
import signal
import os
import time
import ctypes

# global variables
clientdf = pd.DataFrame(columns=['Filename','Owner','Client IP Address','Port', 'File Directory'])
serverdf = pd.DataFrame(columns=['name','online-status', 'IPaddress', 'TCPport', 'UDPport', 'filenames', 'file-dirs'])
serverdf = serverdf.astype('object')
serverfiledf = pd.DataFrame(columns=['Filename','Owner','Client IP Address','Port', 'File Directory'])
myClientIP = None
ACKMessage = None
ACKClient = None
searchDir = None
ACKFileOffer = False
TCPListen = True
isderegACKed = False
isOffline = False

mode = sys.argv[1]

# error checking functions
def checkPortNum(portNum):
    # takes in string version of portNum and returns integer version if valid
    try:
        portNum = int(portNum)
    except:
        sys.exit(">>> [ERROR: Port number not an integer]")
    
    if portNum < 1024 or portNum > 65535:
        sys.exit(">>> [ERROR: Port number out of range]")
    
    return portNum

def checkIPAddress(ip):
    # valid: four integers ranging from 0-255 separated by 3 dots
    pattern = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
    if not (re.search(pattern,ip)):
        sys.exit(">>> [ERROR: Invalid IP Address]")

# class for killing thread upon timeout
class thread_with_exception(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
             
    def run(self):
        global ACKMessage
        global ACKClient
        ACKMessage, ACKClient = serverSock.recvfrom(2048)   
          
    def get_id(self):
 
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id
  
    def raise_exception(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
              ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')        

#server mode
if mode =='-s':
    # preliminary error checking
    if len(sys.argv) != 3: # check command line arguments
        sys.exit(">>> [ERROR: Incorrect Number of Arguments]")
    port = checkPortNum(sys.argv[2])
    try:
        serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serverSock.bind(("localhost", port))
    except:
        sys.exit(">>> [ERROR: Failed Connection - already used server port.]")
    
    # FUNCTION AREA FOR SERVER
    def transformDF():
        tempdf = pd.DataFrame(columns=['Filename','Owner','Client IP Address','Port', 'File Directory'])
        for index, row in serverdf.iterrows():
            files = row['filenames'].split()
            dirs = row['file-dirs'].split()
            if len(files) > 0:
                for i in range(0,len(files)):
                    fileli = [files[i], row['name'], row['IPaddress'], row['TCPport'],dirs[i]]
                    tempdf.loc[len(tempdf.index)] = fileli
        return tempdf
       
    def checkACK():
        global ACKMessage
        global ACKClient
        ACKMessage, ACKClient = serverSock.recvfrom(2048)             
    
    def broadcastTable():
        # tempdf to store only online client info
        tempdf = pd.DataFrame(columns=['Filename','Owner','Client IP Address','Port', 'File Directory'])
        # list of all active client names
        activeli = serverdf.loc[serverdf['online-status'] == True, 'name'].tolist()
        for index, row in serverfiledf.iterrows():
            if row['Owner'] in activeli:
                tempdf.loc[len(tempdf.index)] = row.tolist()

        activedf = serverdf.loc[serverdf['online-status'] == True]
        for index, row in activedf.iterrows():
            activeIP = row['IPaddress']
            activeUDP = int(row['UDPport'])
            serverSock.sendto(pickle.dumps(tempdf, protocol=4), (activeIP, activeUDP))
                
                
                
                    
    while True:
        try:
            message, clientAddress = serverSock.recvfrom(2048)
            clientIP = clientAddress[0]
            try:    # pickle message of list
                message =  pickle.loads(message) 
                if message[0] == "REGISTRATION:":
                    # check if name already exists
                    if message[1] in serverdf['name'].values:
                        errorMsg = ">>> [ERROR: Registration rejected. Username already taken.]"
                        serverSock.sendto(errorMsg.encode(), clientAddress)
                        continue
                    regli = [message[1], message[2], clientIP, message[3], message[4], message[5], message[6]]
                    serverdf.loc[len(serverdf.index)] = regli
                    regSuccess = ">>> [Welcome, You are registered.]"
                    serverSock.sendto(regSuccess.encode(), clientAddress)
                    yourIP = 'YourIP: '+ clientIP
                    serverSock.sendto(yourIP.encode(), clientAddress)
                    serverfiledf = transformDF()
                    count = 0
                    while count < 3:
                        serverSock.sendto(pickle.dumps(serverfiledf, protocol=4), clientAddress)
                        checkACKThread = thread_with_exception()
                        checkACKThread.start()
                        time.sleep(0.5)
                        checkACKThread.raise_exception()
                        checkACKThread.join()
                        if ACKMessage != None and ACKClient!= None: #received something from client
                            try:
                                ACKMessage = ACKMessage.decode().split()
                                if ACKMessage[0] == "ACKTableUpdate:" and ACKMessage[1] == ACKClient[0] and ACKMessage[2] == str(ACKClient[1]):
                                    # ACK Message from the right client
                                    #print("client ACK received") 
                                    ACKMessage = None
                                    ACKClient = None
                                    break
                                else:
                                    # any message that is not the ACK Table Update just have to be dropped?
                                    count += 1
                            except:
                                count += 1
                        else:
                            count+=1
                elif message[0]== "FILEOFFER:":
                    serverSock.sendto("ACKFileOffer".encode(), clientAddress)         
                    message = message[1:]
                    # offerFiles = []
                    currfilenames = serverdf.loc[(serverdf['IPaddress'] == clientAddress[0]) & (serverdf['UDPport'] == str(clientAddress[1])), 'filenames']
                    currfilepaths = serverdf.loc[(serverdf['IPaddress'] == clientAddress[0]) & (serverdf['UDPport'] == str(clientAddress[1])), 'file-dirs']
                    for fullFile in message:
                        filePath = fullFile.rpartition('/')[0] +'/'
                        fileN = fullFile.rpartition('/')[2]
                        if fileN not in currfilenames.values[0]:
                            currfilenames += fileN + ' '
                            currfilepaths += filePath + ' '

                    serverdf.loc[(serverdf['IPaddress'] == clientAddress[0]) & (serverdf['UDPport'] == str(clientAddress[1])), 'filenames'] = currfilenames
                    serverdf.loc[(serverdf['IPaddress'] == clientAddress[0]) & (serverdf['UDPport'] == str(clientAddress[1])), 'file-dirs'] = currfilepaths
                    #print(serverdf)
                    serverfiledf = transformDF()
                    broadcastTable()
                    
                elif message[0] == "dereg":
                    serverdf.loc[(serverdf['name'] == message[1]), 'online-status'] = False
                    serverfiledf = transformDF()
                    broadcastTable()
                    serverSock.sendto("ACKDereg".encode(), clientAddress)  
            except:
                pass
        except:
            pass
    
    
#client mode        
elif mode =='-c':
    # preliminary error checking
    if len(sys.argv) != 7:
        sys.exit(">>> [ERROR: Incorrect Number of Arguments]")
    username = sys.argv[2]
    server_ip = sys.argv[3]
    checkIPAddress(server_ip)
    server_port = checkPortNum(sys.argv[4])
    clientUDP = checkPortNum(sys.argv[5])
    clientTCP = checkPortNum(sys.argv[6])
    
    # building client UDP socket for communication with server
    try:
        clientUDPsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        clientUDPsock.bind(("localhost", clientUDP))
    except:
        sys.exit(">>> [ERROR: Failed building UDP Socket - already used port.]")
    
    # building client TCP socket for listening to TCP connection requests from other clients
    try:
        clientTCPsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientTCPsock.bind(("localhost", clientTCP))
    except:
         sys.exit(">>> [ERROR: Failed building TCP Socket - already used port.]")  
    
    # FUNCTION AREA FOR CLIENT
    def clientExit(signum, frame):
        os._exit(0)
    def clientTCPReceive():
        global TCPListen
        clientTCPsock.listen()
        while True:
            connectionSock, addr = clientTCPsock.accept()   # create new client socket for communicating with other clients
            if not TCPListen:  # ignoring incoming requests
                connectionSock.close()
                continue
            IPfrom = addr[0]
            print("< Accepting connection request from {IP}. >".format(IP = IPfrom))
            firstline = connectionSock.recv(2048).decode()
            firstline = firstline.split()
            requestPathFile = firstline[1]
            clientN = firstline[2]
            requestFileName = requestPathFile.rpartition('/')[2]
            file = open(requestPathFile, "rb")
            file_size = os.path.getsize(requestPathFile)
            connectionSock.send(requestFileName.encode())   #first send: send over file nae
            connectionSock.send(str(file_size).encode())    #second send: send over file size in bytes
            data = file.read()
            print("< Transferring {transferF}... >".format(transferF = requestFileName))
            connectionSock.sendall(data)    # third send: sending all file content
            connectionSock.send(b"<ENDFILEREQ>")
            
            file.close()
            print("< {transferF} transferred successfully! >".format(transferF = requestFileName))
             
            connectionSock.close()
            print("< Connection with client {name} closed. >".format(name = clientN))
            
    def clientUDPReceive():
        global clientdf
        global myClientIP
        global ACKFileOffer
        global isderegACKed
        while True:
            try:
                recvmessage, senderAddress = clientUDPsock.recvfrom(2048)
                try:
                    clientdf = pickle.loads(recvmessage)
                    tableUpdate = ">>> [Client table updated.]"
                    #print(clientdf)
                    print(tableUpdate)
                    ACKmsg = "ACKTableUpdate: " + myClientIP + " " + str(clientUDP)
                    #print(ACKmsg)
                    #time.sleep(2)
                    clientUDPsock.sendto(ACKmsg.encode(), (server_ip, server_port))
                except:
                    recvmessage = recvmessage.decode().split(" ", 1)
                    if recvmessage[0] == "YourIP:":
                        myClientIP = recvmessage[1]
                    elif recvmessage[0] == "ACKFileOffer":
                        ACKFileOffer = True
                    elif recvmessage[0] == "ACKDereg":
                        isderegACKed = True
            except:
                pass    
    
    # client registration to server (UDP)
    regInfo = ["REGISTRATION:", username, True, str(clientTCP), str(clientUDP),'','']
    try:
        clientUDPsock.sendto(pickle.dumps(regInfo), (server_ip, server_port))
        regStatus, serverAddress = clientUDPsock.recvfrom(2048)
    except:
        sys.exit(">>> [ERROR: specified FileApp server does not exist.]")   
    # receive registration result
    regStatus = regStatus.decode()
    if "ERROR" in regStatus:
        print(regStatus)
        sys.exit()
    print(regStatus)
    
    # create separate thread to take incoming messages from other clients(TCP)
    clientCommThread = threading.Thread(target=clientTCPReceive)
    clientCommThread.start()
    # create separate thread to take incoming messages(UDP)
    clientRecvThread = threading.Thread(target=clientUDPReceive)
    clientRecvThread.start()
    
    # reads in client action
    signal.signal(signal.SIGINT, clientExit)
    while True:
        # client input from console
        action = input(">>> ") 
        if isOffline:   # After deregistration the client side shouldn't send anything to the server when those commands are typed in
            print(">>> [Action Failed: Client is deregistered.]")
            continue
        
        action = action.split(" ", 1)
        if action[0] == "setdir":
            searchDir = action[1]
            if os.path.isdir(searchDir):
                print(">>> [Successfully set {dir} as the directory for searching offered files.]".format(dir = searchDir))
                # making sure that directory ends with a /
                if not searchDir.endswith("/"):
                    searchDir = searchDir + "/"
            else:
                print(">>> [setdir failed: {dir} does not exist.]".format(dir = searchDir))
                searchDir = None    #invalid set it back to None
        elif action[0] == "offer":
            if searchDir == None:
                print(">>> [ERROR: attempt to offer file before issuing setdir command.]")
                continue
            filenames = action[1].split()
            # filenames can be relativepaths or simply filenames
            filesToShare = ["FILEOFFER:"]
            allFilesDontExist = True
            for filename in filenames:
                # remove the prepending / if it exists
                if filename[0] == '/':
                    filename = filename[1:]
                fileFullPath = searchDir+filename
                if os.path.isfile(fileFullPath):
                    filesToShare.append(fileFullPath)
                    allFilesDontExist = False
                else:
                    print(">>> [ERROR: cannot offer {file}. File does not exist.]".format(file = fileFullPath))
            #print(filesToShare)
            # if all files don't exist don't need to update offer
            if allFilesDontExist:
                continue
            
            count = 0
            while count < 3:
                clientUDPsock.sendto(pickle.dumps(filesToShare), (server_ip, server_port))
                time.sleep(0.5)
                if ACKFileOffer:
                    print(">>> [Offer Message received by Server.]")
                    break
                else:
                    count+=1
            
            if ACKFileOffer:
                ACKFileOffer = False #reset
            else:
                print(">>> [No ACK from Server, please try again later.]")
        elif action[0] == "list":
            col_names = clientdf.columns.tolist()
            col_names = [s.capitalize() for s in col_names]
            if clientdf.empty:
                print(">>> [No files available for download at the moment.]")
                continue   
            tempdf = clientdf
            tempdf = tempdf.rename(columns={'Filename': 'FILENAME', 'Owner': 'OWNER', 'Client IP Address': 'IP ADDRESS', 'Port': 'TCP PORT'})
            # set display options
            tempdf = tempdf.drop('File Directory', axis=1)
            pd.set_option('display.max_colwidth', None)
            pd.set_option("display.colheader_justify","left")
            tempdf.style.set_properties(**{'text-align': 'left'})
            #sort by column1 from Z to A, then by column2 from A to Z
            tempdf = tempdf.sort_values(['FILENAME', 'OWNER'], ascending=(True, True))
            tempdf = tempdf.to_string(index=False, header=True, justify='left', col_space=2)
            print(tempdf) 
        elif action[0] == "request":
            params = action[1].split()
            if len(params)!=2:
                print(">>> [ERROR: Wrong number of arguments for request action.]")
                continue
            requestClient = params[1]
            requestFile = params[0]
            if requestClient == username:
                print("< Invalid Request >")
                continue
            requestdf = clientdf.loc[(clientdf['Filename'] == requestFile) & (clientdf['Owner'] == requestClient)]
            if requestdf.empty:
                print("< Invalid Request >")
                continue
            requestdf = requestdf.values.flatten().tolist()
            requestIP = requestdf[2]
            requestPort = int(requestdf[3])
            requestDir = requestdf[4]
            # print(requestIP)
            # print(requestPort)
            
            # create new TCP socket that acts as client to other clients
            clientTCPsockclnt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                clientTCPsockclnt.connect((requestIP, requestPort))
                print("< Connection with client {requestclnt} established. >".format(requestclnt = requestClient))
            except:
                print("< ERROR: Connection with client {requestclnt} failed. >".format(requestclnt = requestClient))
                continue
            
            reqDirPath = requestDir + requestFile
            # file request msg includes what file to request and to send it to the listening TCP socket of the client
            fileReqMsg = "FILEREQUEST: " + reqDirPath + ' ' + username
            clientTCPsockclnt.send(fileReqMsg.encode())
            # receive message after sending requset to client
            reqfilename = clientTCPsockclnt.recv(2048).decode()
            reqfilesize = clientTCPsockclnt.recv(2048).decode()
            # print(reqfilename)
            # print(reqfilesize)
            file = open(reqfilename, "wb")
            file_bytes = b""    # empty byte string to append to
            downloadDone = False
            
            print("< Downloading {dwnldfile}... >".format(dwnldfile = reqfilename))
            while not downloadDone:
                data = clientTCPsockclnt.recv(2048)
                if file_bytes[-12:] == b"<ENDFILEREQ>":     # check if last 12 characters is end tag
                    downloadDone = True
                else:
                    file_bytes += data
            
            file_bytes = file_bytes[:-12]    #remove the ending characters
            file.write(file_bytes)
            file.close()
            print("< {dwnldfile} downloaded successfully! >".format(dwnldfile = reqfilename))
            clientTCPsockclnt.close()
            print("< Connection with client {reqClnt} closed. >".format(reqClnt = requestClient))
            
        elif action[0] == "dereg":
            #immediately start ignoring incoming file requests though TCP
            TCPListen = False
            if action[1] != username:
                print(">>> [ERROR: cannot deregister a client other than itself ({myName})]".format(myName= username))
                continue
            count = 0
            while count < 3:
                clientUDPsock.sendto(pickle.dumps(action), (server_ip, server_port))
                time.sleep(0.5)
                if isderegACKed == True:
                    isderegACKed = False
                    print(">>> [You are Offline. Bye.]")
                    isOffline = True
                    break
                else:
                    count += 1
            if not isOffline:
                print(">>> [Server not responding]")
                print(">>> [Exiting]")
                os._exit(0) #terminate the program after failed ACK all three times
        else:
            print(">>> [ERROR: action {act} is not implemented]".format(act = action[0]))
else:
    sys.exit(">>> [ERROR: Undefined mode]")