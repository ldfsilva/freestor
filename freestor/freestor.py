import requests
import json

from datetime import datetime


def format_wwpn(wwpn, delimiter='-'):
    """Formats a WWPN with the given delimiter"""

    # a non formated WWPN has 16 characters
    if len(wwpn) == 16:
        wwpn = delimiter.join([ wwpn[idx-2:idx] for idx in range(2, 17,2)])

    return wwpn


class FreeStor:
    def __init__(self, server, username, password):
        self.server = server
        self.username = username
        self.password = password

        self.session_id = self.get_session_id()

    def get_session_id(self):
        """Get a session id to be used in later requests"""

        headers = {'Content-Type': 'application/json'}
        data = '{}"server": "{}", "username": "{}", "password": "{}"{}'.format(
            '{', self.server, self.username, self.password, '}'
        )

        URL = 'http://{}:/ipstor/auth/login'.format(self.server)
        r = requests.post(URL, headers=headers, data=data)
        r_json = r.json()

        status_code = r_json.get('rc')
        #If request is not successful it must through its return code
        if status_code != 0:
            exit(status_code)

        session_id = r_json.get('id')

        return session_id

    def get_fc_adapters(self):
        """
        Query the server and return a list of all fiber channel adapter IDs.

        For example:
        [100, 101, 102, 103]
        """

        URL = 'http://{}:/ipstor/physicalresource/physicaladapter/'.format(self.server)
        r = requests.get(URL, cookies={'session_id': self.session_id})
        r_json = r.json()

        status_code = r_json.get('rc')
        #If request is not successful it must through its return code
        if status_code != 0:
            exit(status_code)

        #Get information about physical adapters
        data = r_json.get('data').get('physicaladapters')
        #Iterate through each device and return only id for the fc ones
        hbas = [hba.get('id') for hba in data if hba.get('type') == 'fc']

        return hbas

    def get_fc_detail(self, fca):
        """
        Get detail for a given fiber channel adapter.

        If the adapter is set to to either initiator or target mode,
        it shall return a single result containing its relevant data.
        For example:

        [
            ['FC Adapter 100', 'QLogic', 'initiator',
            'linkdown', '21-00-00-e0-8b-94-30-05', 'initiator'],
        ]

        In case the adapter is set to dual mode it shall return
        two results, being one for the initiator wwpn and the other
        for the target one.
        For example:

        [
            ['FC Adapter 101', 'QLogic', 'dual',
            'linkdown', '21-01-00-e0-8b-b4-30-05', 'initiator'],
            ['FC Adapter 101', 'QLogic', 'dual',
            'linkdown', '21-01-00-0d-77-b4-30-05', 'target']
        ]
        """

        URL = 'http://{}:/ipstor/physicalresource/physicaladapter/{}/'.format(
                self.server, fca
        )
        r = requests.get(URL, cookies={'session_id': self.session_id})
        r_json = r.json()

        status_code = r_json.get('rc')
        #If request is not successful it must through its return code
        if status_code != 0:
            exit(status_code)

        #Replaces - (hyphen) wwpn separator for : (column)
        fix_wwpn = lambda wwpn: wwpn.replace('-', ':')

        #Get information about physical adapters
        data = r_json.get('data')
        mode = data.get('mode')
        name = data.get('name')
        vendor = data.get('vendor')
        portstatus = data.get('portstatus')
        wwpn = data.get('wwpn')
        wwpn = fix_wwpn(wwpn)

        #If fc adapter is set to dual mode we need to get the target wwpn
        if mode == "dual":
            aliaswwpn = data.get('aliaswwpn')[0].get('name')
            aliaswwpn = fix_wwpn(aliaswwpn)

            fc_detail = [
                [name, vendor, mode, portstatus, wwpn, 'initiator'],
                [name, vendor, mode, portstatus, aliaswwpn, 'target']
            ]
        #if fc adapter is not set to dual mode, mode value will be either
        #initiator or target that's why it's repeated on the list
        else:
            fc_detail = [
                [name, vendor, mode, portstatus, wwpn, mode],
            ]

        return fc_detail

    def get_fc_detail_all(self):
        """
        Get detail for all fiber channel adapters and dump it on a csv file.

        It uses get_fc_adapters in order to get a list of all fc adapters
        available on the server and then iterate through each one of them
        executing get_fc_detail in order to gather the required information.
        """

        #Prepare output file
        d = datetime.now()
        date = d.strftime("%Y%m%d_%H%M%S")
        f_name = 'fc_adapters_info_{}.csv'.format(date)
        header = ('server,adapter,vendor,fc mode,status,wwpn,wwpn mode\n')

        #Query server for adapter detail
        adapters = self.get_fc_adapters()
        adapters_detail = []
        for fca in adapters:
            fca_detail = self.get_fc_detail(fca)
            adapters_detail.append(fca_detail)

        with open(f_name, 'w') as fp:
            fp.write(header)
            for fc in adapters_detail:
                for line in fc:
                    fp.write(self.server + ',')
                    fp.write(','.join(line))
                    fp.write('\n')

        message = "Adapters detail saved at: {}".format(f_name)

        print(message)
        return 1

    def get_initiator_fc_ports(self):
        """Retrieves the list of INITIATOR WWPNs of Fibre Channel target ports of all physical adapters"""

        URL = 'http://{}:/ipstor/physicalresource/physicaladapter/fcwwpn'.format(self.server)
        mode = 'initiator'
        adapters = []
        r = requests.get(URL, cookies={'session_id': self.session_id})
        data = r.json().get('data')
        for fc in data:
            adapter = fc.get('adapter')
            wwpn = fc.get('wwpn')

            # Get fiber channel port status (link up / link down)
            URL = 'http://{}:/ipstor/physicalresource/physicaladapter/{}/'.format(self.server, adapter)
            r = requests.get(URL, cookies={'session_id': self.session_id})
            portstatus = r.json()['data'].get('portstatus')

            adapters.append(",".join([self.server, str(adapter), wwpn, mode, portstatus]))

        return adapters

    def get_target_fc_ports(self):
        """Retrieves the list of TARGET WWPNs of Fibre Channel target ports of all physical adapters"""

        URL = 'http://{}:/ipstor/physicalresource/physicaladapter/fctgtwwpn'.format(self.server)
        mode = 'target'
        adapters = []
        r = requests.get(URL, cookies={'session_id': self.session_id})
        data = r.json().get('data')
        for fc in data:
            adapter = fc.get('adapter')
            wwpn = fc.get('aliaswwpn')

            # Get fiber channel port status (link up / link down)
            URL = 'http://{}:/ipstor/physicalresource/physicaladapter/{}/'.format(self.server, adapter)
            r = requests.get(URL, cookies={'session_id': self.session_id})
            portstatus = r.json()['data'].get('portstatus')

            adapters.append(",".join([self.server, str(adapter), wwpn, mode, portstatus]))

        return adapters

    def get_virtual_device(self):
        """Retrieve status information about all virtual devices and supporting devices."""
        
        headers = {'Content-Type': 'application/json'}
        URL = 'http://{}:/ipstor/logicalresource/sanresource/'.format(self.server)
        r = requests.get(URL, cookies={'session_id': self.session_id}, headers=headers)
        
        return r
    
    def get_virtual_device_details(self, vdev):
        """Retrieves information about the specified virtualized device."""

        headers = {'Content-Type': 'application/json'}
        URL = 'http://{}:/ipstor/logicalresource/sanresource/{}'.format(self.server, vdev)

        r = requests.get(URL, cookies={'session_id': self.session_id})

        return r

    def get_badwidth(self, server_t):
        """Test the network bandwidth with a replica server."""

        headers = {'Content-Type': 'application/json'}
        URL = 'http://{}:/ipstor/logicalresource/replication'.format(self.server)

        data = json.dumps({
            "action": "test",  
            "ipaddress": server_t
        })
        r = requests.put(URL, cookies={'session_id': self.session_id}, data=data, headers=headers)

        return r

    def get_replication_status(self, vdev):
        """Returns incoming replication status for a replica device"""

        headers = {'Content-Type': 'application/json'}
        URL = 'http://{}:/ipstor/logicalresource/replication/incoming/{}'.format(self.server, vdev)

        r = requests.get(URL, cookies={'session_id': self.session_id})

        return r

    def get_physical_devices(self):
        """Get physical devices information for a given CDP server"""
        
        URL = 'http://{}:/ipstor/physicalresource/physicaldevice/'.format(self.server)
        d = datetime.now()
        date = d.strftime("%Y%m%d %X")
        data = ['date, server, cdp lun id, acsl, vendor, product, \
            lun name, wwid, category, lun size (bytes), total used (bytes), status']

        r = requests.get(URL, cookies={'session_id': self.session_id})
        devices = r.json()['data'].get('physicaldevices')

        for device in devices:
            id = device.get('id')
            acsl = device.get('acsl')
            r = requests.get(URL + id, cookies={'session_id': self.session_id})
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
                date, self.server, id, acsl, vendor, product, name, 
                wwid, category, size, used, status

            ))

        return data

    def create_vdev_thin(self, name, size, qty=1, pool_id=1):
        """Create virtual devices in a storagepool already created (Thin provision)"""

        headers = {'Content-Type': 'application/json'}
        URL = 'http://{}:/ipstor/batch/logicalresource/sanresource'.format(self.server)
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
        r = requests.post(URL, cookies={'session_id': self.session_id}, data=data, headers=headers)

        return r

    def create_vdev_thick(self, name, size, qty=1, pool_id=1):
        """Create virtual devices in a storagepool already created (Thick provision)"""

        headers = {'Content-Type': 'application/json'}
        URL = 'http://{}:/ipstor/batch/logicalresource/sanresource'.format(self.server)
        data = json.dumps({
            "category": "virtual",
            "batchvirtualdevicenumber": qty,
            "name": name,
            "sizemb": size,
            "storagepoolid": pool_id
        })

        r = requests.post(URL, cookies={'session_id': self.session_id}, data=data, headers=headers)

        return r

    def create_fc_sanclient(self, name, os_type, initiators_wwpn):
        """Create fiber channel SAN client"""

        headers = {'Content-Type': 'application/json'}
        URL = 'http://{}:/ipstor/client/sanclient/'.format(self.server)
        data = json.dumps({
            "name": name,
            "protocoltype": ['fc'],
            "ostype": os_type,
            "persistentreservation": True,
            "clustered": True,
            "fcpolicy": {
                "initiators": [initiators_wwpn,],
                "vsaenabled": False
            }
        })

        r = requests.post(URL, cookies={'session_id': self.session_id}, data=data, headers=headers)
        r_json = r.json()

        status_code = r_json.get('rc')

        return r

    def create_multiple_san_clients(self, san_clients, os_type='aix'):
        """Create multiple SAN clients


        Given a list containing multiple aliases names and wwpn information
        ["alias_name", "wwpn"]"""

        for san_client in san_clients:
            name = san_client[0]
            wwpn = format_wwpn(san_client[1])

            self.create_fc_sanclient(name, os_type, wwpn)

    def rescan_adapters(self):
        """Rescan physical resources to refresh the list of devices. SCSI Inquiry String \
            commands are sent to physical adapter ports to get the list of devices"""

        headers = {'Content-Type': 'application/json'}
        URL = 'http://{}:/ipstor/physicalresource/physicaldevice/rescan'.format(self.server)
        data = json.dumps({
            "existing": False,
            "scanonlynew": False,
            "reportluns": True,
            "autodetect": True,
            "readfrominactive": True
        })
        r = requests.put(URL, cookies={'session_id': self.session_id}, data=data, headers=headers)

        return r