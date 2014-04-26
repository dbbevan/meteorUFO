meteorUFO
=========

###What is it?


A python library to Create, Replace, Delete, and otherwise manage Meteor Application Users
by connecting to the mongodb data base for the meteor app and manipulating the users "table"/collection.

Compatible with (and can recompute) Meteor cryptographic SRP tokens.

April 26, 2014 -- Initial Release.

###Installtion

Everything is in a single python file: meteorUFO.py

Click that "Download ZIP" button to the right, or use git clone, and then
copy meteorUFO.py to wherever you need it to go.  


###Help

Python help is included

Once you have the meteorUFO.py file in your directory, you can do this:

```
$ python (run python)
import meteorUFO
help(meteorUFO)
```

If the help is insufficient, read the source code.  There's not that much.

You don't need to understand the internal  SRP cryptographic functionality 
to create, delete, update, etc... Meteor users as this library will handle
those aspects for you.  In summary, the Meteor framework replaces user passwords
with a cryptographic SRP token, and uses that token to check passwords later so
that passwords are never sent back and forth in clear text. 

But this also makes it difficult to create/update users from outside the app.... until now. 
This python library is compatible with that same cryptography.


You will need to know your `MONGO_URL` for accessing the mongoDB associated
with the meteor application.  

###API

The current API should be considered experimental.  

