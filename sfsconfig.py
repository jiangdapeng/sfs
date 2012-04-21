#!python

legal_commands=['share','remove','removeall','query','quit']
cmd_param_sep =' ' # separator between command and param
params_sep    ='$' # separator between different params
info_sep      =';' # separator between different file info struct
field_sep     ='^' # separator between fields in a info struct
key_value_sep ='=' # key:value
host_port_sep = '_'# host_port

default_port  = 6666 # port for filedowning
server_port   = 6668 # port for server
