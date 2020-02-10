#!/bin/bash

# ////////////////////////////////////////////////////////////////////////////
# SCRIPT:   snmpget.sh
#
# AUTHOR:   Eric Nelson
#
# PLATFORM: Not Platform Dependent
#
# PURPOSE:  This shell script performs a snmpGet using Net-SNMP and passed 
#           in args 
#
# INPUTS:   -v <SNMP version>               = [v2c|v3]
#           -u <v3 snmp user>               = a string
#           -a <v3 authentication type>     = [MD5|SHA]
#           -b <v3 authentication keyword>  = a string
#           -p <v3 priv type>               = [AES|DES|nopriv]
#           -q <v3 priv keyword>            = a string or nopriv
#           -r <v2c SNMP Read Community>    = a string
#           -w <v2c SNMP write community>   = a string
#           -o <OID>                        = a string
#           -t <target host ip>             = Target IP address
#
# CALL
#           ./snmpget-ng.sh -v "v3" -u "testerSHA"  -a "SHA" -b "snmptester123" -p "nopriv" -q "nopriv" -o "VENDOR-MIB::clusterVersion.0" -t "10.1.144.53"
#           ./snmpget-ng.sh -v "v2c" -r "vendor" -o "SNMPv2-MIB::sysName.0" -t "10.1.1.111"
#
# REV:      2015-05-06  by Eric Nelson
#           Created Script
#
# ////////////////////////////////////////////////////////////////////////////

# ////////////////////////////////////////////////////////////////////////////
function usage
{
    echo -e "\nUSAGE: $THISSCRIPT \"-v <v2c> -r <read-community> -w <write-community> -o <snmpMib::miboid> -t <snmp target ip>\" \n"
    echo -e "\nUSAGE: $THISSCRIPT \"-v <v3>  -u <snmp user> -a <auth-type> -b <auth-key> -p <priv-type> -q <priv-key> -o <snmpMib::miboid> -t <snmp target ip>\" \n"
    exit 1
}

# ////////////////////////////////////////////////////////////////////////////
function usage_error
{
    echo -e "\nERROR: This shell script requires 4 command line arguments to set
           up a SNMPv2c transaction with a remote target.\n"
    echo -e "\nERROR: This shell script requires 7 command line arguments to set
           up a SNMPv3 transaction with a remote target.\n"
    usage
}

# ////////////////////////////////////////////////////////////////////////////
# MAIN
# ////////////////////////////////////////////////////////////////////////////

#
# DEFINE VARIABLES HERE 
#
THISSCRIPT=$(basename $0)
DEBUG=0

#
# CHECK USAGE
#
if (( $# > 19 || $# < 4 ))
then 
    usage_error
    exit 1
fi

#
# GET COMMAND LINE ARGS
#
SNMPVER="null"
SNMP2CREAD="null"
SNMP2CWRITE="null"
SNMPUSER="null"
AUTHTYPE="null"
AUTHKEY="null"
PRIVTYPE="nopriv"
PRIVKEY="nopriv"
MYOID="null"
TGTHOST="null"

while getopts ":a:b:o:p:q:r:t:u:v:w:" NEWVAR
do
    case $NEWVAR in
        a)  AUTHTYPE=$OPTARG
            ;;
        b)  AUTHKEY=$OPTARG
            ;;
        o)  MYOID=$OPTARG
            ;;
        p)  PRIVTYPE=$OPTARG
            ;;
        q)  PRIVKEY=$OPTARG
            ;;
        r)  SNMP2CREAD=$OPTARG
            ;;
        t)  TGTHOST=$OPTARG
            ;;
        u)  SNMPUSER=$OPTARG
            ;;
        v)  SNMPVER=$OPTARG
            ;;
        w)  SNMP2CWRITE=$OPTARG
            ;;
        \?) usage
            exit 1
            ;;
    esac
done

if (( $DEBUG == 1 )) 
then
    echo -e "\nDEBUG:  Script       = $THISSCRIPT"
    echo -e "DEBUG:  AUTHTYPE     = $AUTHTYPE"
    echo -e "DEBUG:  AUTHKEY      = $AUTHKEY"
    echo -e "DEBUG:  MYOID        = $MYOID"
    echo -e "DEBUG:  PRIVTYPE     = $PRIVTYPE"
    echo -e "DEBUG:  PRIVKEY      = $PRIVKEY"
    echo -e "DEBUG:  SNMP2CREAD   = $SNMP2CREAD"
    echo -e "DEBUG:  TGTHOST      = $TGTHOST"
    echo -e "DEBUG:  SNMPUSER     = $SNMPUSER"
    echo -e "DEBUG:  SNMPVER      = $SNMPVER"
    echo -e "DEBUG:  SNMP2CWRITE  = $SNMP2CWRITE\n"
fi

#
# START TESTS
# 
CAPAUTHTYPE=`echo ${AUTHTYPE} | tr [a-z] [A-Z]`
CAPPRIVTYPE=`echo ${PRIVTYPE} | tr [a-z] [A-Z]`
if [ "$SNMPVER" == "v2c" ]
then
  if (( $DEBUG == 1 )) 
  then
    echo -e "DEBUG:  Executing SNMP v2c MIB Get Command"
  fi
  snmpget -v 2c -c ${SNMP2CREAD} ${TGTHOST} ${MYOID} 
else
  if [ "$CAPPRIVTYPE" == "NOPRIV" ] 
  then
    if (( $DEBUG == 1 )) 
    then
      echo -e "DEBUG:  Executing SNMP v3 MIB Get Command AuthNoPriv"
    fi
    snmpget -v 3 -n "" -u ${SNMPUSER} -a ${CAPAUTHTYPE} -A ${AUTHKEY} -l authNoPriv ${TGTHOST} ${MYOID} 
  else 
    if (( $DEBUG == 1 )) 
    then
      echo -e "DEBUG:  Executing SNMP v3 MIB Get Command AuthPriv"
    fi
    snmpget -v 3 -n "" -u ${SNMPUSER} -a ${CAPAUTHTYPE} -A ${AUTHKEY} -x ${CAPPRIVTYPE} -X ${PRIVKEY} -l authPriv ${TGTHOST} ${MYOID}
  fi
fi

