# Install Python Docker support

This document describes the steps for installing Python Docker support modules.  The Docker modules that get installed allow all the usual Docker commands to be used within a Python script.

*NOTE:* Installing the Python Docker support modules is optional. If you don't intend to use Python for scripting of Docker operations, then this section can be skipped. It is **not** necessary to install `pip` as a pre-requisite to installing ICP.  

*NOTE:* Python has a `docker` package and a `docker-py` package. The documentation gives the impression they are synonymous.  However, in comparing the effects of doing the install of `docker` vs `docker-py`, they do not appear to be equivalent. The installation of the `docker` package appears to include the `docker-py` package, but not vice versa. More investigation is needed.

In order to install the Python Docker support modules, `pip` needs to be installed.  (Pip is the Python package manager.) In order to install `pip`, the `python-setuptools` package needs to be installed.

- Install Python setup tools. (Python setuptools may already be installed.)
  ```
  yum -y install python-setuptools
  Loaded plugins: langpacks, product-id, search-disabled-repos, subscription-manager
  Package python-setuptools-0.9.8-4.el7.noarch already installed and latest version
  Nothing to do
  ```
- Install `pip`.
  ```
  easy_install pip
  Searching for pip
  Reading https://pypi.python.org/simple/pip/
  Best match: pip 9.0.1
  ...
  Adding pip 9.0.1 to easy-install.pth file
  Installing pip script to /usr/bin
  Installing pip2.7 script to /usr/bin
  Installing pip2 script to /usr/bin

  Installed /usr/lib/python2.7/site-packages/pip-9.0.1-py2.7.egg
  Processing dependencies for pip
  Finished processing dependencies for pip
  ```

- Install Python Docker support modules.

	```
  pip install docker
  ```

After the install of the Python Docker support modules you should see the following directories:
```
> ls -l /usr/lib/python2.7/site-packages/docker*
/usr/lib/python2.7/site-packages/docker:
api   auth.py   client.py   constants.py   errors.py   __init__.py   models      tls.py   transport  utils       version.pyc
auth  auth.pyc  client.pyc  constants.pyc  errors.pyc  __init__.pyc  ssladapter  tls.pyc  types      version.py

/usr/lib/python2.7/site-packages/docker-2.5.1.dist-info:
DESCRIPTION.rst  INSTALLER  METADATA  metadata.json  RECORD  top_level.txt  WHEEL

/usr/lib/python2.7/site-packages/docker_py-1.10.6.dist-info:
DESCRIPTION.rst  INSTALLER  METADATA  metadata.json  RECORD  top_level.txt  WHEEL

/usr/lib/python2.7/site-packages/dockerpycreds:
constants.py  constants.pyc  errors.py  errors.pyc  __init__.py  __init__.pyc  store.py  store.pyc  version.py  version.pyc

/usr/lib/python2.7/site-packages/docker_pycreds-0.2.1.dist-info:
DESCRIPTION.rst  INSTALLER  METADATA  metadata.json  RECORD  top_level.txt  WHEEL
```
## Things that can go wrong with the Python Docker support installation

- Pip needs access to the public Internet to get the modules.  Public access to the Internet may not be available in all contexts.  In such cases, you need to configure a private pip repo.
