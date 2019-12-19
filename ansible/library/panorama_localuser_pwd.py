#!/usr/bin/env python

#  Copyright 2018 Palo Alto Networks, Inc
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

DOCUMENTATION = '''
---
module: panos_localuser_pwd
short_description: Module used to change the password of a local user via Panorama
description:
    - Module used to change the password of a local user via Panorama
author: "Luigi Mori (@jtschichold), Ivan Bojer (@ivanbojer), Patrik Malinen (@pmalinen), Francesco Vigo (@fvigo)"
version_added: "2.4"
requirements:
    - pan-python can be obtained from PyPI U(https://pypi.python.org/pypi/pan-python)
    - pandevice can be obtained from PyPI U(https://pypi.python.org/pypi/pandevice)
notes:
    - Checkmode is not supported.
    - Panorama is supported
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device being configured.
        required: true
    username:
        description:
            - Username credentials to use for auth unless I(api_key) is set.
        default: "admin"
    password:
        description:
            - Password credentials to use for auth unless I(api_key) is set.
        required: true
    api_key:
        description:
            - API key that can be used instead of I(username)/I(password) credentials.
    template:
        description:
            - Template name.
    localuser:
        description:
            - Local User.
    newpassword:
        description:
            - New Password.
    commit:
        description:
            - Commit configuration if changed.
        default: true

'''

EXAMPLES = '''
- name: set localuser password
  panorama_localuser_pwd:
    ip_address: "192.168.1.1"
    password: "admin"
    template: "Template1
    localuser: "testuser"
    newpassword: "password"
'''

RETURN = '''
# Default return values
'''

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import get_exception

try:
    from pan.xapi import PanXapiError
    import pandevice
    from pandevice import base
    from pandevice import panorama
    from pandevice.device import SystemSettings
    HAS_LIB = True
except ImportError:
    HAS_LIB = False

def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True, no_log=True),
        username=dict(default='admin'),
        api_key=dict(no_log=True),
        newpassword=dict(required=True, no_log=True),
        localuser=dict(required=True),
        template=dict(required=True),
        commit=dict(type='bool', default=True)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False,
                           required_one_of=[['api_key', 'password']])
    if not HAS_LIB:
        module.fail_json(msg='Missing required libraries.')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']
    local = module.params['localuser']
    commit = module.params['commit']
    api_key = module.params['api_key']
    newpassword = module.params["newpassword"]    
    template = module.params['template']

    # Create the device with the appropriate pandevice type
    device = base.PanDevice.create_from_device(ip_address, username, password, api_key=api_key)
    changed = False
    try:
        phash = device.request_password_hash(password)

        #return phash        
        ss = SystemSettings.refreshall(device)[0]

        print('changed = {}'.format(changed))
        if dns_server_primary is not None and ss.dns_primary != dns_server_primary:
            ss.dns_primary = dns_server_primary
            changed = True
        print('changed = {}'.format(changed))
        if dns_server_secondary is not None and ss.dns_secondary != dns_server_secondary:
            ss.dns_secondary = dns_server_secondary
            changed = True
        print('changed = {}'.format(changed))
        if panorama_primary is not None and ss.panorama != panorama_primary:
            ss.panorama = panorama_primary
            changed = True
        print('changed = {}'.format(changed))
        if panorama_secondary is not None and ss.panorama2 != panorama_secondary:
            ss.panorama2 = panorama_secondary
            changed = True
        print('changed = {}'.format(changed))
        if ntp_server_primary is not None:
            changed |= set_ntp_server(ss, ntp_server_primary, primary=True)
        print('changed = {}'.format(changed))
        if ntp_server_secondary is not None:
            changed |= set_ntp_server(ss, ntp_server_secondary, primary=False)
        print('changed = {}'.format(changed))
        if login_banner and ss.login_banner != login_banner:
            ss.login_banner = login_banner
            changed = True
        if timezone and ss.timezone != timezone:
            ss.timezone = timezone
            changed = True
        if update_server and ss.update_server != update_server:
            ss.update_server = update_server
            changed = True
        if hostname and ss.hostname != hostname:
            ss.hostname = hostname
            changed = True
        if domain and ss.domain != domain:
            ss.domain = domain
            changed = True

        print('changed = {}'.format(changed))
        if changed:
            ss.apply()
        if commit:
            device.commit(sync=True)
    except PanXapiError:
        exc = get_exception()
        module.fail_json(msg=exc.message)
    except PanDeviceError as e:
        module.fail_json(msg='Failed to change password: {}'.format(e))

    module.exit_json(changed=changed, msg="okey dokey")

if __name__ == '__main__':
    main()