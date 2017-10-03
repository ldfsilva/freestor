import unittest
import json
from unittest.mock import patch
from freestor import FreeStor


def load_json(file_name):
    """Load a json file"""
    with open(file_name, 'r') as fp:
        data = fp.read()

    return json.loads(data)


class TestFreestor(unittest.TestCase):

    @patch('freestor.FreeStor._post')
    def setUp(self, mock_post):
        expected_json = {'rc': 0, 'type': 'root',
                        'id': 'b5588eea-0354-46db-8934-5504204ad183'}

        mock_post.return_value._post.return_value = expected_json

        self.cdp = FreeStor('dagcdp01', 'root', 'abc')

    @patch('freestor.FreeStor._post')
    def test_get_session_id_ok(self, mock_post):
        """
        A successful request must return a hash id 36 chars long.
        """

        #Expected json response
        expected_json = {'rc': 0, 'type': 'root',
                        'id': 'b5588eea-0354-46db-8934-5504204ad183'}
        # mock_get.return_value.json.return_value = expected_json
        mock_post.return_value = expected_json

        session_id = self.cdp.get_session_id()

        self.assertEqual(36, len(session_id))

    @patch('freestor.FreeStor._get')
    def test_get_fc_adapters(self, mock_get):
        """
        A list of all fc adapters ID must be returned.
        """

        #Expected json response
        f_name = 'tests/fc_adapters.json'
        expected_json = load_json(f_name)

        mock_get.return_value = expected_json

        expected = [100, 101, 102, 103]
        hbas = self.cdp.get_fc_adapters()

        self.assertListEqual(expected, hbas)

    @patch('freestor.FreeStor._get')
    def test_get_fc_detail_mode_initiator(self, mock_get):
        """
        When fc adapter is set to initiator mode, it has to 
        return a single wwpn information.
        """

        f_name = 'tests/fc_adapter_100_detail.json'
        expected_json = load_json(f_name)

        mock_get.return_value = expected_json

        expected = [['FC Adapter 100', 'QLogic', 'initiator', 'linkdown',
                    '21:00:00:e0:8b:94:30:05', 'initiator'],]
        adapter = self.cdp.get_fc_detail(101)

        self.assertListEqual(expected, adapter)

    @patch('freestor.FreeStor._get')
    def test_get_fc_detail_dual_mode(self, mock_get):
        """
        When fc adapter is set to dual mode, it has to 
        return a two wwpn information. One initiator and
        one for target.
        """ 

        f_name = 'tests/fc_adapter_101_detail.json'
        expected_json = load_json(f_name)
        mock_get.return_value = expected_json

        expected = [
            ['FC Adapter 101', 'QLogic', 'dual', 'linkdown',
            '21:01:00:e0:8b:b4:30:05', 'initiator'],
            ['FC Adapter 101', 'QLogic', 'dual', 'linkdown',
            '21:01:00:0d:77:b4:30:05', 'target']
        ]
        adapter = self.cdp.get_fc_detail(101)

        self.assertListEqual(expected, adapter)

    @patch('freestor.FreeStor._get')
    def test_enumerate_licenses_ok(self, mock_get):
        """
        When successfull a list of registered licenses is returned.
        """

        expected = [
            {
                "key": "XXXXXXXXXXXXXXXXXXXXXXXXA",
                "registration": 0,
                "type": "Standard license for NSS, High Availability, HotZone, SafeCache, \
Service Enabled Disk, Zero-Impact Backup Enabler"
            },
            {
                "key": "XXXXXXXXXXXXXXXXXXXXXXXXB",
                "registration": 0,
                "type": "Standard license for NSS, Base (8 iSCSI ports, Unlimited Client \
Connections, 256 Snapshot, Email Alerts, Mirroring, Replication, iSCSI Boot, Multi-pathing), \
8 FC Ports, Unlimited TimeMarks and Snapshot Copy"
            },
            {
                "key": "XXXXXXXXXXXXXXXXXXXXXXXXC",
                "registration": 0,
                "type": "Standard license for NSS, 5 TB storage capacity"
            },
            {
                "key": "XXXXXXXXXXXXXXXXXXXXXXXXD",
                "registration": 0,
                "type": "Standard license for NSS, 5 TB storage capacity"
            },
            {
                "key": "XXXXXXXXXXXXXXXXXXXXXXXXE",
                "registration": 0,
                "type": "Standard license for NSS, 5 TB storage capacity"
            }
        ]

        mock_get.return_value = load_json('tests/licenses.json')
        licenses = self.cdp.enumerate_licenses()

        self.assertListEqual(expected, licenses)

    @patch('freestor.FreeStor._get')
    def test_get_license_detail_ok(self, mock_get):
        """
        When successfull a dictionary with additional data is returned for the given license key.
        """

        expected = {
            "asciikeycode": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "info": "BBBBBBBBBBBB"
        }

        mock_get.return_value = load_json('tests/license_detail.json')
        license_detail = self.cdp.get_license_detail('XXXXXXXXXXXXXXXXXXXXXXXXA')

        self.assertDictEqual(expected, license_detail)

    @patch('freestor.freestor.datetime')
    @patch('freestor.FreeStor.get_license_detail')
    @patch('freestor.FreeStor.enumerate_licenses')
    def test_get_licenses_ok(self, mock_enumerate, mock_license, mock_date):
        """
        When successfull a dictionary containing all registered licenses is returned.
        get_licenes perform a merge of enumerate_licenses and license_detail returning
        a list of dictionaries containing all information of registered licenses.
        """

        from datetime import datetime

        expected = [
            {'date': '20171003_16:23:59',
            "key": "XXXXXXXXXXXXXXXXXXXXXXXXA",
            "registration": 0,
            "type": "Standard license for NSS, High Availability, HotZone, SafeCache, \
Service Enabled Disk, Zero-Impact Backup Enabler",
            "asciikeycode": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "info": "BBBBBBBBBBBB"},
            {'date': '20171003_16:23:59',
            "key": "XXXXXXXXXXXXXXXXXXXXXXXXB",
            "registration": 0,
            "type": "Standard license for NSS, Base (8 iSCSI ports, Unlimited Client \
Connections, 256 Snapshot, Email Alerts, Mirroring, Replication, iSCSI Boot, \
Multi-pathing), 8 FC Ports, Unlimited TimeMarks and Snapshot Copy",
            "asciikeycode": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB",
            "info": "BBBBBBBBBBBB"}
        ]

        licenses = [
            {"key": "XXXXXXXXXXXXXXXXXXXXXXXXA",
            "registration": 0,
            "type": "Standard license for NSS, High Availability, HotZone, SafeCache, \
Service Enabled Disk, Zero-Impact Backup Enabler"},
            {"key": "XXXXXXXXXXXXXXXXXXXXXXXXB",
            "registration": 0,
            "type": "Standard license for NSS, Base (8 iSCSI ports, Unlimited Client \
Connections, 256 Snapshot, Email Alerts, Mirroring, Replication, iSCSI Boot, \
Multi-pathing), 8 FC Ports, Unlimited TimeMarks and Snapshot Copy"}
        ]

        # Detail information for two licenses to be used on side_effect. As there are
        # two licenses it will run get_license_detail two times. That's why side_effect
        # is being used.
        licenses_detail = [
            {"asciikeycode": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "info": "BBBBBBBBBBBB"},
            {"asciikeycode": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB",
            "info": "BBBBBBBBBBBB"}
        ]

        mock_date.now.return_value = datetime(2017, 10, 3, 16, 23, 59)
        mock_enumerate.return_value = licenses
        mock_license.side_effect = licenses_detail
        licenses = self.cdp.get_licenses()

        self.assertListEqual(expected, licenses)