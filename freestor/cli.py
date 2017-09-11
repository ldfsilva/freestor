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

    parser.add_argument('--physical-devices', action='store_true', help='List all physical disk devices information')

    args = parser.parse_args()

    password = args.password or getpass("Provide %s's password: " % args.username)

    freestor = FreeStor(args.server, args.username, password)

    assert freestor.get_session_id()

    if args.physical_devices:
        data = freestor.get_physical_devices()
        print()
        print(data)
