Borgdrone2
===

This is a simple script used to backup VM images to a [Borg](https://github.com/borgbackup/borg) repository.
Guest filesystems are frozen, a zfs snapshot is taken, then we run `borg` using that snapshot.

When I say simple I mean it:
 - it assumes you're running libvirt and all VMs have the qemu-guest-agent up & running
 - it assumes all your VM images follow a "name.img" pattern and don't have multiple virtual disks.
 - it assumes your VMs are saved on a single ZFS dataset
 - it assumes you don't care about XML definition of the VM for your backup (as in `virsh dumpxml myvm`), just the disk images

I might add a feature to get the VM's XML later on.

## Usage

Should your target Borg repository need a passphrase, supply it via the environment as shown here.

```shell
export BORG_PASSPHRASE=supersecret
borgdrone2 --zfs-dataset vmstore/VMs --borg-uri ssh://user@cube.example.com/tank/myrepo --vms myvm1,othervm2
```
