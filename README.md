# file-transfer-app
Computer Networks Project
## Description
Simple file transfer application that supports multiple clients and one server using both TCP and UDP protocols.
Server keeps track of client information and their associated sharing files. This information is broadcasted and used by clients to communicate directly with each other and initiate file transfers. All server-client communication is done over UDP, whereas clients communicate with each other over TCP.   

## Functionalities
all command line instruction is indicated with the $ symbol
### Server Initiation
server needs to be started before clients start going online
```
$ FileApp -s <listening-port>
```
### Client Registration
only registered clients should be able to offer files and will receive the updated list of 
