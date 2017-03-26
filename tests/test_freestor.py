import unittest
import json
from os import getenv
from unittest.mock import patch
from freestor import *


def load_json(file_name):
    """Load a json file"""
    with open(file_name, 'r') as fp:
        data = fp.read()

    return json.loads(data)


class TestFreestor(unittest.TestCase):
    @patch('freestor.requests.post')
    def setUp(self, mock_get):
        expected_json = {'rc': 0, 'type': 'root',
                        'id': 'b5588eea-0354-46db-8934-5504204ad183'}
        mock_get.return_value.json.return_value = expected_json

        #Get environment variables for real test
        self.server = getenv('CDP_SERVER')
        self.username = getenv('CDP_USERNAME', 'root')
        self.password = getenv('CDP_PASSWORD', 'IPStor101')
        self.session_id = get_session_id(self.server, 
                                        self.username, 
                                        self.password)

    @patch('freestor.requests.post')
    def test_get_session_id_ok(self, mock_get):
        """
        A successful request must return a hash id 36 chars long.
        """

        #Expected json response
        expected_json = {'rc': 0, 'type': 'root',
                        'id': 'b5588eea-0354-46db-8934-5504204ad183'}
        mock_get.return_value.json.return_value = expected_json

        session_id = get_session_id(self.server, 
                                    self.username, 
                                    self.password)

        self.assertEqual(36, len(session_id))

    @patch('freestor.requests.get')
    def test_get_fc_adapters(self, mock_get):
        """
        A list of all fc adapters ID must be returned.
        """

        #Expected json response
        f_name = 'tests/fc_adapters.json'
        expected_json = load_json(f_name)
        mock_get.return_value.json.return_value = expected_json

        expected = [100, 101, 102, 103]
        hbas = get_fc_adapters(self.server, self.session_id)

        self.assertListEqual(expected, hbas)

    @patch('freestor.requests.get')
    def test_get_fc_detail_mode_initiator(self, mock_get):
        """
        When fc adapter is set to initiator mode, it has to 
        return a single wwpn information.
        """

        f_name = 'tests/fc_adapter_100_detail.json'
        expected_json = load_json(f_name)
        mock_get.return_value.json.return_value = expected_json

        expected = [['FC Adapter 100', 'QLogic', 'initiator', 'linkdown',
                    '21:00:00:e0:8b:94:30:05', 'initiator'],]
        adapter = get_fc_detail(self.server, self.session_id, 101)

        self.assertListEqual(expected, adapter)

    @patch('freestor.requests.get')
    def test_get_fc_detail_dual_mode(self, mock_get):
        """
        When fc adapter is set to dual mode, it has to 
        return a two wwpn information. One initiator and
        one for target.
        """ 

        f_name = 'tests/fc_adapter_101_detail.json'
        expected_json = load_json(f_name)
        mock_get.return_value.json.return_value = expected_json
 
        expected = [
            ['FC Adapter 101', 'QLogic', 'dual', 'linkdown',
            '21:01:00:e0:8b:b4:30:05', 'initiator'],
            ['FC Adapter 101', 'QLogic', 'dual', 'linkdown',
            '21:01:00:0d:77:b4:30:05', 'target']
        ]
        adapter = get_fc_detail(self.server, self.session_id, 101)
 
        self.assertListEqual(expected, adapter)

