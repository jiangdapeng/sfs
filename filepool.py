#!python

"""
@file filepool.py
@author asuwill.jdp@gmail.com
"""

from sfsexceptions import *

class FilePool():
    """
    @brief maintain files shared by different hosts
    """
    def __init__(self):
        self.file_list={}
        self.user_files={}

    def add_file(self,filename,fileinfo):
        """
        @param file_name str
        @param fileinfo [ip+host_port_sep+port,file_size(in bytes),md5]
        """
        
        if self.file_list.has_key(filename):
            if fileinfo in self.file_list[filename]:
                raise DupError(filename)
            else:
                self.file_list[filename].append(fileinfo)
        else:
            self.file_list[filename]=[fileinfo]

    def add_userfile(self,user,filename):
        """
        @param user str(ip+host_port_sep+port)
        @param filename str(filename)
        """
        if self.user_files.has_key(user):
            if filename in self.user_files[user]:
                raise DupError(filename)
            else:
                self.user_files[user].append(filename)
        else:
            self.user_files[user]=[filename]

    def _rm_from_files(self,filename,user):
        """
        remove file shared by user from file_list 
        @param user str(ip+host_port_sep+port)
        @param filename file to be removed from shared file list
        """
        
        infos = self.file_list.get(filename)
        if infos ==None:
            return
        for finfo in infos:
            if finfo[0] == user:
                infos.remove(finfo)
                break
        
        if len(infos)==0:
            self.file_list.pop(filename)
    
    def remove_file(self,filename,user):
        """
        remove file shared by user
        """
        if not self.user_files.has_key(user):
            raise NotExistsError("UserNotExists "+user)
        else:
            if filename in self.user_files[user]:
                self._rm_from_files(filename,user)
                self.user_files[user].remove(filename)

    def remove_user(self,user):
        """
        remove all files shared by user
        and remove user
        """
        if not self.user_files.has_key(user):
            raise NotExistsError("UserNotExists "+user)
        else:
            files=self.user_files[user]
            for fn in files:
                self._rm_from_files(fn,user)
            self.user_files.pop(user)

    def query(self,filename):
        """
        @return ip$port list of hosts which shared the file
        @param filename name of file to download
        """
        return self.file_list.get(filename,[])         

    def get_files(self):
        return self.file_list

    def get_user(self):
        return self.user_files

