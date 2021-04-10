# munin-node-sim

A Python script simulating munin-node, which can be called through SSH directly using the below instructions.

It is targeted towards TrueNAS Core / FreeNAS, but may be used on other system that don't allow installation of munin-node (like ESXi). The goal is to be persistent over reboots.

Requirements are SSH and Python.

## Setup for TrueNAS Core (FreeNAS)
In the TrueNAS Core (FreeNAS) GUI, perform following steps:
- Storage -> Pools -> add new dataset called "munin-data"
- Services -> SSH -> enable and start automatically
- Accounts -> Users -> Add
  - Username: munin
  - Password: 1neDifficultToGuessPasswordIsProvidedHere22
  - Home Directory: /mnt/mypool/munin-data
    - Note that this needs to be part of /mnt per the GUI - e.g. using /home/munin/ will not work.
    - Also, note that this needs to be set through the GUI. A "pw user mod -n munin -d /mnt/mypool/munin-data" will not persist reboots.

On the server running Munin Master, generate a new SSH key pair:

    root@MonServ:~# su - munin --shell=/bin/bash
    munin@MonServ:~$ ssh-keygen
    Generating public/private rsa key pair.
    Enter file in which to save the key (/var/lib/munin/.ssh/id_rsa):
    Enter passphrase (empty for no passphrase):
    Enter same passphrase again:
    Your identification has been saved in /var/lib/munin/.ssh/id_rsa.
    Your public key has been saved in /var/lib/munin/.ssh/id_rsa.pub.
    The key fingerprint is:
    (...)

Copy over the public id to the Munin Node (this will automatically create an .ssh/ directory with a file 'authorized_keys' containing the public SSH key of the Munin Master):

    munin@MonServ:~$ ssh-copy-id munin@10.0.0.2
    The authenticity of host '10.0.0.2 (10.0.0.2)' can't be established.
    ECDSA key fingerprint is 7d:39:e9:5f:25:71:cf:15:04:18:a8:8a:42:90:73:35.
    Are you sure you want to continue connecting (yes/no)? yes
    /usr/bin/ssh-copy-id: INFO: attempting to log in with the new key(s), to filter out any that are already installed
    /usr/bin/ssh-copy-id: INFO: 1 key(s) remain to be installed -- if you are prompted now it is to install the new keys
    munin@10.0.0.2's password:

	Number of key(s) added: 1

    Now try logging into the machine, with:   "ssh 'munin@10.0.0.2'"
    and check to make sure that only the key(s) you wanted were added.

	munin@MonServ:~$

As per the suggestion, login onto TrueNAS without a password (as a test) and insert a 'command' section to .ssh/authorized_keys, dictating which script should be started upon login and securing the login a bit more:

    command="./munin-node-sim.py",no-port-forwarding,no-x11-forwarding,no-agent-forwarding ssh-rsa AAAAB3NzaC1yc2EAAAA<snip> munin@MonServ

On the server running the Munin Node (TrueNAS in this case), place the munin-node-sim.py file in the /home/munin/ folder and ensure a plugins/ directory exists with some plugins.

Now test:

	munin@MonServ:~$ ssh munin@10.0.0.2
	# munin node at servername

	fetch load
	load.value 0.14

	.

	config load
	graph_title Load average
	graph_vlabel load
	load.label load
	graph_args --base 1000 -l 0
	graph_scale no
	graph_category system
	load.warning 10
	load.critical 120
	graph_info The load average of the machine describes how many processes are in the runqueue (scheduled to run "immediately").
	load.info Average load for the five minutes.

	.

	list
	ip_forwarding ip_host df ip_drops load

Proceed to the actual Munin configuration on the Munin Master. 
Add following section in /etc/munin/munin.conf:

	[TrueNAS-v1.mydomain.com]
        address ssh://munin@10.0.0.2
        use_node_name no

Now try to execute the Munin plugin manually as a test:

	root@MonServ:~# su - munin --shell=/bin/bash
	munin@MonServ:~$ /usr/share/munin/munin-update --debug --nofork --host TrueNAS-v1.mydomain.com
	→ should work and yield output as “FETCH from <service>”

## Plugins

Some example plugins are included (feel free to add more) but it should be possible to use any TrueNAS compatible plugin (e.g. `ip_host` from https://github.com/farrokhi/freebsd-munin-plugins); feel free to update the list with supported ones.

- `df`: Python script plugin that shows disk usage in % of the disk pools
- `load`: Shell script plugin that shows the 5 minute average

## License

MIT
