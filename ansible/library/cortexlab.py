from __future__ import print_function
#!/usr/bin/env python

# Copyright (c) 2018, Palo Alto Networks <techbizdev@paloaltonetworks.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

DOCUMENTATION = '''
---
module: cortexlab_config
short_description: Configures NGFW for Cortex Lab
description:
    - Configures NGFW for Cortex Lab use case
author:
    - Palo Alto Networks
    - Francesco Vigo (fvigo)
version_added: "0.0"
requirements:
    - pan-python
    - pan-device
options:
    ngfw_ip_address:
        description:
            - IP address (or hostname) of NGFW
        required: true
    ngfw_password:
        description:
            - password for authentication on NGFW
        required: true
    ngfw_username:
        description:
            - username for authentication on NGFW
        required: false
        default: "admin"
    datalake_region:
        description:
            - Cortex Data Lake Region
        required: true
    datalake_psk:
        description:
            - Cortex Data Lake Pre Shared Key
        required: false
    localuser_name:
        description:
            - Name of the local user
        required: true
    localuser_newpassword:
        description:
            - New password of the local user
        required: true
    external_ip:
        description:
            - External IP for GlobalProtect
        required: true
'''

EXAMPLES = '''
# configure Cortex lab
- name: cortex lab
  appframework_template:
    ngfw_ip_address: "192.168.1.10"
    ngfw_username: "admin"
    ngfw_password: "admin"
    datalake_region: "americas"
    datalake_psk: "1234556"
    localuser_name: "vpnuser"
    localuser_newpassword: "password"
    external_ip: "1.2.3.4"
'''

import ssl
import sys
import time
import json
import re
import os

try:
    import pan.xapi
    from pandevice import firewall
    from pandevice import device
except ImportError:
    print("failed=True msg='pan-python and pan-device required for this module'")
    sys.exit(1)

def syncjob(ngfw, job_id, interval=0.5):
        try:
            import http.client as httplib
        except ImportError:
            import httplib
        if interval is not None:
            try:
                interval = float(interval)
                if interval < 0:
                    raise ValueError
            except ValueError:
                raise err.PanDeviceError('Invalid interval: %s' % interval)

        try:
            job = job_id.find('./result/job')
            if job is None:
                return False
            job = job.text
        except AttributeError:
            job = job_id

        cmd = 'show jobs id "%s"' % job
        start_time = time.time()

        attempts = 0
        while True:
            try:
                attempts += 1
                job_xml = ngfw.op(cmd=cmd, cmd_xml=True)
            except (pan.xapi.PanXapiError, err.PanDeviceError) as e:
                # Connection errors (URLError) are ok, this can happen in PAN-OS 7.0.1 and 7.0.2
                # if the hostname is changed
                # Invalid cred errors are ok because FW auth system takes longer to start up in these cases
                # Other errors should be raised
                if not str(e).startswith("URLError:") and not str(e).startswith("Invalid credentials."):
                    # Error not related to connection issue.  Raise it.
                    raise e
                else:
                    #self._logger.debug2("Sleep %.2f seconds" % interval)
                    time.sleep(interval)
                    continue
            except httplib.BadStatusLine as e:
                # Connection issue.  The firewall is currently restarting the API service or rebooting
                #self._logger.debug2("Sleep %.2f seconds" % interval)
                time.sleep(interval)
                continue

            status = job_xml.find("./result/job/status")
            if status is None:
                raise pan.xapi.PanXapiError('No status element in ' + "'%s' response" % cmd)
            if status.text == "FIN":
                # Job completed, check if it's ok
                res = job_xml.find("./result/job/result")
                if res is None:
                    raise pan.xapi.PanXapiError('No job result element in ' + "'%s' response" % cmd)
                if res.text == "OK":
                    return True
                else:
                    raise pan.xapi.PanXapiError('Job result is: {}'.format(res.text))
            else:
                pass

        time.sleep(interval)

def setConfigEntry(fw, xpath, value, module):
    if 'hostname' not in fw or 'username' not in fw or 'password' not in fw:
        module.fail_json(msg='Device credentials not specified!')

    #print('Connecting to device')

    try:
        xapi = pan.xapi.PanXapi(hostname=fw['hostname'], api_username=fw['username'], api_password=fw['password'])
    except pan.xapi.PanXapiError as msg:
        module.fail_json(msg='pan.xapi.PanXapi: {}'.format(msg))
    except Exception as e:
        module.fail_json(msg='Exception: {}'.format(e))

    #print('Connected to device, setting configuration in path: {}'.format(xpath))

    try:
        xapi.set(xpath=xpath, element=value)
    except pan.xapi.PanXapiError as msg:
        if "Unauthorized request" in str(msg): # skip duplicate region set
            return True
        module.fail_json(msg='pan.xapi.PanXapi (set): {}'.format(msg))

    #print('Configuration successfully set!')
    return True        

