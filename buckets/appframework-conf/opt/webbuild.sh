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
        REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt ${CFNSIGNAL} -s false --stack ${AWSSTACKNAME} --region ${AWSREGION} --resource ${SELF} -r ${msg}
    fi
    exit 1
fi

source ./vars.sh
cd ${DEPLOYPATH}

if [ ! -r "/home/ubuntu/web-traffic-generator/config.py" ]; then
    msg="Cannot find /home/ubuntu/web-traffic-generator/config.py, aborting..."
    echo $msg
    if [ "${FIRSTRUN}" = true]; then
        REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt ${CFNSIGNAL} -s false --stack ${AWSSTACKNAME} --region ${AWSREGION} --resource ${SELF} -r ${msg}
    fi
    exit 1
fi

if [  -z "$FIREWALLIP"  ]; then
    msg="FIREWALLIP variable not set, aborting..."
    echo $msg
    if [ "${FIRSTRUN}" = true ]; then
        REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt ${CFNSIGNAL} -s false --stack ${AWSSTACKNAME} --region ${AWSREGION} --resource ${SELF} -r ${msg}
    fi
    exit 1
fi

if [  -z "$ADMINPWD"  ]; then
    msg="ADMINPWD variable not set, aborting..."
    echo $msg
    if [ "${FIRSTRUN}" = true ]; then
        REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt ${CFNSIGNAL} -s false --stack ${AWSSTACKNAME} --region ${AWSREGION} --resource ${SELF} -r ${msg}
    fi
    exit 1
fi

if [  -z "$NETBIOSDOMAIN"  ]; then
    msg="NETBIOSDOMAIN variable not set, aborting..."
    echo $msg
    if [ "${FIRSTRUN}" = true ]; then
        REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt ${CFNSIGNAL} -s false --stack ${AWSSTACKNAME} --region ${AWSREGION} --resource ${SELF} -r ${msg}
    fi
    exit 1
fi

# Start/Restart apache
echo "Restarting Apache2"
systemctl restart apache2

# Create UID file
echo "Creating /tmp/uid.xml UID file"
cat <<_EOF_ > /tmp/uid.xml
<uid-message>
  <type>update</type>
  <payload>
    <login>
      <entry name="${NETBIOSDOMAIN}\\user1" ip="10.0.1.101"/>
    </login>
  </payload>
</uid-message>
_EOF_

# Prepare panrc file
echo "Creating /.panrc file"
panxapi.py -h ${FIREWALLIP} -l "admin:${ADMINPWD}" -k -t '' > /tmp/.panrc

echo "Mapping IP to UserID on Firewall"
cd /tmp && panxapi.py -U /tmp/uid.xml
cd ${OLDPWD}

# Prepare crontab
echo "Creating crontab for UID mapping on user ubuntu"
echo '*/15 * * * * cd /tmp && /usr/local/bin/panxapi.py -U uid.xml' > /tmp/crontab_uid.txt
sudo -u ubuntu bash -c "crontab /tmp/crontab_uid.txt"

# Create web traffic generator startup script
echo "Creating web generator startup script"
echo "#!/bin/bash" > /home/ubuntu/webgen.sh
echo "export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt" >> /home/ubuntu/webgen.sh
echo "nohup python /home/ubuntu/web-traffic-generator/gen.py 1>>/tmp/webgen.stdout 2>>/tmp/webgen.stderr &" >> /home/ubuntu/webgen.sh
echo "exit 0" >> /home/ubuntu/webgen.sh
chown ubuntu:ubuntu /home/ubuntu/webgen.sh
chmod +x /home/ubuntu/webgen.sh

# Configure script for startup
grep "webgen" /etc/crontab 1> /dev/null 2>&1
retVal=$?
if [ $retVal -gt 0 ]; then
    echo "Configuring web generator script at startup"
    echo "@reboot ubuntu /home/ubuntu/webgen.sh" >> /etc/crontab
else
    echo "Web traffic generator already in /etc/crontab at reboot, skipping" 
fi

# Start web traffic generator
echo "Starting web generator in background"
sudo -u ubuntu /home/ubuntu/webgen.sh &

# Send cfn-success p rovisioning is complete
echo "Sending CFN success signal!"
if [ "${FIRSTRUN}" = true ]; then
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt ${CFNSIGNAL} -s true --stack ${AWSSTACKNAME} --region ${AWSREGION} --resource ${SELF}
fi