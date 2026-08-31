#!/usr/bin/env python3
"""Mint TEMPORARY SSH credentials for the Lightsail box.

    eval "$(./scripts/lightsail_access.py --export)"
    ./scripts/deploy_mention_bot.sh "$LIGHTSAIL_TARGET"

Why this exists rather than a private key sitting in a file somewhere: the GM
pasted a long-lived server key into a chat session, which puts it in a
transcript forever and makes it a thing that has to be remembered and rotated.
Lightsail will issue a key pair valid for a few minutes instead, so nothing
durable is ever written down. `lightsail:GetInstanceAccessDetails` is the whole
privilege needed, and the policy attached to `gm-assistant-ci` grants that plus
two read calls and nothing else - no create, no delete, no reboot, no snapshot.

The host keys come back from the same API call and are written to a known_hosts
file, so the connection is verified rather than blindly accepted. That is the
part `StrictHostKeyChecking=no` throws away, and it costs nothing to keep.
"""

from __future__ import annotations

import argparse
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'webapp'))

DEFAULT_INSTANCE = 'courtwright.org'


def _aws_kwargs() -> dict[str, str]:
    from configobj import ConfigObj

    secrets = Path(__file__).resolve().parent.parent / 'webapp' / 'development-secrets.ini'
    section = ConfigObj(str(secrets), encoding='utf-8').get('aws') or {}
    if not section.get('access_key_id'):
        raise SystemExit(f'no [aws] credentials in {secrets}')
    return {
        'aws_access_key_id': section['access_key_id'],
        'aws_secret_access_key': section['secret_access_key'],
        'region_name': section.get('region', 'us-east-1'),
    }


def access_details(instance: str) -> dict[str, Any]:
    import boto3

    client = boto3.client('lightsail', **_aws_kwargs())
    details: dict[str, Any] = client.get_instance_access_details(instanceName=instance)['accessDetails']
    return details


def write_credentials(details: dict[str, Any], out_dir: Path | None = None) -> tuple[Path, Path]:
    """Write the private key, its CERTIFICATE, and known_hosts.

    Lightsail's temporary access is certificate-based: the private key alone
    gets `Permission denied (publickey)`, because the box trusts the Lightsail
    CA rather than that key. OpenSSH picks the certificate up automatically when
    it sits beside the key as `<identity>-cert.pub`, which is why the name below
    is not arbitrary.
    """
    directory = out_dir or Path(tempfile.mkdtemp(prefix='lightsail-'))
    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, stat.S_IRWXU)

    key_path = directory / 'id_lightsail'
    key = details['privateKey']
    if not key.endswith('\n'):
        key += '\n'
    with open(os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w') as handle:
        handle.write(key)

    cert = details.get('certKey')
    if cert:
        # The name matters: OpenSSH looks for exactly <identity>-cert.pub.
        cert_path = directory / 'id_lightsail-cert.pub'
        if not cert.endswith('\n'):
            cert += '\n'
        cert_path.write_text(cert)

    # Verify the host rather than trusting whatever answers on port 22. The API
    # hands us the fingerprints, so there is no excuse for turning the check off.
    hosts_path = directory / 'known_hosts'
    ip = details['ipAddress']
    lines = [
        f'{ip} {entry["algorithm"]} {entry["publicKey"]}'
        for entry in details.get('hostKeys', [])
        if entry.get('algorithm') and entry.get('publicKey')
    ]
    hosts_path.write_text('\n'.join(lines) + ('\n' if lines else ''))
    return key_path, hosts_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instance', default=DEFAULT_INSTANCE)
    parser.add_argument(
        '--export',
        action='store_true',
        help='print shell assignments to eval, instead of a human summary',
    )
    args = parser.parse_args()

    details = access_details(args.instance)
    key_path, hosts_path = write_credentials(details)
    target = f'{details["username"]}@{details["ipAddress"]}'
    verified = hosts_path.read_text().strip() != ''

    if args.export:
        print(f'export LIGHTSAIL_TARGET={target}')
        print(f'export SSH_KEY={key_path}')
        print(f'export SSH_KNOWN_HOSTS={hosts_path}')
        return 0

    print(f'instance : {args.instance} ({details.get("protocol", "ssh")})')
    print(f'target   : {target}')
    print(f'key      : {key_path}  (temporary - Lightsail expires it in minutes)')
    cert_path = key_path.parent / 'id_lightsail-cert.pub'
    print(f'cert     : {cert_path}  ({"present" if cert_path.exists() else "MISSING"})')
    print(f'hostkeys : {hosts_path}  ({"verified" if verified else "NONE RETURNED"})')
    print()
    print('  ssh -i {} -o UserKnownHostsFile={} {}'.format(key_path, hosts_path, target))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