```
help(meteorUFO)

Help on module meteorUFO:

NAME
    meteorUFO

FILE
    /home/paul/meteorUFO/meteorUFO.py

CLASSES
    MeteorUser
    UFO
    
    class MeteorUser
     |  class for manipulating individual Meteor User records
     |  
     |  Instances are local copies.  They may have been read off of a mongodb, or
     |  created locally with a email/password pair.
     |  
     |  Example 1:
     |  To create a NEW USER (one that does not yet exist in the mongodb), as "bob"
     |  bob = ufo.MeteorUser(email='bob@bobsemailaddress.com', password='MyPassw0rd2014')
     |  
     |  To send bob down to the meteor dev passwordless mongodb (db meteor) running locally on port 3001
     |  import meteorUFO
     |  ufo = meteorUFO.UFO()
     |  ufo.orbit('mongodb://localhost:3001/meteor')
     |  ufo.beamDown(bob)
     |  
     |  users returned with ufo.beamUp(email) will be created as instances of class MeteorUser
     |  
     |  Example 2: Change Susan's password
     |  import meteorUFO
     |  ufo = meteorUFO.UFO()
     |  ufo.orbit('mongodb://mongouser:mongopassword@betterknowyourmongoprovider.com/meteor')
     |  susan = ufo.beamUp('susan@susansemailaddress.com')
     |  if susan is not None:      
     |      susan.set_password('notanotherpassword')
     |      ufo.beamDown(susan, replace=True)
     |  
     |  
     |  Methods defined here:
     |  
     |  __init__(self, user=None, email=None, password=None)
     |      the constructor for MeteorUser expects either an old user or new user
     |      either call will initialize self.user
     |      
     |      old (pre-existing) users
     |         MeteorUser(user=userObject)
     |         
     |      new users
     |         MeteorUser(email='newuseremail@somwhere', password='secret')
     |         
     |         this call will calculate the cryptographic SRP verifier for the password
     |         that is needed internally in Meteor.  The actual password will not be saved,
     |         only the cryptographic verifier.
     |  
     |  get_email(self)
     |      returns email address for the user
     |  
     |  set_email(self, email)
     |      sets the email address, returns nothing
     |      
     |      Updates local copy of the user. Does not save to mongodb. 
     |      To save to the mongodb, use ufo.beamDown(user, replace=True)
     |  
     |  set_password(self, password)
     |      sets the password by creating a new salt
     |      and recalulating the cryptographic SRP password verifier used by meteor
     |      
     |      The actual password is not saved.
     |      
     |      Updates local copy of the user. Does not save to mongodb. 
     |      To save to the mongodb, use ufo.beamDown(user, replace=True)
     |  
     |  update(self, updates)
     |      updates (overrides) fields in the meteor user
     |      can be used to update custom fields
     |      This updates the local copy
     |      Updates local copy of the user. Does not save to mongodb. 
     |      To save to the mongodb, use ufo.beamDown(user, replace=True)
     |      
     |      
     |      example
     |         susan.update({'paidSubscriber': True, 'subscription-expires': 3718992949569})
     |         ufo.beamDown(susan, replace=True)
    
    class UFO
     |  UFO = (Manage) _U_sers _F_rom _O_utside (Meteor)
     |  To use the class, instantiate it
     |  import meteorUFO
     |  ufo =  meteorUFO.UFO()
     |  The constructor takes no parameters.
     |  
     |  You need to connect to a mongoDB with a mongodb URL 
     |  by calling:
     |  
     |  ufo.orbit('mongodb://.........')
     |  
     |  before calling other ufo methods!!!
     |  
     |  Methods defined here:
     |  
     |  __init__(self)
     |  
     |  beamDown(self, meteorUser, replace=False)
     |      create or replace meteorUser onto the current mongodb
     |      to confirm replacement, call with replace=True
     |      Without replace=True, will insert new unique user or throw error
     |  
     |  beamUp(self, email=None)
     |      find_one user from the meteor mongodb
     |      searches by email
     |      returns class MeteorUser defined herein
     |  
     |  nuke(self, email=None, meteorUser=None)
     |      delete user by email address or by meteorUser.user[_id] field
     |  
:     |  
     |      set mongodb URL to new url and initiate MongoDB connection
     |      
     |      ufo.orbit(...) must be called and the connection must be good for
     |      any of the other ufo methods to work.

FUNCTIONS (consider these as internal functions -- these are called internally in the classes above for you)

    meteorSecret()
        used internally to create salt and other (probably unique) random ids
        returns 43 char random base64 string 
        similar to RandomGenerator.prototype.secret in 
        meteor github source at 
        https://github.com/meteor/meteor/blob/devel/packages/random/random.js
    
    test()
        This test() routine will install a user with email "test@email.com" and
        password marvin on a local meteor installation on a nitrous.io box the author used
        during development.
        
        It will then pull the user record for test@email.com from the mongodb and display it
    
    verifier(username, password, salt, hash_alg=<built-in function openssl_sha256>, ng_type=0, n_hex=None, g_hex=None)
        Generate cryptographic SRP Verifier used in meteor's user srp field
        
        The verifier function here is a cut/paste/modify of 
        SRP algorithm code from Tom Cocagne's SRP python module code in file _pysrp.py
        github URL https://github.com/cocagne/pysrp/blob/master/srp/_pysrp.py
        Copyright Tom Cogane
        copied and modified by Paul Brewer under public MIT License permissions granted by Tom Cocagne 
        
        CHANGES by Dr Paul Brewer, Economic and Financial Technology Consulting LLC
        
        Meteor's SRP implementation does not match Tom's python implementation
        The issue is that the SHA256 hash function used in Meteor outputs a string of human readable ascii hexadecimal string that is then rehashed.  Tom's code has a hash H() which 
        modifies a standard hash (e.g. SHA256) to make a long out of the bytes  
        and so the 2nd hash inputs end up looking different as do the outputs even when the final python output
        is converted to a hex string.  To fix, the change is primarily to change the long_to_bytes function
        used to rehash back to a hex string so as obtained a match to the Meteor JS code. 
 
        Another issue is that MeteorJS's srp code take the salt as an input, whereas the python
        code provides a seed as output.  This was solved by adding a verification_token() 
        method that behaves as the JS srp code.
        
        Finally, because the application only needs to be able to generate verification tokens
        from python for use within the MeteorJS code, the remaining code from python srp to 
        implement the SRP check in python may or may not work after these changes.... 
        so it has been deleted out.

DATA
    NITROUS_DEV = 'mongodb://localhost:3001/meteor'

```




