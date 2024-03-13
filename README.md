# OffLyne
Offline server for Ylands to play locally or if servers are dead.

__WARNING__: only use on an account or copy of the game you're not planning on reconnecting to official servers again.

# Contents
* [Setup](#setup)
  * [Setup VM Server](#setup-vm-server)
    * [Download](#download)
    * [Create VM](#create-vm)
    * [Install Prereqs on VM](#install-prereqs-on-vm)
    * [Configure VM Interfaces](#configure-vm-interfaces)
  * [Add OffLyne](#add-offlyne)
  * [Allow Writing to Captures](#allow-writing-to-captures)
  * [Configure Apache Site](#configure-apache-site)
  * [Enabling HTTPS](#enabling-https)
* [Run](#run)
  * [Redirect for Windows](#redirect-for-windows)
* [Notes](#notes)

# Setup
Note: This is temporary VM setup during development; planning to change to a docker container for easier deployment.

## Setup VM Server

### Download
* [Ubuntu Server ISO](https://ubuntu.com/download/server)
* [VirtualBox](https://www.virtualbox.org/wiki/Downloads) (or similar VM manager)

### Create VM
* Use ISO and VM manager to create VM
* Install Ubuntu Server minimum (Check OpenSSH pre-install)
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
  * `sudo pip install mod_wsgi`
  * `sudo mod_wsgi-express install-module`
* [Django]()
  * `sudo pip install django`

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
    * Set `/etc/netplan/01-host-config.yaml` permissions with `sudo chmod 600 /etc/netplan/01-host-config.yaml`
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

## Add OffLyne
* Clone main branch from OffLyne
  * Note: if adding to a `/home` directory then make sure to `chmod +x -R /home/<user>`
* Update __ALLOWED_HOSTS__ in `offlyne/settings.py`
  * Add second interface, host-only, IP address or anything else as needed

## Allow Writing to Captures
```
cd OffLyne
mkdir captures
sudo chown -R www-data:www-data captures/
```

## Configure Apache Site
Note: must be root to modify these apache files
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

## Enabling HTTPS
* Create CSR keys
  * Input anything or use defaults, __Common Name__ must match __ServerName__
```
openssl genrsa -out site.key 2048
openssl req -new -x509 -key site.key -out site.pem -days 1095
sudo chown root:root site.key site.pem
sudo mv site.key /etc/ssl/private/
sudo mv site.pem /etc/ssl/certs/
sudo a2enmod ssl
```
* Edit `/etc/apache2/sites-enabled/000-default.conf`
  * Add to top
```
<VirtualHost *:80>
   ServerName api.bistudio.com
   Redirect permanent / https://api.bistudio.com/
</VirtualHost>
```
  * Change second VirtualHost to 443 and add
```
ServerName api.bistudio.com

SSLEngine on
SSLCertificateFile "/etc/ssl/certs/offlyne.pem"
SSLCertificateKeyFile "/etc/ssl/private/offlyne.key"
```


# Run
* sudo apachectl start
  * stop or restart allowed
* Logs at `less /var/log/apache2/offlyne_*.log`

## Redirect for Windows
* Open `C:\Windows\System32\drivers\etc\hosts` as admin in text editor
```
	192.168.56.101 api.bistudio.com
	192.168.56.101 ylands-api.bistudio.com
```

# Notes
* Yland WinApp logs: `C:\Users\<user>\AppData\Local\Packages\BohemiaInteractivea.s.Ylands_ezkh2j9f9meea\TempState`
* With HTTPS and redirect Ylands is cert aware and will throw `Curl error 7: Failed to connect to api.bistudio.com port 443 after 0 ms: Bad access`
  * Need to inspect/inject host key somehow or exploit curl usage...
