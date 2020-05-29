#!/bin/bash

/usr/sbin/useradd -m kamal.pinnapureddy
/usr/sbin/usermod -aG wheel kamal.pinnapureddy

mkdir -p /home/kamal.pinnapureddy/.ssh/
chmod 700 /home/kamal.pinnapureddy/.ssh/
sleep 1
chown kamal.pinnapureddy:kamal.pinnapureddy /home/kamal.pinnapureddy/.ssh/
sleep 1

echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDnHSDmVPj3yjqlSADgfxh4SeDhU95ezNyOUI2wVfsvjuKlHTdw9SfW4Xd11D+32Aka5iWn1L4CtNfOPDOC3QRKduWHGKQAUSfoWQLZKK/bAmXtfVQE5BGk2Q2O+piwse0e4xmQSlHcSli4Pwbawt0WYeJY0ko8cyneTl+Av4YwsY7Fz1iKCJ10rDj6E7M+OnEVPkUzcH0Zzhei9dA8Fpq6I1jmcvmnqMUzrw3lsIjAlP/Xa6ucrEHjXeB4Pdkm3yp5CPv3MCGxewgEJVJwRAZ07IiFDdtffJdqPlDKFwSo2PlNZq/ta02m/o8dfB5NjvfsVdIqPmbyKEhudqeFfMsn kamal.pinnapureddy@KPinnapureddymbp.local" > /home/kamal.pinnapureddy/.ssh/authorized_keys

chmod 600 /home/kamal.pinnapureddy/.ssh/authorized_keys
sleep 1
chown kamal.pinnapureddy:kamal.pinnapureddy /home/kamal.pinnapureddy/.ssh/authorized_keys
