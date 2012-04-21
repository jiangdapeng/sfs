#!python

"""
@file sfsserver.py
@author asuwll.jdp@gmail.com
"""

from filepool import *
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.protocols.basic import NetstringReceiver
from sfsconfig import *

class SFSServer(LineReceiver):
    """
    @brief share file system server protocol
    """

    def __init__(self):
        """ """
        self.ip=None
        self.port=None
        self.user = None

    def connectionMade(self):
        """when acceptted a requet send a welcome line"""
        self.ip = self.transport.getPeer().host
        self.port = self.transport.getPeer().port
        self.user = self.ip
        print("%s connected" % self.user)

    def connectionLost(self,reason):
        """ """
        print("%s exit" % self.user)

    def lineReceived(self,line):
        """ receive line event """
        print("line:%s" % line)
        cmd,param=self._parse(line)

        self.RequestReceived(cmd,param)

    def RequestReceived(self,cmd,param):
        """ a request to be served """
        cmd_func = getattr(self.factory,'SFS_%s' % (cmd,),None)
        result = cmd_func(self.user,param)
        self.sendLine(result)

    def _parse(self,line):
        """ 
        parse the line received
        @return (command,param)
        """

        cmd_param=line.split(cmd_param_sep,1)
        cmd=cmd_param[0]
        if len(cmd_param)>1:
            param=cmd_param[1]
        else:
            param=None
        if cmd == 'share':
            if param == None:
               param,cmd= cmd,'paramerror'
            else:
                infos = param.split(info_sep)
                param=[[field for field  in  info.split(field_sep)] for info in infos]
        elif cmd == 'remove':
            if param==None:
                param,cmd= cmd,'paramerror'
            else:
                param=param.split(info_sep)
        elif cmd == 'removeall':
            param = None
        elif cmd == 'query':
            if param == None:
                param,cmd= cmd,'paramerror'
            else:
                param=param.split(info_sep)
        elif cmd == 'quit':
            pass
        else:
            cmd = 'undefined'
            param = None
        return (cmd,param)

class SFSService(object):

    def __init__(self,filepool):
        self.filepool=filepool
    
    def query(self,filelist):
        """
        @param  filelist: [name1,name2,...,namen]
        @return query result
        """
        each_file_addrs=[ fn+':'+info_sep.join([field_sep.join(info) for info
            in self.filepool.query(fn)]) for fn in filelist]
        fbmsg = params_sep.join(each_file_addrs)
        return "ok "+fbmsg

    def share(self,user,fileinfo_list):
        """
        @param user: who share fileinfo_list
        @param fileinfo_list: like [['file1', '2014', 'gaafsdf'], ['file2', '3006', 'kjjuhoklkl']]
        """
        fbmsg=''
        for info in fileinfo_list:
            try:
                self.filepool.add_userfile(user,info[0])
            except DupError,e:
                print(e)
                fbmsg += e.msg+info_sep
        for info in fileinfo_list:
            newinfo = [user]+info[1:]
            self.filepool.add_file(info[0],newinfo)
        if fbmsg != '':
            return 'error duplicate'+fbmsg[:-1]
        return "ok"

    def remove(self,user,filelist):
        """
        @param user: remove user's shared filelist
        @param filelist: [name1,name2,...,namen]
        """
        fbmsg=''
        try:
            for fname in filelist:
                self.filepool.remove_file(fname,user)
        except NotExistsError,e:
                fbmsg+=e.msg
                return "error "+fbmsg
        else:
            return "ok"

    def removeall(self,user):
        """
        @brief remove all files shard by user and remove user from userlist
        """
        try:
            self.filepool.remove_user(user)
        except NotExistsError,e:
            return "error "+e.msg
        else:
            return "ok"

    def quit(self,user,option):
        """
        @brief when the client quit, deal with the files shared
        by the client according to the param
        @param user: who quit
        @param option:None or -d
        """
        fdmsg='bye bye'
        if option == '-d':
            return self.removeall(user)
        return fdmsg


class SFSFactory(Factory):

    protocol = SFSServer
    def __init__(self,service):
        self.service = service

    def SFS_share(self,user,param):
        return self.service.share(user,param)
    
    def SFS_remove(self,user,param):
        """
        @param param [name1,name2,...,namen]
        """
        return self.service.remove(user,param)

    def SFS_removeall(self,user,param=None):

        return self.service.removeall(user)

    def SFS_query(self,user,param):
        """
        @param  param [name1,name2,...,namen]
        @return query result
        """
        return self.service.query(param)

    def SFS_quit(self,user,param):
        """
        @brief when the client quit, deal with the files shared
        by the client according to the param
        @param param None or -d
        """
        return self.service.quit(user,param)

    def SFS_paramerror(self,user,param):
        return 'error in %s\'s parameters' %(param,)

    def SFS_undefined(self,user,param):
        return "error undefined command"

def sfs_main():
    reactor.listenTCP(server_port,SFSFactory(SFSService(FilePool())))
    reactor.run()

if __name__=='__main__':  
    sfs_main()
