# OffLyne
Offline server for Ylands to play locally or if servers are dead.

WARNING: only use on an account or copy of the game you're not planning on reconnecting to official servers again.

# Setup
Note: This is temporary VM setup during development; planning to change to a docker container for easier deployment.

## Setup VM Server

### Download
* [Ubuntu Server ISO](https://ubuntu.com/download/server)
* [VirtualBox](https://www.virtualbox.org/wiki/Downloads) (or similar VM manager)

### Create VM
* Use ISO and VM manager to create VM
* Install Ubuntu Server minimum (ensure SSH and Python3 is included)
* Shutdown VM
* Add host-only or equivalent network adapter (will configure later)
* NAT adapter add port forwarding host 2222 and guest 22 for SSH access from Host
  * Optional: create id_rsa keys, add public to authorized_hosts
* Start up the VM

### Install Prereqs on VM
* Nice to have (optional)
  * `sudo apt install less vim bash-completion net-tools inetutils-ping`
    * Note: for __bash-completion__ make sure `~/.bashrc` has the following and re-source to apply `source ~/.bashrc`
```
# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi
```
* Install GIT
  * `sudo apt install git`
* Install PIP for python
  * `sudo apt install python3-pip`
* [Apache](https://httpd.apache.org/)
  * Recommend following [this](https://ubuntu.com/tutorials/install-and-configure-apache#1-overview)
  * `sudo apt install apache2 apache2-dev`
* [mod_wsgi](https://modwsgi.readthedocs.io/en/master/index.html)
  * `pip install mod_wsgi`
* [Django]()
  * `pip install django`

### Configure VM Interfaces
* NAT
  * Confirm `/etc/netplan/00-installer-config.yaml` is:
```
# This is the network config written by 'subiquity'
network:
  ethernets:
    enp0s3:
      dhcp4: true
  version: 2
```
* Host-Only
  * In VM manager, check host-only adapters and pick out a valid IP from DHCP range (ex: 192.168.56.101)
    * This will be used in `01-host-config.yaml` below
  * On VM get the host-only, second, adapter interface name
    * `ip addr show`
    * Find `enp0s#` which either has no address or one within the DHCP range of the host-only adapter.
      * This will be used in `01-host-config.yaml` below
  * Create `/etc/netplan/01-host-config.yaml`, replace __enp0s8__ and __192.168.56.101/24__ as needed:
```
network:
  ethernets:
    enp0s8:
      addresses:
        - 192.168.56.101/24
```
* Apply Changes
  * `sudo netplan apply`
  * Confirm
    * `ip addr show`

### Add OffLyne
* Clone main branch from OffLyne
  * Note: if adding to `/home/*/` then make sure to `chmod +x -R /home/<user>`
* Update __ALLOWED_HOSTS__ in `offlyne/settings.py`
  * Add second interface, host-only, IP address or anything else as needed

### Configure Apache Site
* Add following to `/etc/apache2/apache2.conf`
  * Get **wsgi_module** location with `mod_wsgi-express module-location`
```
LoadModule wsgi_module /usr/lib/apache2/modules/mod_wsgi-py310.cpython-310-x86_64-linux-gnu.so
```
* Edit `/etc/apache2/sites-enabled/000-default.conf`
  * Replace `<offlyne_root>` with wherever you cloned OffLyne to
  * Replace `<wherever_django_is_installed>` with django's location
    * Check with and grab location up to and including __site-packages__:
```
$ python3
> import django
> django.__file__
```

```
<VirtualHost *:80>
        ServerName OffLyne

        ServerAdmin webmaster@localhost

        Alias /static/ <offlyne_root>/offlyne/static/

        WSGIScriptAlias / <offlyne_root>/offlyne/wsgi.py
        WSGIDaemonProcess offlyne python-path=<offlyne_root>:<wherever_django_is_installed>
        WSGIProcessGroup offlyne
        #WSGIPythonPath <offlyne_root>

        <Directory <offlyne_root>offlyne/static>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
        # Order deny,allow
        # Allow from all
        </Directory>

        <Directory <offlyne_root>/offlyne>
        <Files wsgi.py>
        Require all granted
        </Files>
        </Directory>

        LogLevel debug
        ErrorLog ${APACHE_LOG_DIR}/offlyne_error.log
        CustomLog ${APACHE_LOG_DIR}/offlyne_access.log combined
</VirtualHost>
```
