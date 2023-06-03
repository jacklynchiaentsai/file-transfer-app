# Computer Networks Project: file-transfer-app
## Description
Simple file transfer application that supports multiple clients and one server using both TCP and UDP protocols.
Server keeps track of client information and their associated sharing files. This information is broadcasted and used by clients to communicate directly with each other and initiate file transfers. All server-client communication is done over UDP, whereas clients communicate with each other over TCP.      

**See project_info.pdf for detailed project functionlities description. ** 

Note: '$' is used to signify the start of a command line
# Command Line Instructions for Compiling and Running Program
Note: run the command line instruction at the directory of FileApp.py
- Compiling and running in Server Mode
$ python FileApp.py -s <port>

- Compiling and running in Client Mode
$ python FileApp.py -c <name> <server-ip> <server-port> <client-udp-port> <client-tcp-port>

# Python Libraries Utilized
Here's the list of libraries I imported: 
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

Also generated a requirements.txt file using the command $ pip freeze > requirements.txt

# Project Documentation & Program Features
## Command Line Error Checking
- check if mode is valid (-s or -c)
- check if number of command line arguments fit project specifications for each mode
- implemented function checkPortNum() to check if port arguments are valid (within range, int)
- implemented function checkIPAddress() to check if IP address format is valid
- check if port is already used for server port , client UDP and TCP port
- check if server is started before client

## Registration
- Please see test.txt for output samples on test cases.
- implemented class thread_with_exception to kill thread upon timeout
- implemented function transformDF() to transform server table to client local table format
- implemented silent leave

## File Offering
- Please see test.txt for output samples on test cases.
- took care of not adding duplicate entries of file offerings by the same client
- NOTE My implementation:
    - if offer file doesn't exist will print error message
    - if all of the offer files don't exist then will not send UDP notification to server
    - otherwise if 1 or more of the offer file exist 
        - will still print error message of the non-existant files
        - will still offer the existing files to server
    - <filename> supports relative paths of filename from setdir

## File listing
- Please see test.txt for output samples on test cases.
- NOTE My implementation:
    - the list is ordered alphabetically by filename
    - if file name is the same ordered alphabetically by owner name

## File Transfer
- Please see test.txt for output samples on test cases.
- prints error message if unable to make TCP connection with requesting client

# De-Registration
- Please see test.txt for output samples on test cases.
- a client can only dereg itself
- NOTE My implmentation:
    - after a client successfully deregisters the client side shouldn't send anything to the server when those commands are typed in
    - every client input will have the same action failed message on console

# Client and Server Tables Structure
utilized pandas dataframe 
## serverdf
- server table of nicknames of all the clients, their status, the files they are sharing, along wiht thier IP addressses and port numbers
- Columns:
    - name: str
    - online-status: boolean True/False
    - IPaddress: str
    - TCPport: str of number
    - UDPport: str of number
    - filenames: str of filenames separated by ' '
    - file-dirs: str of file directories separated by ' ' (not required but used to find file directory path)

## serverfiledf
- transformed version of serverdf to broadcast to client
- Columns:
    - Filename: str
    - Owner: str
    - Client IP Address: str
    - Port: str of number
    - File Directory: str (not required but used to find file directory path)

## clientdf
- client local table
- Columns:
    - Filename: str
    - Owner: str
    - Client IP Address: str
    - Port: str of number
    - File Directory: str (not required but used to find file directory path)
