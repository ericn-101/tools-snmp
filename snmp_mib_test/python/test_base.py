#!/usr/bin/env python

import csv
import datetime
import logging
import os
import pxssh
import shlex
import string
import subprocess
import sys
import time
import traceback
# from connect_nutanix import ConnectVendor
from connect_base import *


class TestBase(object):
  """class TestBase
  PURPOSE:
  METHODS:
  INPUTS:
  TODO:
  """

  def __init__(self, **kwargs):
    # Parameter Assignments
    self.debug          = kwargs.pop('debug', 0)
    self.logLevel       = kwargs.pop('logLevel', 'info')
    self.clusterName    = kwargs.pop('hostName', None)
    self.ipList         = kwargs.pop('ipList', None)
    self.testName       = kwargs.pop('testName', 'debugTest')
    self.logFSpec       = kwargs.pop('logFSpec', None)

    if self.debug:
      print "DEBUG: In TestBase"
      print "DEBUG: General Test Parameters - - - - - - - "
      print "DEBUG: debug          =",self.debug
      print "DEBUG: logLevel       =",self.logLevel
      print "DEBUG: clusterName    = %s" % self.clusterName
      print "DEBUG: ipList         = %s" % self.ipList
      print "DEBUG: testName       = %s" % self.testName
      print "DEBUG: logFSpec       = %s" % self.logFSpec



  def setUpTestLogging(self):
    """  Setup Logging
    Set up a date-time-stamped-snmptest.log in the logs directory.
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
    logName = self.testName
    logName = logName.replace("::","-")
    logName = logName.replace(".","-")
    logName = logName + ".log"
    fName = _timeStamped(logName)
    fLogSpec = os.path.join(dirBaseSpec, "logs", fName)
    self.logFSpec = fLogSpec
    print 'DEBUG: Log FileSpec = ', self.logFSpec
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

  def getTestResultsSummary(self):
    """  Retrieve results from test log
    """
    totalTC = 0
    passTC = 0
    failTC = 0
    warnTC = 0
    with open(self.logFSpec, 'rU') as f:
      reader = csv.reader(f)
      for row in reader:
        if self.debug:
          print "DEBUG: logFSpec row = %s" % row
        for item in row:
          if "TESTCASE" in item:
            totalTC += 1
          if "PASS" in item:
            passTC += 1
          if "FAIL" in item:
            failTC += 1
          if "WARN" in item:
            warnTC += 1
          if self.debug:
            print "DEBUG: totalTestCases = %s, passTestCases = %s, " \
               "failTestCases = %s, warnTestCases = %s" % \
               (totalTC, passTC, failTC, warnTC)
    values = {'totalTestCases': totalTC, 'passTestCases': passTC, \
        'failTestCases': failTC, 'warnTestCases': warnTC}
    return values

    
  def getClusterLogs(self, logList):
    """getClusterLogs
    NAME:     getClusterLogs
    PURPOSE:  Copy Vendor Product logs to local host logs dir
    IC:       This script may be called after 
              a. logging is configured
              b. some test has produced cluster logs worth saving
    OUTPUTS:  cluster logs copied from Vendor host to local logs dir.
    """
    if self.ipList is not None:
      # Get local test logs directory 
      currentDirSpec = os.getcwd()
      dirBaseSpec, curDir = os.path.split(currentDirSpec)
      logName = self.testName
      logName = logName.replace("::","-")
      logName = logName.replace(".","-")
      logName = logName + ".log"
      remoteBaseDir = os.path.join(dirBaseSpec, "logs")
      logging.debug("remoteBaseDir = %s" % remoteBaseDir)

      # Construct remote log filespec 
      for logFileSpec in logList:
        rawTestlogsDir = os.path.dirname(logFileSpec)
        rawTestLogName = os.path.basename(logFileSpec)   
        for cvmIP in self.ipList:
          rawLogFile = rawTestLogName.split(".")
          testLogFile = rawLogFile[0] + "_" + cvmIP + "." + rawLogFile[1]
          testLogSpec = os.path.join(remoteBaseDir, testLogFile)
          logging.debug("testLogSpec = %s" % testLogSpec)

          rawCmd1 = ('/usr/bin/scp -v -o "StrictHostKeyChecking no" '
            '-i ../keys/nut-int/nutanix '
            '   nutanix@%s:%s %s'
            % (cvmIP, logFileSpec, testLogSpec))
          logging.debug("Raw Cmd 1 = %s" % rawCmd1)

          rv = subprocess.call(rawCmd1, shell=True)
          logging.debug("subprocess rv = %s, on cmd1 = %s" % (rv, rawCmd1))
          if rv == 0:
            logging.info("Retrieved Vendor log %s" % logFileSpec)
          elif rv >= 1:
            logging.info("Vendor log %s not not found on CVM %s" % 
                (logFileSpec, cvmIP))
      return 0
    else:
      logging.error("Vendor CVM IP Addresses are undefined")
      return 1



def _timeStamped(fname, fmt='%Y-%m-%d-%H-%M-%S_{fname}'):
  """
  # NAME:        timeStamped
  # DESCRIPTION: Inserts a time stamp into the filename
  # USAGE:
  # INPUTS:      fname = file name we instead to create
  # OUTPUTS:     Updated file name with date-time stamp prepended to fname
  """
  return datetime.datetime.now().strftime(fmt).format(fname=fname)