def configureNGFW(fw, localuser_name, localuser_phash, admin_phash, extip, datalake_region, datalake_psk, module):
    if 'hostname' not in fw or 'username' not in fw or 'password' not in fw:
        raise RuntimeError('Firewall credentials not specified!')

    # Configure admin user password again (as it was overwritten by config import)
    # Configure vpn user password
    xpath = "/config/mgt-config/users/entry[@name='admin']"
    element = '<phash>{}</phash>'.format(admin_phash)
    if not setConfigEntry(fw, xpath, element, module):
        raise RuntimeError('Error configuring admin password')

    # Configure vpn user password
    xpath = "/config/shared/local-user-database/user/entry[@name='{}']".format(localuser_name)
    element = '<phash>{}</phash>'.format(localuser_phash)
    if not setConfigEntry(fw, xpath, element, module):
        raise RuntimeError('Error configuring vpn user password')

    # Configure GP Portal for external gateway
    xpath = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/global-protect/global-protect-portal/entry[@name='GP-Portal']/client-config/configs/entry[@name='agentconfig']/gateways/external/list/entry[@name='ext']/ip"
    element = '<ipv4>{}</ipv4>'.format(extip)
    if not setConfigEntry(fw, xpath, element, module):
        raise RuntimeError('Error configuring GP External IP')

    # Configure Data Lake Region, only if PSK is enabled
    if(datalake_psk and datalake_psk != "disabled"):
        # set deviceconfig setting logging logging-service-forwarding logging-service-regions
        xpath = "/config/deviceconfig/setting/logging/logging-service-forwarding"
        element = '<logging-service-regions>{}</logging-service-regions><enable>yes</enable>'.format(datalake_region)
        if not setConfigEntry(fw, xpath, element, module):
            raise RuntimeError('Error configuring Data Lake Region')

    # print('NGFW Configuration complete!')
    return True

def getDeviceSerial(fw, module):
    if 'hostname' not in fw or 'username' not in fw or 'password' not in fw:
        module.fail_json(msg='Device credentials not specified!')

    device = firewall.Firewall(fw['hostname'], fw['username'], fw['password'])
    devInfo = device.refresh_system_info()
    devSerial = devInfo.serial
    #print('Device Serial = {}'.format(devSerial))
    return devSerial


def getDevicePhash(device, password, module):
    if 'hostname' not in device or 'username' not in device or 'password' not in device:
        module.fail_json(msg='Device credentials not specified!')

    dev = firewall.Firewall(device['hostname'], device['username'], device['password'])
    phash = dev.request_password_hash(password)
    return phash

def configureDataLakeWithPSK(device, password, psk, module):
    # request logging-service-forwarding certificate fetch-noproxy pre-shared-key <value>
    try:
        if 'hostname' not in device or 'username' not in device or 'password' not in device:
            module.fail_json(msg='Device credentials not specified!')
        ngfw = firewall.Firewall(device['hostname'], device['username'], device['password'])
        #print("Configuring Data Lake on NGFW")
        cmd='<request><logging-service-forwarding><certificate><fetch-noproxy><pre-shared-key>{}</pre-shared-key></fetch-noproxy></certificate></logging-service-forwarding></request>'.format(psk)
        response = ngfw.op(cmd=cmd, cmd_xml=False)
        result = response.find('./result').text
        if result:
            reg = r'^Successfully scheduled logging service certificate fetch job with a job id of ([0-9]*)$'
            m = re.search(reg, result)
            if m and m.group(1):
                job_id = m.group(1)
                if job_id:
                    res = syncjob(ngfw, job_id=job_id)
                    if not res:
                        raise pan.xapi.PanXapiError('Not success')
                else:
                    raise pan.xapi.PanXapiError('Job ID not found')
            else:
                raise pan.xapi.PanXapiError('Unexpected response: {}'.format(result))
        else:
            raise pan.xapi.PanXapiError('No result in response')
        #print("Configured Data Lake on NGFW")    
    except Exception as e:
        module.fail_json(msg='Fail on Data Lake PSK configuration: {}'.format(e))
        return False
    return True

def ngfwCommit(fw, devicegroup, module):
    try:
        ngfw = firewall.Firewall(fw['hostname'], fw['username'], fw['password'])
        #print("Committing on NGFW")
        ngfw.commit(sync=True)
        #print("Committed on NGFW")
    except Exception as e:
        module.fail_json(msg='Fail on commit: {}'.format(e))
    return True

def main():
    argument_spec = dict(
        ngfw_ip_address=dict(default=None),
        ngfw_password=dict(default=None, no_log=True),
        ngfw_username=dict(default='admin'),
        datalake_region=dict(default='americas'),
        datalake_psk=dict(default=None, no_log=True),
        localuser_name=dict(default=None),
        localuser_newpassword=dict(default=None, no_log=True),
        external_ip=dict(default=None, no_log=True)

    )
    module = AnsibleModule(argument_spec=argument_spec)

    ngfw_ip_address = module.params["ngfw_ip_address"]
    if not ngfw_ip_address:
        module.fail_json(msg="NGFW ip_address should be specified")
    ngfw_password = module.params["ngfw_password"]
    if not ngfw_password:
        module.fail_json(msg="NGFW password is required")
    ngfw_username = module.params['ngfw_username']

    localuser_name = module.params['localuser_name']
    localuser_newpassword = module.params['localuser_newpassword']
    extip = module.params['external_ip']
    datalake_region = module.params['datalake_region']
    datalake_psk = module.params['datalake_psk']

    changed = False

    fw = {
        'hostname' : ngfw_ip_address,
        'username' : ngfw_username,
        'password' : ngfw_password
    }

    try:
        #fwSerial = getDeviceSerial(fw, module)
        localuser_phash = getDevicePhash(fw, localuser_newpassword, module)
        admin_phash = getDevicePhash(fw, ngfw_password, module)
        changed |= configureNGFW(fw, localuser_name, localuser_phash, admin_phash, extip, datalake_region, datalake_psk, module)
        if(datalake_psk and datalake_psk != "disabled"):
            changed |= configureDataLakeWithPSK(fw, admin_phash, datalake_psk, module)
        #no commit changed |= ngfwCommit(fw, module)
    except Exception as e:
        module.fail_json(msg='Got exception: {}'.format(e))

    module.exit_json(changed=changed, msg="okey dokey")

from ansible.module_utils.basic import *  # noqa


if __name__ == "__main__":
    main()
