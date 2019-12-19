from __future__ import print_function
import sys
import json
import os
from pandevice import panorama
from pandevice import firewall
from pandevice import device
import pan.xapi
import ssl
#import logging
import time
#logging.basicConfig(filename="/tmp/panorama_setup.log", level=logging.DEBUG)
#logging.getLogger("pandevice").setLevel(logging.DEBUG)
#logging.getLogger().setLevel(pan.xapi.DEBUG3)

def editPanoramaEntry(pn, xpath, file):
    if 'hostname' not in pn or 'username' not in pn or 'password' not in pn:
        print('Panorama credentials not specified!')
        return False

    print('Reading configuration file: {}'. format(file))
    try:
        f = open(file,'r')
        d = f.read()
        f.close()
    except Exception as msg:
        print('Error while reading file: {}'.format(msg))
        return False
    
    print('Configuration file read, connecting to Panorama...')

    try:
        xapi = pan.xapi.PanXapi(hostname=pn['hostname'], api_username=pn['username'], api_password=pn['password'])
    except pan.xapi.PanXapiError as msg:
        print('pan.xapi.PanXapi: {}'.format(msg))
        return False
    except Exception as e:
        print('Exception: {}'.format(e))
        return False
 
    print('Connected to Panorama, editing configuration in path: {}'.format(xpath))
 
    try:
        xapi.edit(xpath=xpath, element=d)
    except pan.xapi.PanXapiError as msg:
        print('pan.xapi.PanXapi (edit): {}'.format(msg))
        return False
    
    print('Configuration successfully edited!')
    return True

def setPanoramaEntry(pn, xpath, value):
    if 'hostname' not in pn or 'username' not in pn or 'password' not in pn:
        print('Panorama credentials not specified!')
        return False

    print('Connecting to Panorama')

    try:
        xapi = pan.xapi.PanXapi(hostname=pn['hostname'], api_username=pn['username'], api_password=pn['password'])
    except pan.xapi.PanXapiError as msg:
        print('pan.xapi.PanXapi: {}'.format(msg))
        return False
    except Exception as e:
        print('Exception: {}'.format(e))
        return False
 
    print('Connected to Panorama, setting configuration in path: {}'.format(xpath))
 
    try:
        xapi.set(xpath=xpath, element=value)
    except pan.xapi.PanXapiError as msg:
        print('pan.xapi.PanXapi (set): {}'.format(msg))
        return False
    
    print('Configuration successfully set!')
    return True

def configurePanorama(pn, fwSerial, sharedFile, devGroupName, devGroupFile, templateName, templateFile, templateStackName, templateStackFile):
    if 'hostname' not in pn or 'username' not in pn or 'password' not in pn:
        raise RuntimeError('Panorama credentials not specified!')


    print('Editing shared configuration')
    if not editPanoramaEntry(pn, "/config/shared", sharedFile):
        raise RuntimeError('Error editing shared resource')

    print('Editing Device Group: {}'.format(devGroupName))    
    if not editPanoramaEntry(pn, "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='{}']".format(devGroupName), devGroupFile):
        raise RuntimeError('Error editing Device Group')

    print('Editing Template: {}'.format(templateName))    
    if not editPanoramaEntry(pn, "/config/devices/entry[@name='localhost.localdomain']/template/entry[@name='{}']".format(templateName), templateFile):
        raise RuntimeError('Error editing Template')

    print('Editing Template Stack: {}'.format(templateStackName)) 
    if not editPanoramaEntry(pn, "/config/devices/entry[@name='localhost.localdomain']/template-stack/entry[@name='{}']".format(templateStackName), templateStackFile):
        raise RuntimeError('Error editing Template Stack')

    print('Adding device {} to Panorama managed devices'.format(fwSerial))
    xpath = "/config/mgt-config/devices"
    element = '<entry name=\"{}\"><vsys><entry name=\"vsys1\"/></vsys></entry>'.format(fwSerial)
    if not setPanoramaEntry(pn, xpath, element):
        raise RuntimeError('Error adding device to Panorama managed devices')

    print('Adding device {} to Panorama Device Group: {}'.format(fwSerial, devGroupName))
    xpath = "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='{}']/devices".format(devGroupName)
    element = '<entry name=\"{}\"><vsys><entry name=\"vsys1\"/></vsys></entry>'.format(fwSerial)
    if not setPanoramaEntry(pn, xpath, element):
        raise RuntimeError('Error adding device to Panorama Device Group')

    print('Adding device {} to Panorama Template Stack: {}'.format(fwSerial, templateStackName))
    xpath = "/config/devices/entry[@name='localhost.localdomain']/template-stack/entry[@name='{}']/devices".format(templateStackName)
    element = '<entry name=\"{}\"/>'.format(fwSerial)
    if not setPanoramaEntry(pn, xpath, element):
        raise RuntimeError('Error adding device to Panorama Template Stack')


    print('Panorama Configuration complete!')

def getDeviceSerial(fw):
    if 'hostname' not in fw or 'username' not in fw or 'password' not in fw:
        raise  RuntimeError('Device credentials not specified!')

    device = firewall.Firewall(fw['hostname'], fw['username'], fw['password'])
    devInfo = device.refresh_system_info()
    devSerial = devInfo.serial
    print('Device Serial = {}'.format(devSerial))
    return devSerial

    
def panoramaCommitAll(pn, devicegroup):
    pano = panorama.Panorama(pn['hostname'], pn['username'], pn['password'])
    print("Committing on Panorama")
    pano.commit(sync=True)
    print("Committed on Panorama")
    print("Committing All on Panorama")
    pano.commit_all(sync=True, sync_all=True, devicegroup=devicegroup)
    print("Committed All on Panorama")

def main():
    pn = {
        'hostname' : '10.0.0.20',
        'username' : 'admin',
        'password' : 'PaloAlto1!'
    }
    fw = {
        'hostname' : '10.0.0.99',
        'username' : 'admin',
        'password' : 'PaloAlto1!'
    }
    files = {
        'shared': './shared.xml',
        'devgroup': './devgroup.xml',
        'template': './template.xml',
        'template-stack': './template-stack.xml'
    }

    objectNames = {
        'devgroup': 'DevGroup1',
        'template': 'Template1',
        'template-stack': 'TS1'
    }

    #prodlog = logging.getLogger('panorama_setup')

    try:
        fwSerial = getDeviceSerial(fw)
        configurePanorama(pn, fwSerial, files['shared'], objectNames['devgroup'], files['devgroup'], objectNames['template'], files['template'], objectNames['template-stack'], files['template-stack'])
        panoramaCommitAll(pn, objectNames['devgroup'])
    except Exception as e:
        print('Got Exception: {}'.format(e))
        sys.exit(0)

if __name__ == "__main__":
    main()
