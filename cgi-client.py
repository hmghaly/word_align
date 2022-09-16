#!/usr/bin/python

import socket
import os, sys, json, subprocess

PORT = 65432        # The port used by the server - match the server with the client
HOST = '127.0.0.1'  # The server's hostname or IP address
HOST = socket.gethostname()


received_data=""
print "Content-type:text/html\r\n\r\n"
#print "Hello!<br>"
input_dict={}
output_dict={}


#Application specific data
#receive input from query string or stdin/ajax post-get
input_dict["sentence"]="test"
input_dict_json=json.dumps(input_dict)
#do some processing
#asly: generate an ID for the transaction, pass it to the socket server to create qr-codes and pdf files
#sa7/champolu: save the audio file to remporary location, pass the audio file path to the socket server to process it with feature extraction/rnn


#now sending the data to the socket server
#If server is not on, start it
# try:
#     s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.settimeout(10.0)
#     s.connect((HOST, PORT))
#     s.close()
#     print "the server is working somehow"
# except:
#     Process = subprocess.Popen("python socket-server.py", shell=True)
#     print "starting a new process <br>"
    #Process.wait()
    # s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # s.settimeout(10.0)
    # s.connect((HOST, PORT))

    #os.system("python socket-server.py")

#now send the data to the socket server

print "Hello"
try:

    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10.0)
    s.connect((HOST, PORT))
    s.sendall(input_dict_json.encode("utf-8"))
    received_data = s.recv(1024)
    output_dict["received_data"]=received_data
    output_dict["success"]=True
    output_dict["message"]="success"
    s.close()
except Exception as e:
    #received_data="error with the data %s"%str(e)
    output_dict["received_data"]=""
    output_dict["success"]=False
    output_dict["message"]=str(e)#"success"
    #Process = subprocess.Popen("python socket-server.py", shell=True)

print json.dumps(output_dict)
#print "so far ok"
