#!python

"""
"""

from filepool import *  # FilePool
from sfsconfig import * # some basic parameters
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory,Protocol,ServerFactory
from twisted.protocols.basic import LineReceiver
from twisted.protocols.basic import NetstringReceiver

import os

SUCCESS,ERROR,PARTIAL=range(3)
FLAG,CONTENT = range(2)
LEGAL_PARAMS = ['name','start','size'] # legal FileServer request params

class SFSClient(LineReceiver):
    """
    @brief This protocol communicate with center server
    """
    def connectionMade(self):
        self.sendRequest(self.factory.cmd,self.factory.param)

    def lineReceived(self,line):
        result=self.parse(line)
        if len(result) ==2:
            self.resultReceived(result[0],result[1])
        else:
            self.resultReceived(result[0],'')

    def resultReceived(self,flag,result):
        self.factory.cmdCompleted(flag,result)

    def sendRequest(self,cmd,param):
        if cmd not in legal_commands:
            self.resultReceived('error','illegal command %s' %(cmd,))
        else:
            request = '%s%s%s' % (cmd,cmd_param_sep,param)
            self.sendLine(request)

    def parse(self,line):
        return line.split(cmd_param_sep,1)

class SFSClientFactory(ClientFactory):

    protocol = SFSClient

    def __init__(self,cmd,param):
        """
        @param cmd: command in string
        @param param: command's parameters in appropriate string format
        """
        self.cmd = cmd
        self.param = param
        self.defer = Deferred()
        
    def cmdCompleted(self,flag,result):
        if self.defer is not None:
            d,self.defer = self.defer,None
            
            if flag == 'ok':
                d.callback(result)
            else:
                d.errback(result)


class SFSFileServer(NetstringReceiver):
    """
    @brief This ptotocol provide file downloading service
    """
    def stringReceived(self,string):
        cmd,params=self.parse(string)
        self.requestReceived(cmd,params)

    def requestReceived(self,cmd,params):
        print(cmd)
        print(params)
        flag,content=self.factory.handleRequest(cmd,params)
        if flag == ERROR:
            self.sendString(str(ERROR)+' '+content)
        else:
            self.sendFile(content)
    def parse(self,string):
        cmd_params=string.split(' ')
        cmd = cmd_params[0]
        params={}
        for param in cmd_params[1:]:
            key,value=param.split(key_value_sep,1)
            if key == 'name':
                params[key]=value
            else:
                params[key] = int(value)
        return (cmd,params)
    
    def sendFile(self,content):
        self.sendString(str(SUCCESS))
        self.sendString(content)

class FSFactory(ServerFactory):

    protocol = SFSFileServer

    def __init__(self,service):
        self.service = service
    
    def handleRequest(self,cmd,params):
        cmd_func=getattr(self.service,'fs_%s' % (cmd,),None)
        if cmd_func == None:
            return (ERROR,None)
        return cmd_func(params)

class FSService():

    name_path={} # a map from filename to file path

    def fs_get(self,params):
        """
        @param params: a python map, legal keys such as: name,start,size
        """
        start = params.get('start',0)
        size = params.get('size',0)
        filename=params.get('name','')
        flag = ERROR
        if filename == '':
            return (flag,'no filename provided')
        if not self.name_path.has_key(filename):
            return (flag,'%s is not shared' %(filename,))
        content=''
        with open(self.name_path[filename],'r') as f:
            f.seek(0,os.SEEK_END)
            length=f.tell()
            # debug
            print(length)
            if length<start:
                return (flag,'start position out of index')
            f.seek(start)
            size = length-start if size==0 else size
            content = f.read(size)
        if len(content)!= size:
            print(size,len(content))
            flag = PARTIAL
        else:
            flag = SUCCESS
        print(flag,content)
        return (flag,content)

class SFSFileClient(NetstringReceiver):
    """
    @brief This is the protocol for downloading file
    from other hosts
    """

    buf = ''
    state=FLAG

    def connectionMade(self):
        self.request = 'get name=%s start=%d size=%d' %(self.factory.filename,self.factory.start,self.factory.size)
        self.sendString(self.request)
    
    def stringReceived(self,string):
        
        if self.state == FLAG:
            flag=string.split(' ',1)
            if flag[0] == str(SUCCESS):
                self.state = CONTENT
            elif flag[0] == str(ERROR):
                self.errorReceived(flag[1])
        else:
            self.state = FLAG
            self.fileReceived(string)
    
    def fileReceived(self,file):
        self.factory.receive(file,True)

    def errorReceived(self,err):
        self.factory.receive(err,False)

class FCFactory(ClientFactory):

    protocol = SFSFileClient
    
    def __init__(self,filename,start=0,size=0):
        self.filename=filename
        self.start=start
        self.size =size
        self.defer = Deferred()
    
    def receive(self,msg,state):
        if self.defer is not None:
            d,self.defer = self.defer,None
            if state == True:
                d.callback(msg)
            else:
                d.errback(msg)
            

class SFSInterCommunicator(NetstringReceiver):
    """
    @brief This is a Protocol for internal process comunication
    in the way like message passing
    """
    pass

class ICFactory(ServerFactory):

    protocol = SFSInterCommunicator

    def __init__(self,service):
        self.service = service
