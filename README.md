# N2P


<p align="center"> 
  <img src="logo.png" alt="logo">
</p>


[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)


A basic P2P mesh network implemented in multi-threaded asynchronous python.

Each peer can broadcast a message. The message is received by other peers which have subscribed to it. Subscribing peers will also broadcast the message but retain the originals broadcaster's info. The peers will automatically detect and control message floods.

Also, peers can query other peers for a search. The first match will be returned to the peer which initiated the query. Other subsequent answers will be discarded.

## 	Running the Project

- You will need at least python 3.7 with async support.
- Setup a virtual-env and install the packages in `requirements.txt` using pip.
  - `virtualenv --python=python <venv-name>`
  - `. <venv-name>/bin/activate.sh`
  - `pip install -r requirements.txt`
- Go to `peer/` and run the script to bring up a peer.
  - `python peer.py  <ip-server>:<port-server>  <ip-ctrl>:<port-ctrl>`
  - The first argument is the address listening server's socket to let other peers connect.
  - The second argument is the address controlling server's socket to let users control the peer.
- Connect to the controlling server using a TCP client. You can use `netcat` command. Or `telnet`.
  - `nc <ip> <port>`
- List of all commands and their responses is listed in `api/`.

## Contribution
1. Fork the project.
2. Create a new branch with an appropriate name.
3. Commit the changes, Please use meaningful commit messages.([guide](https://github.com/RomuloOliveira/commit-messages-guide))
4. Create a merge request to one of the basic branches.
