# jackdaw
gather gather gather

![jackdaw_small](https://user-images.githubusercontent.com/19204702/57587578-6159b280-7507-11e9-8762-c5e9022e37bc.png)

# Example commands
### Enumeration
#### Full enumeration with integrated sspi
`jackdaw --sql sqlite:///test.db enum TEST/victim/sspi:@10.10.10.2`
#### LDAP-only enumeration with username and password
The passowrd is `Passw0rd!`  
`jackdaw --sql sqlite:///test.db ldap TEST/victim/pass:Passw0rd!@10.10.10.2`

### Plotting all paths to Domain Admins group
`jackdaw --sql sqlite:///test.db plot admins`


# Important
This project is in experimental phase! This means multiple things:
1. it may crash
2. the controls you are using might change in the future (most likely)
3. (worst part) The database design is not necessary suitable for future requests so it may change. There will be no effor to maintain backwards compatibility with experimental-phase DB structure!

# What is this?
Jackdaw is here to collect all information in your domain, store it in a SQL database and show you nice graphs on how your domain objects interact with each-other an how a potential attacker may exploit these interactions.
It also comes with a handy feature to help you in a password-cracking project by storing/looking up/reporting hashes/passowrds/users.

# Technical part
## Database backend
Jackdaw uses SQLAlchemy ORM module, which gives you the option to use any SQL DB backend you like. The tests are mainly done on SQLite for ovbious reasons. There will be no backend-specific commands used in this project that would limit you.

## Enumeration
Enumeration (gathering data) is done on multiple levels. 
1. The most important one is over LDAP over which Jackdaw gather information on User/Machine/OU/ACL/Group objects. This takes a while depending on the size of your domain. 
2. The second level is the gathering of local groups on each individual machine in the domain. This requires a connection to be made to all machines that might trigger/overflow some sensors you may have in your network.
3. The third level is the gathering of the active sessions on each individual machine. Just like the previous step this includes a lot of connections to be made.
