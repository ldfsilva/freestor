#!/usr/bin/python3
import requests
import json
from datetime import datetime


def get_session_id(cdp_server_ip, username, password):
    """Get a session id to be used in later requests for a given CDP server"""
    headers = {'Content-Type': 'application/json'}
    URL = 'http://{}:/ipstor/auth/login'.format(cdp_server_ip) 
    
    data = '{}"server": "{}", "username": "{}", "password": "{}"{}'.format(
        '{', cdp_server_ip, username, password, '}'
    )
    r = requests.post(URL, headers=headers, data=data)
    session_id = r.cookies.get('session_id')
    return session_id


def get_adapter_info(cdp_server_ip, session_id):
    """Collect Fiber Channel adapter information for a given CDP server"""

    d = datetime.now()
    date = d.strftime("%Y%m%d %X")    
    data = ['date, server, adapter, vendor, wwpn, status, mode']

    for fca in range(100, 108):
        URL = 'http://{}:/ipstor/physicalresource/physicaladapter/{}/'.format(cdp_server_ip, fca)
        r = requests.get(URL, cookies={'session_id': session_id})
        adapter = r.json()
        name = adapter['data'].get('name')
        vendor = adapter['data'].get('vendor')
        bioswwpn = adapter['data'].get('bioswwpn')
        portstatus = adapter['data'].get('portstatus')
        mode = adapter['data'].get('mode')
        data.append('{},{},{},{},{},{},{}'.format(
            date, cdp_server_ip, name, vendor, bioswwpn, portstatus, mode)
        )

    return data


def get_virtual_device(cdp_server_ip, session_id):
    """Retrieve status information about all virtual devices and supporting devices."""

    headers = {'Content-Type': 'application/json'}

    URL = 'http://{}:/ipstor/logicalresource/sanresource/'.format(cdp_server_ip)
    r = requests.get(URL, cookies={'session_id': session_id}, headers=headers)

    return r


def get_badwidth(cdp_server_ip, session_id, server_t):
    """Test the network bandwidth with a replica server."""

    headers = {'Content-Type': 'application/json'}
    URL = 'http://{}:/ipstor/logicalresource/replication'.format(cdp_server_ip)

    data = json.dumps({
        "action": "test",  
        "ipaddress": server_t
    })
    r = requests.put(URL, cookies={'session_id': session_id}, data=data, headers=headers)

    return r


def get_replication_status(cdp_server_ip, session_id, vdev):
    """Returns incoming replication status for a replica device"""

    headers = {'Content-Type': 'application/json'}
    URL = 'http://{}:/ipstor/logicalresource/replication/incoming/{}'.format(cdp_server_ip, vdev)

    r = requests.get(URL, cookies={'session_id': session_id})

    return r


def get_physical_devices(cdp_server_ip, session_id):
    """Get physical devices information for a given CDP server"""
    
    URL = 'http://{}:/ipstor/physicalresource/physicaldevice/'.format(cdp_server_ip)
    d = datetime.now()
    date = d.strftime("%Y%m%d %X")
    data = ['date, server, cdp lun id, acsl, vendor, product, \
        lun name, wwid, category, lun size (bytes), total used (bytes), status']

    r = requests.get(URL, cookies={'session_id': session_id})
    devices = r.json()['data'].get('physicaldevices')

    for device in devices:
        id = device.get('id')
        acsl = device.get('acsl')
        r = requests.get(URL + id, cookies={'session_id': session_id})
        device_detail = r.json()['data']
        owner = device_detail.get('owner')
        vendor = device_detail.get('vendor')
        product = device_detail.get('product')
        name = device_detail.get('name')
        wwid = device_detail.get('wwid')
        category = device_detail.get('category')
        size = device_detail.get('size')
        used = device_detail.get('used')
        status = device_detail.get('status')        
        data.append('{},{},{},{},{},{},{},{},{},{},{},{}'.format(
            date, cdp_server_ip, id, acsl, vendor, product, name, 
            wwid, category, size, used, status

        ))

    return data


def create_vdev_thin(cdp_server_ip, session_id, name, size, qty=1, pool_id=1):
    """Create virtual devices in a storagepool already created (Thin provision)"""

    headers = {'Content-Type': 'application/json'}
    URL = 'http://{}:/ipstor/batch/logicalresource/sanresource'.format(cdp_server_ip)
    data = json.dumps({
        "category": "virtual",
        "batchvirtualdevicenumber": qty,
        "name": name,
        "sizemb": 1024,
        "thinprovisioning": {
            "fullsizemb": size,
            "enabled": False
        },
        "storagepoolid": pool_id
    })
    r = requests.post(URL, cookies={'session_id': session_id}, data=data, headers=headers)

    return r


def create_vdev_thick(cdp_server_ip, session_id, name, size, qty=1, pool_id=1):
    """Create virtual devices in a storagepool already created (Thick provision)"""

    headers = {'Content-Type': 'application/json'}
    URL = 'http://{}:/ipstor/batch/logicalresource/sanresource'.format(cdp_server_ip)
    data = json.dumps({
        "category": "virtual",
        "batchvirtualdevicenumber": qty,
        "name": name,
        "sizemb": size,
        "storagepoolid": pool_id
    })

    r = requests.post(URL, cookies={'session_id': session_id}, data=data, headers=headers)

    return r


def rescan_adapters(cdp_server_ip, session_id):
    """Rescan physical resources to refresh the list of devices. SCSI Inquiry String \
        commands are sent to physical adapter ports to get the list of devices"""

    headers = {'Content-Type': 'application/json'}
    URL = 'http://{}:/ipstor/physicalresource/physicaldevice/rescan'.format(cdp_server_ip)
    data = json.dumps({
        "existing": False,
        "scanonlynew": False,
        "reportluns": True,
        "autodetect": True,
        "readfrominactive": True
    })
    r = requests.put(URL, cookies={'session_id': session_id}, data=data, headers=headers)

    return r
