# jackdaw
gather gather gather
![jackdaw_card](https://user-images.githubusercontent.com/19204702/69013611-6306a600-0982-11ea-8c21-d9f1e6efb9bf.jpg)

# What is this?
Jackdaw is here to collect all information in your domain, store it in a SQL database and show you nice graphs on how your domain objects interact with each-other an how a potential attacker may exploit these interactions.
It also comes with a handy feature to help you in a password-cracking project by storing/looking up/reporting hashes/passowrds/users.

# Quick usage info
 - If not using automatic collection (eg. not on Windows) you will need to create an initial empty database via `dbinit`
 - First you need to perform `enum`. This can be done automatically on windows by double-clicking on the executable, or typing `jackdaw.exe auto`.
 - Second you will need to run `nest` to get the web interface. By default it is served under `http://127.0.0.1:5000/nest` there is a SWAGGER documented API under `http://127.0.0.1:5000/ui`.
 - Web interface, you will need to go to the domain view and click on `Generate graph cache` only once to get the edge information in a cache file. it might take a while but in the command line you will see a progress bar.
 - After graph cache is done, you can play with the graph on the `graph view` but don't forget to select the corrrect cache number on the top left.

# Performance tricts/tips
This section will be regurarly updated based on user feedback.
### Data gathering
No advice here, while some improvements can be done in code there is nothing that a generic can do.
### Graph data cache file generation
Graph data cache file generation must be done on each graph once (and only once) which can take a while using the default sqlalchemy tool.  
Performance and speed can be significantly (over 50x more speed and 20x less memory) if you use the sqlite backend AND put the "sqlite3" command line utility somewhere in the `PATH`. I'd recommend this to every user.
### Path calulcation and Graph data load
Now here comes the big tradeoff part. Early implementation of Jackdaw used the `networkx` module as the graph backend since it is completely written in Python. But this came at a really significant memory and speed cost. To have Jackdaw pure Python, this option still exists however using the `igraph` backend is now the default.  
Note: `igraph` is a C++ library with Python bindings. It has precompiled wheels for Windows and major linux distros but if you use Jackdaw on something else (embedded systems/mobile phones/web browsers) you will either need to switch back to `networkx` or suffer with the hours long compilation time.

# Example commands
### Automatic enumeration - windows only, with domain-joined user -
No need to pre-initialise the database, it will be done automatically.
Using the distributed binary you can just double-click on `jackdaw.exe`  
Using as a python script `jackdaw auto`

### DB init
`jackdaw --sql sqlite:///<full path here>/test.db dbinit`  
ON LINUX SYSTEMS `<full path here>` includes the firest `/` so you will have `////` four (4) dashes before the file name. Don't get freaked out.  

### Enumeration
#### Full enumeration with integrated sspi - windows only
`jackdaw --sql sqlite:///test.db enum 'ldap+sspi-ntlm://<domain>\<placeholder>@10.10.10.2' 'smb+sspi-ntlm://<domain>\<placeholder>@10.10.10.2'`
#### Full enumeration with username and password - platform independent
The passowrd is `Passw0rd!`  
`jackdaw --sql sqlite:///test.db enum 'ldap+ntlm-password://TEST\victim:Passw0rd!@10.10.10.2' 'smb+ntlm-password://TEST\victim:Passw0rd!@10.10.10.2'`
#### LDAP-only enumeration with username and password - platform independent
The passowrd is `Passw0rd!`  
`jackdaw --sql sqlite:///test.db ldap 'ldap+ntlm-password://TEST\victim:Passw0rd!@10.10.10.2'`

### Start interactive web interface to plot graph and access additional features

`jackdaw --sql sqlite:///<FULL PATH TO DB> nest`  

Open `http://127.0.0.1:5000/ui` for the API  

Please see the `Building the UI` section further down to learn how to build the UI. Once built:

Open `http://127.0.0.1:5000/nest` for the graph interface (shows the graph, but far from working)  

# Features
## Data acquisition 
#### via LDAP
LDAP enumeration phase acquires data on AD info, User, Machine, OU, Group objects which will be reprezented as a node in the graph, and as a separate table in the DB. Additionally all afforementioned objects' Security Descriptior will be parsed and the ACLs for the DACL added to the DB. This, together with the memebership information will be represented as edges in the garph. Additionally custom SQL queries can be performed on any of the afforementioned data types when needed.  

#### via SMB
SMB enumeration phase acquires data on shares, localgroups, sessions, NTLM data via connecting to each machine in the domain (which is acquired via LDAP)  

#### via Kerberos
Kerberos module does automatic kerberoasting and aspreproasting

#### via LSASS dumps (optional)  
The framework allows users to upload LSASS memory dumps to store credentials and extend the session information table. Both will be used as additional edges in the graph (shared password and session respectively). The framework also uses this information to create a password report on weak/shared/cracked credentials.  

#### via DCSYNC results (optional)
The framework allows users to upload impacket's DCSYNC files to store credentials. This be used as additional edges in the graph (shared password). The framework also uses this information to create a password report on weak/shared/cracked credentials.  

#### via manual upload (optional)
The framework allows manually extending the available DB in every aspect. Example: when user session information on a given computer is discovered (outside of the automatic enumeration) there is a possibility to manually upload these sessions, which will populate the DB and also the result graph

## Graph
The framework can generate a graph using the available information in the database and plot it via the web UI (nest). Furthermore the graph generation and path canculations can be invoked programmatically, either by using the web API (/ui endpoint) or the grph object's functions.  

## Anomlaies detection  
The framework can identify common AD misconfigurations without graph generation. Currently only via the web API.  

#### User
User anomalies detection involve detection of insecure UAC permissions and extensive user description values. This feature set is expected to grow in the future as new features will be implemented.

#### Machine
Machine anomalies detection involve detection of insecure UAC permissions, non-mandatory SMB singing, outdated OS version, out-of-domain machines. This feature set is expected to grow in the future as new features will be implemented.

## Password cracking
**The framework does not performing any cracking, only organizing the hashes and the cracking results**  
**currently main focus is on impacket and aiosmb's dcsync results !NT and LM hashes only!**  
Sample porcess is the following:  
1. Harvesting credentials as text file via impacket/aiosmb or as memory dumps of the LSASS process via whatever tool you see fit.
2. Upload the harvested credentials via the API
3. Poll uncracked hases via the API
4. Crack them (hashcat?)
5. Upload the results to the framework via the API
6. Generate a report on the cracked/uncracked users and password strength and password sharing
  
*note form author: This feature was implemented for both attackers and defenders. Personally I don't see much added value on either side, since at the point one obtained the NT hash of a user it's just as good as the password... Nonetheless, more and more companies are performing password strength excercises, and this feature would help them. As for attackers: it is just showing off at this point, but be my guest. Maybe scare management for extra points.*  


# Important
This project is in experimental phase! This means multiple things:
1. it may crash
2. the controls you are using might change in the future (most likely)
3. (worst part) The database design is not necessary suitable for future requests so it may change. There will be no effort to maintain backwards compatibility with experimental-phase DB structure!


# Technical part

## Database backend
Jackdaw uses SQLAlchemy ORM module, which gives you the option to use any SQL DB backend you like. The tests are mainly done on SQLite for ovbious reasons. There will be no backend-specific commands used in this project that would limit you.

## Building the UI
**THIS IS ONLY NEEDED IF YOU INSTALL VIA GIT AND/OR CHANGE SOMETHING IN THE UI CODE**  
The UI was written in React. Before first use/installation you have to build it. For this, you will need `nodejs` and `npm` installed. Then:

 1. Go to `jackdaw/nest/site/nui`
 2. Run `npm install`
 3. Run `npm run build`

Once done with the above, the UI is ready to play with.

# Kudos
"If I have seen further it is by standing on the shoulders of Giants."
#### For the original idea 
BloodHound team
#### For the ACL edge calculation
@dirkjanm (https://github.com/dirkjanm/)
#### For the awesome UI
Zsolt Imre (https://github.com/keymandll)
#### For the data collection parts
please see kudos section in [`aiosmb`](https://github.com/skelsec/aiosmb) and [`msldap`](https://github.com/skelsec/msldap) modules
#### In case I forgot to mention someone pls send a PR
