import sys
import argparse
import logging
import subprocess
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s: %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

logger = logging.getLogger('borgdrone2')


def thaw(vms):
    for vm in vms:
        # Simply try to unfreeze everything here.
        # It doesn't hurt VMs that have no frozen filesystems.
        # check_call won't do us any good here, we can't do anything meaningful if unfreezing fails.
        # But we need to continue to the VMs that haven't been thawed yet,
        # so no filesystems is left frozen unnecessarily.
        logger.info(f'domfsthaw {vm}')
        subprocess.call(['virsh', 'domfsthaw', vm])


def freeze(vms):
    for vm in vms:
        logger.info(f'domfsfreeze {vm}')
        subprocess.check_call(['virsh', 'domfsfreeze', vm])


def zsnap(dataset_path, mode):
    if mode == 'present':
        logger.info(f'creating borgdrone2 snapshot from {dataset_path}')
        subprocess.check_call(['zfs', 'snapshot', f'{dataset_path}@borgdrone2'])
    if mode == 'absent':
        # FIXME: make the removal idempotent
        logger.info(f'destroying borgdrone2 snapshot of {dataset_path}')
        subprocess.check_call(['zfs', 'destroy', f'{dataset_path}@borgdrone2'])


def borg(src_paths, uri):
    backup_name = datetime.now().strftime('%Y-%m-%d_%H-%M')
    borg_command = ['borg', 'create', '--compression', 'zstd', f'{uri}::{backup_name}'] + src_paths
    logger.info(f'running {borg_command}')
    subprocess.check_call(borg_command)


def cli():
    parser = argparse.ArgumentParser(description='borgdrone2')
    parser.add_argument('--zfs-dataset', metavar='tank/dataset/w/images', type=str, required=True)
    parser.add_argument('--borg-uri', metavar='ssh://user@example.com/path/to/borgrepo', type=str, required=True)
    parser.add_argument('--vms', metavar='myvm1,yourvm2', type=str, required=True)
    cliargs = parser.parse_args()

    vms = cliargs.vms.split(',')
    # FIXME: if stdout is not associated with a TTY, output order can be messed up between logger and virsh's stderr
    logger.info(f'backing up VMs {vms}')

    try:
        try:
            freeze(vms)
            zsnap(cliargs.zfs_dataset, 'present')
        finally:
            thaw(vms)
        zfs_get_command = ['zfs', 'get', '-H', '-o', 'value', 'mountpoint', cliargs.zfs_dataset]
        zmountpoint = subprocess.run(zfs_get_command, check=True, capture_output=True).stdout.decode('utf-8').strip()
        src_paths = [f'{zmountpoint}/.zfs/snapshot/borgdrone2/{vm}.img' for vm in vms]
        # We don't care about the XML definitions of the VMs at the moment, save only VM images. quick and dirty.
        borg(src_paths, cliargs.borg_uri)
    finally:
        zsnap(cliargs.zfs_dataset, 'absent')


if __name__ == '__main__':
    cli()
