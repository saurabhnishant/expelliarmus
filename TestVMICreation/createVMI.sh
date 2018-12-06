#!/bin/bash
# edit and run-command: see install notes, apparently necessary for bash to work
../../libguestfs-1.36.13/run virt-builder ubuntu-16.04 \
-o Image.qcow2 \
--size 4G \
--format qcow2 \
--root-password password:123 \
--edit '/etc/default/grub:s/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="console=tty0 console=ttyS0,115200n8"/' \
--run-command update-grub \
--install "dpkg-repack,fakeroot,dpkg-dev" \
--update \
--write /etc/default/locale:$"LANG=\"en_US.UTF-8\"" \
--append /etc/default/locale:$"LANGUAGE=\"en_US\"" \
--firstboot-command 'userdel -r builder && useradd -m -p "" builder ; chage -d 0 builder' 
