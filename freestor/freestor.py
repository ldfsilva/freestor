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
        self.headers = {'Content-Type': 'application/json'}
        self.session_id = self.get_session_id()

    def _url(self, path):
        return 'http://%s:/ipstor/%s' % (self.server, path)

    def _get(self, url):
        import sys

        try:
            r = requests.get(url, cookies={'session_id': self.session_id})
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(e)
            sys.exit(1)

        return r.json()

    def _post(self, url, data):
        import sys

        try:
            r = requests.post(url, headers=self.headers, data=data)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(e)
            sys.exit(1)

        return r.json()

    def get_session_id(self):
        """Get a session id to be used in later requests"""

        data = json.dumps(
            {'server': self.server, 'username': self.username, 'password': self.password}
        )

        URL = self._url('auth/login')
        r = self._post(URL, data)

        self.session_id = r.get('id')

        return self.session_id

    def get_fc_adapters(self):
        """
        Query the server and return a list of all fiber channel adapter IDs.

        For example:
        [100, 101, 102, 103]
        """

        URL = self._url('physicalresource/physicaladapter/')
        r = self._get(URL)

        #Get information about physical adapters
        data = r.get('data').get('physicaladapters')
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

        URL = self._url('physicalresource/physicaladapter/%s/' % fca)
        r = self._get(URL)

        #Replaces - (hyphen) wwpn separator for : (column)
        fix_wwpn = lambda wwpn: wwpn.replace('-', ':')

        #Get information about physical adapters
        data = r.get('data')
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

        URL = self._url('physicalresource/physicaladapter/fcwwpn')
        mode = 'initiator'
        adapters = []
        r = self._get(URL)
        data = r.get('data')
        for fc in data:
            adapter = fc.get('adapter')
            wwpn = fc.get('wwpn')

            # Get fiber channel port status (link up / link down)
            URL = self._url('physicalresource/physicaladapter/%s/' % adapter)
            r = self._get(URL)
            portstatus = r.get('data').get('portstatus')

            adapters.append(",".join([self.server, str(adapter), wwpn, mode, portstatus]))

        return adapters

    def get_target_fc_ports(self):
        """Retrieves the list of TARGET WWPNs of Fibre Channel target ports of all physical adapters"""

        URL = self._url('physicalresource/physicaladapter/fctgtwwpn')
        mode = 'target'
        adapters = []
        r = self._get(URL)
        data = r.get('data')
        for fc in data:
            adapter = fc.get('adapter')
            wwpn = fc.get('aliaswwpn')

            # Get fiber channel port status (link up / link down)
            URL = self._url('physicalresource/physicaladapter/%s/' % adapter)
            r = self._get(URL)
            portstatus = r.get('data').get('portstatus')

            adapters.append(",".join([self.server, str(adapter), wwpn, mode, portstatus]))

        return adapters

    def get_virtual_device(self):
        """Retrieve status information about all virtual devices and supporting devices."""
        
        URL = self._url('logicalresource/sanresource/')
        r = self._get(URL)
        
        # extract virtual device data out of the response
        return r.get('data').get('virtualdevices')
    
    def get_virtual_device_details(self, vdev):
        """Retrieves information about the specified virtualized device."""

        URL = self._url('logicalresource/sanresource/%s/' % vdev)
        r = self._get(URL)

        return r.get('data')

    def get_vdevs(self):
        """Gather all virtual devices information"""

        d = datetime.now()
        date = d.strftime("%Y%m%d_%X")

        data = []
        all_devices = self.get_virtual_device()
        for device in all_devices:
            guid = device.get('id')

            device_detail = self.get_virtual_device_details(guid)

            # Merge device and device_detail dictionaries in order to have a single
            # dictionary with all information for the given physical device.
            # There are 6 duplicate keys which contains same value and overlap on them,
            # they are: name, category, isforeign, size, used and status
            #
            # Also add date to enable historical comparison on outputed data
            #
            data.append({**{'date': date}, **device, **device_detail})

        return data

    def get_badwidth(self, server_t):
        """Test the network bandwidth with a replica server."""

        URL = self._url('logicalresource/replication')

        data = json.dumps({
            "action": "test",  
            "ipaddress": server_t
        })
        r = requests.put(URL, cookies={'session_id': self.session_id}, data=data, headers=self.headers)

        return r

    def get_incoming_replication_servers(self):
        """Get the list of source servers for incoming replication."""

        URL = self._url('logicalresource/replication/incoming/')
        r = self._get(URL)

        return r.get('data')

    def get_outgoing_replication_servers(self):
        """Get the list of replica servers for outgoing replication."""

        URL = self._url('logicalresource/replication/outgoing/')
        r = self._get(URL)

        return r.get('data')

    def get_incoming_replication_status(self, vdev):
        """Returns incoming replication status for a replica device."""

        URL = self._url('logicalresource/replication/incoming/%s/' % vdev)
        r = self._get(URL)

        return r. get('data')

    def get_replication_detail(self, vdev):
        """Returns replication information for a virtual device."""

        URL = self._url('logicalresource/replication/%s/' % vdev)
        r = self._get(URL)

        return r.get('data')

    def get_replication_status(self):
        """Returns incoming replication status for a replica device"""

        d = datetime.now()
        date = d.strftime("%Y%m%d_%X")

        outgoing_rep = self.get_outgoing_replication_servers()

        data = []
        # for device in incoming_rep[0].get('devices'):
        for device in outgoing_rep[0].get('devices'):

            device_detail = self.get_replication_detail(device)

            # Also add date to enable historical comparison on outputed data
            #
            device_detail.update({'date': date})

            data.append(device_detail)

        return data

    def get_physical_devices(self):
        """Get physical devices information"""

        URL = self._url('physicalresource/physicaldevice/')
        r = self._get(URL)
        # extract physical device data out of the response

        return r.get('data').get('physicaldevices')

    def get_physical_device_detail(self, guid):
        """Get additional detail of the given physical device"""

        URL = self._url('physicalresource/physicaldevice/%s/' % guid)
        r = self._get(URL)

        return r.get('data')

    def get_pdevs(self):
        """Gather all physical devices information"""

        d = datetime.now()
        date = d.strftime("%Y%m%d_%X")

        data = []
        all_devices = self.get_physical_devices()
        for device in all_devices:
            guid = device.get('id')

            device_detail = self.get_physical_device_detail(guid)

            # Merge device and device_detail dictionaries in order to have a single
            # dictionary with all information for the given physical device.
            # There are 6 duplicate keys which contains same value and overlap on them,
            # they are: name, category, isforeign, size, used and status
            #
            # Also add date to enable historical comparison on outputed data
            #
            data.append({**{'date': date}, **device, **device_detail})

        return data

    def enumerate_licenses(self):
        """Get license information"""

        URL = self._url('server/license/')
        r = self._get(URL)

        data = r.get('data').get('licenseinfo')

        return data

    def get_license_detail(self, key):
        """Get additional license details"""

        URL = self._url('server/license/%s/' % key)
        r = self._get(URL)

        return r.get('data')

    def get_licenses(self):
        """Gather all licenses information"""

        d = datetime.now()
        date = d.strftime("%Y%m%d_%X")

        data = []
        licenses = self.enumerate_licenses()
        for license in licenses:
            key = license.get('key')

            license_detail = self.get_license_detail(key)

            # Merge license and license_detail dictionaries in order to have
            # a single dictionary with all license information.
            #
            # Also add date to enable historical comparison on outputed data
            #
            data.append({**{'date': date}, **license, **license_detail})

        return data

    def create_vdev_thin(self, name, size, qty=1, pool_id=1):
        """Create virtual devices in a storagepool already created (Thin provision)"""

        URL = self._url('batch/logicalresource/sanresource')
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

        return self._post(URL, data)

    def create_vdev_thick(self, name, size, qty=1, pool_id=1):
        """Create virtual devices in a storagepool already created (Thick provision)"""

        URL = self._url('batch/logicalresource/sanresource')
        data = json.dumps({
            "category": "virtual",
            "batchvirtualdevicenumber": qty,
            "name": name,
            "sizemb": size,
            "storagepoolid": pool_id
        })

        return self._post(URL, data)

    def create_fc_sanclient(self, name, os_type, initiators_wwpn):
        """Create fiber channel SAN client"""

        URL = self._url('client/sanclient/')
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

        r = self._post(URL, data)

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

        URL = self._url('physicalresource/physicaldevice/rescan')
        data = json.dumps({
            "existing": False,
            "scanonlynew": False,
            "reportluns": True,
            "autodetect": True,
            "readfrominactive": True
        })
        r = requests.put(URL, cookies={'session_id': self.session_id}, data=data, headers=self.headers)

        return r