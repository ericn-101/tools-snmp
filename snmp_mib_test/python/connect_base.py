#!/usr/bin/env python

# import argparse
import datetime
import getpass
import logging
import os
import pexpect
import pxssh
import re
import shlex
import string
import subprocess
import sys
import time
import traceback

class ConnectBase(object):
  """class ConnectBase
    PURPOSE:

    METHODS:

    INPUTS:

    TODO:
  """

  def __init__(self, **kwargs):
    # Parameter Assignments
    self.debug          = kwargs.pop('debug', 0)
    self.logLevel       = kwargs.pop('logLevel', 'info')
    self.ntxCvmList     = kwargs.pop('ntxCvmList', None)
    self.targetName     = kwargs.pop('targetName', None)
    self.targetIP       = kwargs.pop('targetIP', None)
    self.userName       = kwargs.pop('userName', None)
    self.passWord       = kwargs.pop('passWord', None)
    self.sshKey         = kwargs.pop('sshKey', None)
    self.remCmds        = kwargs.pop('remCmds', None)

    if self.debug:
      print "DEBUG: In ConnectBase"
      print "DEBUG: General Parameters  - - - - - - - - - "
      print "DEBUG: debug          =",self.debug
      print "DEBUG: logLevel       =",self.logLevel
      print "DEBUG: Connection targets  - - - - - - - - - "
      print "DEBUG: targetName     = %s" % self.targetName
      print "DEBUG: targetIP       = %s" % self.targetIP
      print "DEBUG: ntxCvmList     =",self.ntxCvmList
      print "DEBUG: Connection Parameters - - - - - - - - "
      print "DEBUG: userName       = %s" % self.userName
      print "DEBUG: passWord       = %s" % self.passWord
      print "DEBUG: sshKey         = %s" % self.sshKey
      print "DEBUG: Remote Commands - - - - - - - - - - - "
      print "DEBUG: remCmds        = %s" % self.remCmds

    #
    # Do some input validation here to make sure we have all needed inputs
    # to perform a SNMP operation
    #

    usageFlag = 0
    if self.targetName == None and self.targetIP == None:
      print ("USAGE: ConnectBase requires a target. Provide one of"
        " the following arguments: targetName or targetIP")
      usageFlag = 1

    if self.passWord == None and self.sshKey == None:
      print ("USAGE: ConnectBase requires authentication. Provide one of"
        " the following arguments: passWord or sshKey")
      usageFlag = 1

    if self.userName == None:
      print ("USAGE: ConnectBase requires a user. Provide a valid user name"
        " for the target host login")
      usageFlag = 1

    if self.remCmds == None:
      print ("USAGE: ConnectBase requires 1 or more remote commands to execute."
        " Provide 1 or more commands to execute on the target host.")
      usageFlag = 1

    # If any usage was tripped, exit out
    if usageFlag:
      print "USAGE: Exiting because 1 or more required parameters are not set"
      sys.exit(1)

    # Reset .ssh/known_hosts so we don't have EOF issues due to stale entries
    homeDir = os.path.expanduser("~")
    fileSpec1 = os.path.join(homeDir, ".ssh/known_hosts")
    rawCmd1  = 'rm -f %s' % fileSpec1
    rv = subprocess.call(rawCmd1, shell=True)
    if self.debug:
      print "DEBUG: subprocess rv = ",rv, "on cmd1 =", rawCmd1
    if rv == 1:
      print "FAIL: on %s" % rawCmd1
      return rv


  def setUpConnectLogging(self, logName="connecttest.log"):
    """  Setup Logging
    Set up a date-time-stamped-connecttest.log in the logs directory.
    Requires the python logging module
    TO-DO
    1. wrap the logging.level calls with aliases
       [debug|info|warning|error|critical]
    """
    numeric_level = getattr(logging, self.logLevel.upper(), None)
    if not isinstance(numeric_level, int):
      raise ValueError('Invalid log level: %s' % self.logLevel)
    print ('DEBUG: Default Log Params = Number : ',numeric_level, ', Level :',
            self.logLevel)
    currentDirSpec = os.getcwd()
    dirBaseSpec, curDir = os.path.split(currentDirSpec)
    fName = _timeStamped(logName)
    fLogSpec = os.path.join(dirBaseSpec, "logs", fName)
    logging.basicConfig(filename=fLogSpec , filemode='w',
      format='%(asctime)s %(levelname)s: %(message)s',
      datefmt='%Y:%m:%d %I:%M:%S', level=numeric_level)
    # Setup console logging
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    # formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    formatter = logging.Formatter('%(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

  def getTargetIP(self):
    """getTargetIP

    """
    if self.targetIP is None:
      if self.targetName is None:
        print "STATUS: Fix usage check for targetName %s, and targetIP %s" \
            % (self.targetName, self.targetIP)
        return None
      else:
        target = self.ntxCvmList[0]
        print "STATUS: Extracting target from CVM list ntxCvmList %s = %s" \
            % (self.ntxCvmList, self.ntxCvmList[0])
    else:
      target = self.targetIP
    return target


  def connectSSH(self):
    """connectSSH
    TODO List
      a)  Handle Cases = End Of File (EOF). Exception style platform exception
          ==> WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED
          Need to rm -f ~/.ssh/known_hosts

    """
    if self.targetIP is None:
      if self.targetName is None:
        print "STATUS: Fix usage check for targetName %s, and targetIP %s" \
            % (self.targetName, self.targetIP)
        return None
      else:
        target = self.ntxCvmList[0]
        print "STATUS: Extracting target from CVM list ntxCvmList %s = %s" \
            % (self.ntxCvmList, self.ntxCvmList[0])
    else:
      target = self.targetIP
    # rv = getTargetIP(self.targetIP, self.targetName, self.ntxCvmList)
    # target = rv
    # print "DEBUG: Function getTargetIP returned %s" % target


    userName = self.userName
    if self.passWord is None:
      passWord = getpass.getpass(self.passWord)
    else:
      passWord = self.passWord
    remCmds = self.remCmds
    print "STATUS: connectSSH Inputs = target %s, userName %s, passWord %s" \
        % (target, userName, passWord)
    print "STATUS: connectSSH Input Cmds = ", remCmds
    #
    # Some constants.
    #
    ### This is way too simple for industrial use -- we will change is ASAP.
    COMMAND_PROMPT = '[*$] '
    TERMINAL_PROMPT = '(?i)terminal type\?'
    TERMINAL_TYPE = 'vt100'
    # This is the prompt we get if SSH does not have the remote host's public
    # key stored in the cache.
    SSH_NEWKEY = '(?i)are you sure you want to continue connecting'
    responseList = []

    child = pxssh.pxssh()
    if not child.login(target, userName, passWord):
      print "STATUS: SSH session to %s failed on login" % target
    else:
      print "STATUS: SSH session to %s successful" % target
      for cmd in remCmds:
        try:
          print "Executing cmd: ", cmd
          child.sendline (cmd)
          child.prompt()
          response = child.before
          print "Cmd Output = ", response
          responseList.append(response)
        except pxssh.ExceptionPxssh, e:
            print "pxssh failed on login."
            print str(e)
      child.logout()

    if responseList:
      return responseList
    else:
      return None


  def connectCmdResponseParse(self, rawResponse=None):
    """connectCmdResponseParse
    Parses a list of console or CLI commands and their responses
    """
    rvList = []
    if rawResponse is None:
      print "STATUS: Function connectCmdResponseParse call has None response"
      return None
    else:
      responseCount = len(rawResponse)
      print "DEBUG: Number of responses to parse = ", responseCount
      for response in rawResponse:
        # Separate response into list of lines
        responseList = string.split(response, '\n')
        # Cases to handle
        # line 1 has command on it
        cmd = responseList[0].strip()
        paramDict = {}
        dictList = []
        for line in responseList:
          # line = filter(lambda x: x in string.printable, line)
          if line.count(":") > 0:
            print "Processing line:", line
            tmpList = map(str.strip, line.split(':', 1))
            # print "DEBUG: tmpList = ",tmpList

            # Case - Duplicate Entries with same labels
            if paramDict and tmpList[0] in paramDict:
              # print "DEBUG: Case where duplicate param label found"
              # create dict of dict where subdict is each instance
              # print "DEBUG: paramDict so far = ",paramDict
              if dictList:
                # dictList.append([paramDict])
                dictList.append(paramDict)
              else:
                dictList = [paramDict]
              # print "DEBUG: dictList so far = ",dictList
              paramDict = {}
              if len(tmpList[1]) == 0:
                # print "Case where response line has single param : no value"
                paramDict[tmpList[0]] = "None"
              else:
                paramDict[tmpList[0]] = tmpList[1]
            else:
              if len(tmpList[1]) == 0:
                # print "Case where response line has single param : no value"
                paramDict[tmpList[0]] = "None"
              else:
                paramDict[tmpList[0]] = tmpList[1]
          else:
            print "Skipping line:", line

        # Check if we have empty dict, meaning no parameter lists
        if dictList:
            # multiple instancs of same type data were found, each instance
            # is a dict inside a list
            # Add last instance to dictList
            # dictList.append([paramDict])
            dictList.append(paramDict)
            rvList.extend([cmd, dictList])
        elif not dictList and paramDict:
          # we found params in label:value format
          rvList.extend([cmd, paramDict])
        elif not dictList and not paramDict:
          # Either no response or response was not in label:value format
          if len(responseList) > 1:
            rvList.extend([cmd, responseList[1:]])
          else:
            rvList.extend([cmd, "None"])
      return rvList

def _timeStamped(fname, fmt='%Y-%m-%d-%H-%M-%S_{fname}'):
  """timeStamped
  # DESCRIPTION: Inserts a time stamp into the filename
  # USAGE:
  # INPUTS:      fname = file name we instead to create
  # OUTPUTS:     Updated file name with date-time stamp prepended to fname
  """
  return datetime.datetime.now().strftime(fmt).format(fname=fname)
