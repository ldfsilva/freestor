"""Command line interface."""
import sys
import csv
import json
import argparse

from getpass import getpass

from freestor import FreeStor


def f_csv(data, caller):
    """Output data in CSV format"""

    # output data to standard output
    output = sys.stdout

    # define header for each function, fields based on REST API documentation
    # fields will vary for each type of device
    if caller == 'vdevs':
        header = [
            'date','guid','id','name','serialnumber','status','type','category','sizemb','fullsizemb',
            'usedmb','thin','align4k','replicationenabled','replicationsourceserverip',
            'replicationsourcedeviceid','isassignedtoclients','clients','snapshotgroup','mirrorenabled',
            'mirrorsuspended','backupenabled','dedupeenabled','deduperatio','useracl','writecacheenabled',
            'snapshotenabled','snapshotid','snapshotmirrored','snapshotmirrorsuspended','timemarkenabled',
            'cacheenabled','cacheid','cachemirrored','cachemirrorsuspended','hotzoneenabled','hotzoneid',
            'hotzonemirrored','hotzonemirrorsuspended','cdpenabled','cdpid','cdpmirrored','cdpmirrorsuspended',
            'hasnearlinemirror','isnearlinemirror','nearlinesourceserverip','nearlinesourcedeviceid',
            'timeviewlinkid','preferrednode','pdev'
        ]
    elif caller == 'pdevs':
        header = [
            'date','id','acsl','wwid','name','size','used','status','category','product','vendor','inquirystring',
            'isforeign','owner','inpool','pool','queuedepth','firmware','geometry','scsiaddress','segments',
        ]
    elif caller == 'licenses':
        header = ['date', 'key', 'type', 'registration', 'asciikeycode', 'info']

    writer = csv.DictWriter(output, fieldnames=header)
    writer.writeheader()
    for device in data:
        writer = csv.DictWriter(output, fieldnames=header)
        writer.writerow(device)


def f_json(data, caller):
    """Output data in JSON format"""

    print(json.dumps(data, indent=4))


def main():
    parser = argparse.ArgumentParser(
    prog='freestor',
    description='A python library to interact with FalconStor FreeStor REST API')

    parser.add_argument('--server', '-s', help='IPStor server ip address', required=True)
    parser.add_argument('--username', '-u', help='Username', required=True)
    parser.add_argument('--password', '-p', help='Password')

    parser.add_argument('--get-pdevs', action='store_true', help='Get all physical disk devices information')
    parser.add_argument('--get-vdevs', action='store_true', help='Get all virtual disk devices information')
    parser.add_argument('--get-licenses', action='store_true', help='Get all licenses information')

    parser.add_argument('--json', help='Output data in JSON format, default is CSV.', action='store_const', dest='output', const=f_json, default=f_csv)

    args = parser.parse_args()

    output = args.output
    password = args.password or getpass("Provide %s's password: " % args.username)

    freestor = FreeStor(args.server, args.username, password)

    assert freestor.get_session_id()

    if args.get_pdevs:
        data = freestor.get_pdevs()
        output(data, 'pdevs')

    if args.get_vdevs:
        data = freestor.get_vdevs()
        output(data, 'vdevs')

    if args.get_licenses:
        data = freestor.get_licenses()
        output(data, 'licenses')