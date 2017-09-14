"""Command line interface."""
import sys
import csv
import json
import argparse

from getpass import getpass

from freestor import FreeStor


def f_csv(data):
    """Output data in CSV format"""

    # extract header from first object
    header = list(data[0].keys())
    # output data to standard output
    output = sys.stdout
    writer = csv.DictWriter(output, fieldnames=header)
    writer.writeheader()
    for device in data:
        writer.writerow(device)


def f_json(data):
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

    parser.add_argument('--json', help='Output data in JSON format, default is CSV.', action='store_const', dest='output', const=f_json, default=f_csv)

    args = parser.parse_args()

    output = args.output
    password = args.password or getpass("Provide %s's password: " % args.username)

    freestor = FreeStor(args.server, args.username, password)

    assert freestor.get_session_id()

    if args.get_pdevs:
        data = freestor.get_pdevs()
        print()
        output(data)