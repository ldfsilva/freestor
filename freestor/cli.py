"""Command line interface."""
import argparse

from getpass import getpass

from freestor import FreeStor


def main():
    parser = argparse.ArgumentParser(
    prog='freestor',
    description='A python library to interact with FalconStor FreeStor REST API')

    parser.add_argument('--server', '-s', help='IPStor server ip address', required=True)
    parser.add_argument('--username', '-u', help='Username', required=True)
    parser.add_argument('--password', '-p', help='Password')

    parser.add_argument('--get-pdevs', action='store_true', help='Get all physical disk devices information')

    args = parser.parse_args()

    password = args.password or getpass("Provide %s's password: " % args.username)

    freestor = FreeStor(args.server, args.username, password)

    assert freestor.get_session_id()

    if args.get_pdevs:
        data = freestor.get_pdevs()
        print()
        print(data)
