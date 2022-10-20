#! /usr/bin/python3
import sys
from pexpect import pxssh
import re

from concurrent.futures import ThreadPoolExecutor


### gets results of sh ip access-lists IPV4-CONTROL-PLANE-FILTER
### outputs to Individual files
### uses router_list.txt
###
###

p_version = re.compile('Cisco ([\w\s]+) Software')


## p_version is just a variable name looking for  
## any word Cisco then space + one or more characters plus Software
## This is just a way of identifying the gear as Cisco


### username and password for the router 
###
#username = 'user'
#passwd = 'password'
### Compiling Regular Expressions
### Regular expressions are compiled into pattern objects, which have methods for various operations such as searching for pattern matches or performing string substitutions.
###
###
### import re
### p = re.compile('ab*')
### p
### re.compile('ab*')
### re.compile() also accepts an optional flags argument, used to enable various special features and syntax variations. We will go over the available settings later, but for now a single example will do:
###
### p = re.compile('ab*', re.IGNORECASE)
### The RE is passed to re.compile() as a string. REs are handled as strings because regular expressions are not
### part of the core Python language, and no special syntax was created for expressing them. (There are applications that dont need REs at all
### so there is no need to bloat the language specification by including them.) Instead, the re module is simply a C extension module included with Python, just like the socket or zlib modules.
### Putting REs in strings keeps the Python language simpler, but has one disadvantage which is the topic of the next section.


def quit_cleanup(child):
  child.sendline('exit')
  child.close()


###
###
###



def ur_s4name(ur_full_name):
  name_l = ur_full_name.split('.')
  if len(name_l) >= 4:
    s4name = '.'.join(name_l[0:4])
  else:
    s4name = ur_full_name
  return s4name

def run_cisco_commands(child):
  child.sendline('term len 0')
  child.prompt()
  child.sendline('show inventory')
  child.prompt()
  rt_str = child.before
  child.sendline('exit')
  return rt_str

def run_juniper_commands(child):
  child.sendline('set cli screen-width 120')
  child.prompt()
  child.sendline('set cli screen-length 0')
  child.prompt()
  child.sendline('show chassis hardware | no-more')
  child.prompt()
  rt_str = child.before
  child.sendline('exit')
  return rt_str

def login_ur(ur):
  result_path = ur+'.log'
  F0 = open(result_path, 'w') 
  s4_name = ur_s4name(ur)
  login_status = True
  msg = ''
  rt_str = ''
  try:
    child = pxssh.pxssh(encoding='utf-8')
    child.PROMPT = '[\#\>]'
    child.login(
      ur, username, passwd, 
      auto_prompt_reset=False,
      original_prompt='[\#\>]'
    )
    child.logfile = sys.stdout  # None if don't want log output 
    dev_sys = 'Cisco'
    if re.search('re\d', child.before):
        dev_sys = 'Juniper'
    if dev_sys == 'Cisco':
      child.PROMPT = s4_name + '#'
      rt_str = run_cisco_commands(child)
    elif dev_sys == 'Juniper':
     child.PROMPT = s4_name + '>'
     rt_str = run_juniper_commands(child)
  except pxssh.ExceptionPxssh as e:
    login_status = False
    msg = str(e)
  except KeyboardInterrupt:
    quit_cleanup(child)
  except Exception as e:
    login_status = False
    msg = str(e)
  finally:
    if child:
      child.close()
  print('{0} {1}!'.format(ur, 'Succeed' if login_status else 'Failed'))
  print(rt_str, file=F0)
  F0.write(status+'\n')
  F0.write(msg+'\n')
  F0.write(rt_str+'\n')
  F0.write('='*40 + '\n\n')
  F0.close() 
  return (ur, login_status, msg, rt_str)

def mp_scan(ur_list):
  with ThreadPoolExecutor(max_workers=16) as executor:
    res_l = executor.map(login_ur, ur_list)
  return res_l

def main():
  ur_list_path = 'router_list.txt'
  F1 = open(ur_list_path, 'r')
  ur_list = [line.strip() for line in F1]
  print('{0} URs'.format(len(ur_list)))
  F1.close()

  res_list = mp_scan(ur_list)

if __name__ == "__main__":
  main()
