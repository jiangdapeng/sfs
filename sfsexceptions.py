#!python

"""
@file sfsexceptions.py
@author asuwll.jdp@gmail.com
"""

from exceptions import Exception

class SFSError(Exception):
    """ base class for exceptions in sfs system """
    pass

class NotExistsError(SFSError):
    """ file not exists in filepool """
    
    def __init__(self,msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

class DupError(SFSError):
    """ file duplicated """
    
    def __init__(self,msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
