#!/usr/bin/env python

# SNMPWALK TEST

# Basic Setup
import datetime
from itertools import izip
import os
import pxssh
import shlex
import string
import subprocess
import sys
import time
import traceback
from connect_base import *
from snmp_base import *
from test_base import *


#
# INITIALIZE PARAMETERS: snmp_test_walk
#

# TEST CASE PARAMETRSS
bach = ['10.5.97.8', '10.5.97.9', '10.5.97.10', '10.5.97.11']
skywalker6 = ['10.5.96.228', '10.5.96.229', '10.5.96.230', '10.5.96.231']
skywalker9 = ['10.5.96.242', '10.5.96.243', '10.5.96.244', '10.5.96.245']
carlitos = ['10.5.96.25', '10.5.96.26', '10.5.96.27', '10.5.96.28']
pompano = ['10.5.96.67', '10.5.96.68', '10.5.96.69', '10.5.96.70']


clusterCVMList = bach
clusterName = 'bach'
debug = 1
logLevel = 'debug'
# testName = os.path.basename(__file__)
# testName = testName.split(".")[0]
testName = os.path.basename(__file__).split(".")[0]
myTestCase =  {'debug': debug, 'logLevel': logLevel, 'snmpFormat': 1,
    'clusterName': clusterName, 'ipList': clusterCVMList,
    'testName' : testName}

from test_nutanix import TestVendor
test = TestVendor(**myTestCase)

# Setup Logging
rv = test.setUpTestLogging()


# SNMP PARAMETERS
mySNMPUser1 = {'username': 'testerSHAAES', 'auth-key': 'snmptester123',
    'auth-type': 'SHA', 'priv-key': 'privtester', 'priv-type': 'AES'}
mySNMPUser2 = {'username': 'testerSHA', 'auth-key': 'snmptester123',
    'auth-type': 'SHA', 'priv-key': 'None', 'priv-type': 'None'}
mySNMPUserList = [ mySNMPUser1, mySNMPUser2]

homeDir = os.path.expanduser("~")
mibFileSpec = os.path.join(homeDir, '.snmp',  'mibs', 'VENDOR-MIB')

# Note that we fake out required entries with "None' <> None and when we
# mean None we use None
mySNMPDict =  {'debug': debug, 'logLevel': logLevel, 'snmpFormat': 1,
    'hostName': 'None', 'hostIP': clusterCVMList[0], 'portList': 'None',
    'snmpCmd': 'walk', 'snmpVer': 'v3', 'snmpUser': 'testerSHAAES',
    'authType': 'SHA', 'authKey': 'snmptester123',
    'privType': 'AES', 'privKey': 'privtester',
    'ntxCvmList': clusterCVMList, 'portList': None,
    'collectInt': 1,'sampleCnt': 1,
    'snmpOIDList': 'None', 'snmpOutLog': 'snmpout.out',
    'ntxShellUser': 'nutanix', 'ntxShellPasswd': 'nutanix/4u',
    'ntxSnmpUsers': mySNMPUserList, 'ntxMibSpec': mibFileSpec}

from snmp_mib_test_nutanix import SNMPMibTestVendor
p = SNMPMibTestVendor(**mySNMPDict)

# CONNECTION PARAMETERS
mySSHDict =  {'debug': debug, 'targetName': None,
    'targetIP': clusterCVMList[0],
    'ntxCvmList' : clusterCVMList,
    'userName': 'nutanix', 'passWord': 'nutanix/4u', 'sshKey': 'nutanix',
    'remCmds': 'None'}

from connect_nutanix import ConnectVendor
q = ConnectVendor(**mySSHDict)


# We need to retrieve the actual CVM IP list in case we have partial clusters
# or clusters formed from parts of other clusters.
# 1. Resolve whether IP taregtIP or familiar name targetName was input
logging.info('Verify target IP')
rv = q.getTargetIP()
target = rv
logging.info("Module: getTargetIP response = %s" % target)
# 2. Use the CVM IP list on the configured cluster
logging.info('Retrieve actual active CVM IP list from cluster')
q.remCmds = ['echo `svmips`']
rv = q.connectSSH()
# 3. Run remote commands
rawResponse = rv
logging.info("connectSSH Raw Response: %s" % rawResponse)
# 4. Extract and Parse SSH Responses
parsedResponse = q.connectCmdResponseParse(rawResponse)
logging.info("Host %s: Parsed Response = %s" % (target, parsedResponse))
print "cmd-response Length = ", len(parsedResponse)
cmd = parsedResponse[0]
# We get >1 lists sometimes so this won't do
# response = parsedResponse[1]
# print "response part length = ", len(response)
# Hack
response = parsedResponse[1][0]
# Replace Hack after making this work
# response = filter(None, response)
# Remove empty lists won't work because we want to get rid of a string
# responseClean = [x for x in response if x]
logging.info("Host %s: cmd = %s, ,Response = %s" % (target, cmd, response))
cvmIpStr = filter(lambda x: x in string.printable, response)
cvmIpList = cvmIpStr.split()
logging.debug("cvmIpList = %s" % cvmIpList)

# Check SNMP Local test Host Installation
# rm -Rf ~/.snmp
# sudo yum -y remove net-snmp net-snmp-utils net-snmp-devel
logging.info('Check SNMP Local test Host Installation')
rv = p.snmpInstallCheck()
logging.info("snmpInstallCheck rv = %d" % rv)

# Retrieve VENDOR-MIB From Cluster CVM
logging.info('Retrieve VENDOR-MIB From Cluster CVM')
rv = p.snmpInstallVendorMIB()
logging.info("snmpInstallVendorMIB output = %s" % rv)

# Configure SNMP Users On Cluster CVM
logging.info('Configure SNMP Users On Cluster CVM')
rv = p.snmpUserVendorConfig()
logging.info("snmpConfigNtxUsers output = %s" % rv)
rawResponse = rv

# Parse Vendor MIB Object-Ids and Sequences into Dict
logging.info('Parse Vendor MIB Object-Ids and Sequences into Dict')
rv = p.snmpMibParse()
mibData = rv
logging.info("\n\nModule: snmpMibParse response = %s" % mibData)

# Perform SNMP MIB Walk Operations Test
# Loop Setup
mibName = os.path.basename(mibFileSpec)
logging.debug("mibName = %s" % mibName)
# Do the MIB Walk
logging.info('SNMP MIB Walk Test')
mibRoot = mibName + "::" + mibData['MODULE-IDENTITY']['entryName']
myOID = mibRoot
myOIDList = [mibRoot]
logging.debug("myOIDList = %s" % myOIDList)
# Construct Individual SNMP Output log file spec
currentDirSpec = os.getcwd()
dirBaseSpec, curDir = os.path.split(currentDirSpec)
fBase = myOID.replace("::","-")
fBase = fBase.replace(".","-")
fName = p.snmpCmd + '-' + fBase + '.out'
fLogSpec = os.path.join(dirBaseSpec, "logs", fName)
p.snmpOutLog = fLogSpec
p.snmpOIDList = myOIDList
rv = p.snmpExecutor()
if p.snmpFormat:
  snmpOutDict = rv
  logging.info("snmpOutDict = %s" % snmpOutDict)
else:
  snmpOut = rv
  logging.info("snmpOut = %s" % snmpOut)
