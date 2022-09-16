#!/usr/bin/env python3

import socket
import os, sys, json
import signal
from subprocess import Popen, PIPE

PORT = 65432        # Port to listen on (non-privileged ports are > 1023)
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
HOST = socket.gethostname()

#To run and survive closing terminal: nohup python socket-server.py
#To run periodically - chrontab -e: 
# 00 * * * * python /var/www/html/projects/asly/socket-server.py


def kill_port_proc(port_num):
  process = Popen(["lsof", "-i", ":{0}".format(port_num)], stdout=PIPE, stderr=PIPE)
  stdout, stderr = process.communicate()
  for process in str(stdout.decode("utf-8")).split("\n")[1:]:       
      data = [x for x in process.split(" ") if x != '']
      if (len(data) <= 1):
          continue

      os.kill(int(data[1]), signal.SIGKILL)
      print("Killed process, please run the script again")

#Now for the application specific part, functions, libraries, and data to load
#Application specific libraries
# sys.path.append("/var/www/html/code_utils")
# from parsing_lib import *

#shelve_fpath="parsing/verbs.shelve"

#identify the data processing function for each application
def process_data(data0):
  data0_decoded=data.decode("utf-8")
  data0_decoded='Test: %s'%data0_decoded
  output0=data0_decoded.encode("utf-8")
  return output0



try:
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr)
                while True:
                    data = conn.recv(1024)
                    
                    output=process_data(data)
                    if not data:
                        break
                    #conn.sendall(data)
                    conn.sendall(output)
except: #if the port is already used and we want to restart it 
    pass
    kill_port_proc(PORT)
    print("Killed the port process, run the script again")

