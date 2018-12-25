#!/bin/bash
CFNSIGNAL="/opt/aws/bin/cfn-signal"

# True if this is the first run
FIRSTRUN=true

if [ ! -x "$CFNSIGNAL" ]; then
    echo "cfn-signal not found in: ${CFNSIGNAL}"
    FIRSTRUN=false
fi
if [ -z "$SELF" ]; then FIRSTRUN=false; fi
if [ -z "$AWSSTACKNAME" ]; then FIRSTRUN=false; fi
if [ -z "$AWSREGION" ]; then FIRSTRUN=false; fi
echo "Build script started, FIRSTRUN is ${FIRSTRUN}"

# Source script file
if [ ! -x ./vars.sh ]; then
    msg="Cannot find vars.sh file, aborting..."
    echo $msg
    if [ "${FIRSTRUN}" = true ]; then
        echo "FIRSTRUN: Sending CFN fail signal!"    
        ${CFNSIGNAL} -s false --stack ${AWSSTACKNAME} --region ${AWSREGION} --resource ${SELF} -r ${msg}
    fi
    exit 1
fi

source ./vars.sh

if [  -z "$DEPLOYPATH"  ]; then
    msg="DEPLOYPATH variable not set, aborting..."
    echo $msg
    if [ "${FIRSTRUN}" = true ]; then
        echo "FIRSTRUN: Sending CFN fail signal!"    
        REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt ${CFNSIGNAL} -s false --stack ${AWSSTACKNAME} --region ${AWSREGION} --resource ${SELF} -r ${msg}
    fi
    exit 1
fi

cd ${DEPLOYPATH}


if [ ! -r "${DEPLOYPATH}/vars.yml" ]; then
    msg="Cannot find vars.yml, aborting..."
    echo $msg
    if [ "${FIRSTRUN}" = true ]; then
        echo "FIRSTRUN: Sending CFN fail signal!"
        ${CFNSIGNAL} -s false --stack ${AWSSTACKNAME} --region ${AWSREGION} --resource ${SELF} -r ${msg}
    fi
    exit 1
fi

if [ ! -r "${DEPLOYPATH}/key.pem" ]; then
    msg="Cannot find key.pem, aborting..."
    echo $msg
    if [ "${FIRSTRUN}" = true ]; then
        echo "FIRSTRUN: Sending CFN fail signal!"    
        ${CFNSIGNAL} -s false --stack ${AWSSTACKNAME} --region ${AWSREGION} --resource ${SELF} -r ${msg}
    fi
    exit 1
fi

if [ ! -r "${DEPLOYPATH}/devices_setup.yml" ]; then
    msg="Cannot find devices_setup.yml, aborting..."
    echo $msg
    if [ "${FIRSTRUN}" = true ]; then
        echo "FIRSTRUN: Sending CFN fail signal!"    
        ${CFNSIGNAL} -s false --stack ${AWSSTACKNAME} --region ${AWSREGION} --resource ${SELF} -r ${msg}
    fi
    exit 1
fi

if [ ! -r "${DEPLOYPATH}/panorama_setup.yml" ]; then
    msg="Cannot find panorama_setup.yml, aborting..."
    echo $msg
    if [ "${FIRSTRUN}" = true ]; then
        echo "FIRSTRUN: Sending CFN fail signal!"    
        ${CFNSIGNAL} -s false --stack ${AWSSTACKNAME} --region ${AWSREGION} --resource ${SELF} -r ${msg}
    fi
    exit 1
fi

if [ ! -r "${DEPLOYPATH}/firewall_setup.yml" ]; then
    msg="Cannot find firewall_setup.yml, aborting..."
    echo $msg
    if [ "${FIRSTRUN}" = true ]; then
        echo "FIRSTRUN: Sending CFN fail signal!"    
        ${CFNSIGNAL} -s false --stack ${AWSSTACKNAME} --region ${AWSREGION} --resource ${SELF} -r ${msg}
    fi
    exit 1
fi

if [ ! -r "${DEPLOYPATH}/appframework_lab.yml" ]; then
    msg="Cannot find appframework_lab.yml, aborting..."
    echo $msg
    if [ "${FIRSTRUN}" = true ]; then
        echo "FIRSTRUN: Sending CFN fail signal!"    
        ${CFNSIGNAL} -s false --stack ${AWSSTACKNAME} --region ${AWSREGION} --resource ${SELF} -r ${msg}
    fi
    exit 1
fi

# Create ansible log configuration file
echo "Creating Ansible configuration file..."
cat <<_EOF_ > ${DEPLOYPATH}/ansible.cfg
[defaults] 
log_path=${DEPLOYPATH}/ansible.log
_EOF_

# Send cfn-success now, do not wait for the full provisioning
if [ "${FIRSTRUN}" = true ]; then
    echo "FIRSTRUN: Sending CFN success signal!"
    ${CFNSIGNAL} -s true --stack ${AWSSTACKNAME} --region ${AWSREGION} --resource ${SELF}
fi

ansible-playbook ${DEPLOYPATH}/devices_setup.yml
retVal=$?
if [ $retVal -gt 1 ]; then
    echo "Error running devices_setup.yml!"
    exit 1
fi

ansible-playbook ${DEPLOYPATH}/appframework_lab.yml
retVal=$?
if [ $retVal -gt 1 ]; then
    echo echo "Error running appframework_lab.yml!"
    exit 1
fi
# Cleanup
#rm -f ${DEPLOYPATH}/vars.yml
#   rm -f ${DEPLOYPATH}/key.pem