#!/usr/bin/python
import pymongo
import hashlib
import datetime
import binascii
import os
import copy
# use this setting for NITROUS.IO Meteor Developer Environment
NITROUS_DEV = r'mongodb://localhost:3001/meteor'
###
class MeteorUser:
  '''
  class for manipulating individual Meteor User records
  
  Instances are local copies.  They may have been read off of a mongodb, or
  created locally with a email/password pair.
  
  Example 1:
  To create a NEW USER (one that does not yet exist in the mongodb), as "bob"
  import meteorUFO
  bob = meteorUFO.MeteorUser(email='bob@bobsemailaddress.com', password='MyPassw0rd2014')
  
  To send bob down to the meteor dev passwordless mongodb (db meteor) running locally on port 3001
  import meteorUFO
  ufo = meteorUFO.UFO()
  ufo.orbit('mongodb://localhost:3001/meteor')
  ufo.beamDown(bob)
  
  users returned with ufo.beamUp(email) will be created as instances of class MeteorUser
  
  Example 2: Change Susan's password
  import meteorUFO
  ufo = meteorUFO.UFO()
  ufo.orbit('mongodb://mongouser:mongopassword@betterknowyourmongoprovider.com/meteor')
  susan = ufo.beamUp('susan@susansemailaddress.com')
  if susan is not None:      
      susan.set_password('notanotherpassword')
      ufo.beamDown(susan, replace=True)
  
  '''
  
  def __init__(self, email=None, password=None, user=None):
    ''' 
    the constructor for MeteorUser expects either an old user or new user
    either call will initialize self.user
    
    old (pre-existing) users
       MeteorUser(user=userObject)
       
    new users
       MeteorUser(email='newuseremail@somwhere', password='secret')
       
       this call will calculate the cryptographic SRP verifier for the password
       that is needed internally in Meteor.  The actual password will not be saved,
       only the cryptographic verifier.  
    '''    
    
    self.user = copy.deepcopy(user)
    if (email is not None) and (password is not None):
      dbid = meteorSecret()
      salt = meteorSecret()
      identity = meteorSecret()
      newuser = { 
            u'_id': dbid,
            u'services': {
                       u'password':{
                                    u'srp':{
                                            u'verifier':u'',
                                            u'salt': salt,
                                            u'identity': identity,
                                            }
                                    },
                        u'resume':{
                                    u'loginTokens': []
                                    }
                        },
            u'emails': [{u'address': email,
                         u'verified': False}
                        ],
            u'createdAt': datetime.datetime.utcnow()
            }
      newuser[u'services'][u'password'][u'srp'][u'verifier']=verifier(identity,password,salt)
      if self.user is None:
        self.user = newuser
      else:
        self.user.update(newuser)
  
  def get_email(self):
    ''' 
    returns email address for the user
    '''
    return self.user[u'emails'][0][u'address']
  
  def set_email(self, email):
    '''
    sets the email address, returns nothing
    
    Updates local copy of the user. Does not save to mongodb. 
    To save to the mongodb, use ufo.beamDown(user, replace=True)
    '''
    self.user[u'emails'][0][u'address'] = email
    
  def set_password(self, password):
    '''
    sets the password by creating a new salt
    and recalulating the cryptographic SRP password verifier used by meteor
    
    The actual password is not saved.
    
    Updates local copy of the user. Does not save to mongodb. 
    To save to the mongodb, use ufo.beamDown(user, replace=True)

    '''
    srp = self.user[u'services'][u'password'][u'srp']
    srp[u'salt'] = meteorSecret()
    srp[u'verifier']=verifier(srp[u'identity'],password,srp[u'salt'])
    
  def update(self, updates):
    '''
    updates (overrides) fields in the meteor user
    can be used to update custom fields
    This updates the local copy
    Updates local copy of the user. Does not save to mongodb. 
    To save to the mongodb, use ufo.beamDown(user, replace=True)

    
    example
       susan.update({'paidSubscriber': True, 'subscription-expires': 3718992949569})
       ufo.beamDown(susan, replace=True)
    '''   
    self.user.update(updates)

    
class UFO:
  '''
  UFO = (Manage) _U_sers _F_rom _O_utside (Meteor)
  To use the class, instantiate it
  import meteorUFO
  ufo =  meteorUFO.UFO()
  The constructor takes no parameters.
  
  You need to connect to a mongoDB with a mongodb URL 
  by calling:

  ufo.orbit('mongodb://.........')

  before calling other ufo methods!!!
  
  '''
  
  def __init__(self):
    self.mongourl = ''
    self.c = None
    
  def orbit(self, newurl):
    '''
    set mongodb URL to new url and initiate MongoDB connection
    
    ufo.orbit(...) must be called and the connection must be good for
    any of the other ufo methods to work.
    '''
    self.c = r''
    self.db = r''
    self.users = r'Not Connected'
    self.mongourl = newurl
    self.c = pymongo.MongoClient(newurl)
    self.db = self.c.get_default_database()
    self.users = self.db.users
    test = self.users.find_one({})
    
  def beamUp(self, email=None):
    '''
    find_one user from the meteor mongodb
    searches by email
    returns class MeteorUser defined herein
    '''
    user = self.users.find_one({"emails.address":email})
    if user is None:
      return None
    else:
      return MeteorUser(user=user)
  
  def beamDown(self, meteorUser, replace=False):
    '''
    create or replace meteorUser onto the current mongodb
    to confirm replacement, call with replace=True
    Without replace=True, will insert new unique user or throw error
    '''
    if replace:
      return self.users.save(meteorUser.user)
    else:
      return self.users.insert(meteorUser.user)

  def nuke(self, email=None, meteorUser=None):
    '''
    delete user by email address or by meteorUser.user[_id] field
    '''
    if email is not None:
      return self.users.remove({"emails.address":email}, {justOne: True})
    if meteorUser is not None:
      return self.users.remove({"_id":meteorUser.user['_id']}, {justOne: True})
  
def meteorSecret():
  '''
  used internally to create salt and other (probably unique) random ids
  returns 43 char random base64 string 
  similar to RandomGenerator.prototype.secret in 
  meteor github source at 
  https://github.com/meteor/meteor/blob/devel/packages/random/random.js
  '''
  secret = os.urandom(33).encode("base64")[:43]
  return secret

def verifier( username, password, salt, hash_alg=hashlib.sha256, ng_type=0, n_hex=None, g_hex=None ):
  '''
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
  '''
  
#  Paul Brewer  April 2014 drpaulbrewer@eaftc.com


# N    A large safe prime (N = 2q+1, where q is prime)
  #      All arithmetic is done modulo N.
  # g    A generator modulo N
  # k    Multiplier parameter (k = H(N, g) in SRP-6a, k = 3 for legacy SRP-6)
  # s    User's salt
  # I    Username
  # p    Cleartext Password
  # H()  One-way hash function
  # ^    (Modular) Exponentiation
  # u    Random scrambling parameter
  # a,b  Secret ephemeral values
  # A,B  Public ephemeral values
  # x    Private key (derived from p and s)
  # v    Password verifier

  _ng_const = (
# 1024-bit
('''\
EEAF0AB9ADB38DD69C33F80AFA8FC5E86072618775FF3C0B9EA2314C9C256576D674DF7496\
EA81D3383B4813D692C6E0E0D5D8E250B98BE48E495C1D6089DAD15DC7D7B46154D6B6CE8E\
F4AD69B15D4982559B297BCF1885C529F566660E57EC68EDBC3C05726CC02FD4CBF4976EAA\
9AFD5138FE8376435B9FC61D2FC0EB06E3''',
"2"),
# 2048
('''\
AC6BDB41324A9A9BF166DE5E1389582FAF72B6651987EE07FC3192943DB56050A37329CBB4\
A099ED8193E0757767A13DD52312AB4B03310DCD7F48A9DA04FD50E8083969EDB767B0CF60\
95179A163AB3661A05FBD5FAAAE82918A9962F0B93B855F97993EC975EEAA80D740ADBF4FF\
747359D041D5C33EA71D281E446B14773BCA97B43A23FB801676BD207A436C6481F1D2B907\
8717461A5B9D32E688F87748544523B524B0D57D5EA77A2775D2ECFA032CFBDBF52FB37861\
60279004E57AE6AF874E7303CE53299CCC041C7BC308D82A5698F3A8D0C38271AE35F8E9DB\
FBB694B5C803D89F7AE435DE236D525F54759B65E372FCD68EF20FA7111F9E4AFF73''',
"2"),
# 4096
('''\
FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E08\
8A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B\
302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9\
A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE6\
49286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8\
FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D\
670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C\
180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF695581718\
3995497CEA956AE515D2261898FA051015728E5A8AAAC42DAD33170D\
04507A33A85521ABDF1CBA64ECFB850458DBEF0A8AEA71575D060C7D\
B3970F85A6E1E4C7ABF5AE8CDB0933D71E8C94E04A25619DCEE3D226\
1AD2EE6BF12FFA06D98A0864D87602733EC86A64521F2B18177B200C\
BBE117577A615D6C770988C0BAD946E208E24FA074E5AB3143DB5BFC\
E0FD108E4B82D120A92108011A723C12A787E6D788719A10BDBA5B26\
99C327186AF4E23C1A946834B6150BDA2583E9CA2AD44CE8DBBBC2DB\
04DE8EF92E8EFC141FBECAA6287C59474E6BC05D99B2964FA090C3A2\
233BA186515BE7ED1F612970CEE2D7AFB81BDD762170481CD0069127\
D5B05AA993B4EA988D8FDDC186FFB7DC90A6C08F4DF435C934063199\
FFFFFFFFFFFFFFFF''',
"5"),
# 8192
('''\
FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E08\
8A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B\
302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9\
A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE6\
49286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8\
FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D\
670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C\
180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF695581718\
3995497CEA956AE515D2261898FA051015728E5A8AAAC42DAD33170D\
04507A33A85521ABDF1CBA64ECFB850458DBEF0A8AEA71575D060C7D\
B3970F85A6E1E4C7ABF5AE8CDB0933D71E8C94E04A25619DCEE3D226\
1AD2EE6BF12FFA06D98A0864D87602733EC86A64521F2B18177B200C\
BBE117577A615D6C770988C0BAD946E208E24FA074E5AB3143DB5BFC\
E0FD108E4B82D120A92108011A723C12A787E6D788719A10BDBA5B26\
99C327186AF4E23C1A946834B6150BDA2583E9CA2AD44CE8DBBBC2DB\
04DE8EF92E8EFC141FBECAA6287C59474E6BC05D99B2964FA090C3A2\
233BA186515BE7ED1F612970CEE2D7AFB81BDD762170481CD0069127\
D5B05AA993B4EA988D8FDDC186FFB7DC90A6C08F4DF435C934028492\
36C3FAB4D27C7026C1D4DCB2602646DEC9751E763DBA37BDF8FF9406\
AD9E530EE5DB382F413001AEB06A53ED9027D831179727B0865A8918\
DA3EDBEBCF9B14ED44CE6CBACED4BB1BDB7F1447E6CC254B33205151\
2BD7AF426FB8F401378CD2BF5983CA01C64B92ECF032EA15D1721D03\
F482D7CE6E74FEF6D55E702F46980C82B5A84031900B1C9E59E7C97F\
BEC7E8F323A97A7E36CC88BE0F1D45B7FF585AC54BD407B22B4154AA\
CC8F6D7EBF48E1D814CC5ED20F8037E0A79715EEF29BE32806A1D58B\
B7C5DA76F550AA3D8A1FBFF0EB19CCB1A313D55CDA56C9EC2EF29632\
387FE8D76E3C0468043E8F663F4860EE12BF2D5B0B7474D6E694F91E\
6DBE115974A3926F12FEE5E438777CB6A932DF8CD8BEC4D073B931BA\
3BC832B68D9DD300741FA7BF8AFC47ED2576F6936BA424663AAB639C\
5AE4F5683423B4742BF1C978238F16CBE39D652DE3FDB8BEFC848AD9\
22222E04A4037C0713EB57A81A23F0C73473FC646CEA306B4BCBC886\
2F8385DDFA9D4B7FA2C087E879683303ED5BDD3A062B3CF5B3A278A6\
6D2A13F83F44F82DDF310EE074AB6A364597E899A0255DC164F31CC5\
0846851DF9AB48195DED7EA1B1D510BD7EE74D73FAF36BC31ECFA268\
359046F4EB879F924009438B481C6CD7889A002ED5EE382BC9190DA6\
FC026E479558E4475677E9AA9E3050E2765694DFC81F56E880B96E71\
60C980DD98EDD3DFFFFFFFFFFFFFFFFF''',
'0x13')
)
  
  NG_CUSTOM = len(_ng_const)

  
  def get_ng( ng_type, n_hex, g_hex ):
      if ng_type < NG_CUSTOM:
          n_hex, g_hex = _ng_const[ ng_type ]
      return int(n_hex,16), int(g_hex,16)
                
  
  def bytes_to_long(s):
      n = ord(s[0])
      for b in ( ord(x) for x in s[1:] ):
          n = (n << 8) | b
      return n
  
      
  def long_to_bytes(n):
      l = list()
      x = 0
      off = 0
      while x != n:
          b = (n >> off) & 0xFF
          l.append( chr(b) )
          x = x | (b << off)
          off += 8
      l.reverse()
      return ''.join(l)
  
  def long_to_hex(n):
    return long_to_bytes(n).encode('hex')
      
  def get_random( nbytes ):
      return bytes_to_long( os.urandom( nbytes ) )
      
  def H( hash_class, *args, **kwargs ):
      h = hash_class()
      
      for s in args:
          if s is not None:
              h.update( long_to_hex(s) if isinstance(s, (long, int)) else s )
  
      return long( h.hexdigest(), 16 )
      
  def gen_x( hash_class, salt, username, password ):
      return H( hash_class, salt, H( hash_class, username + ':' + password ) )
      
  # main body of verifier() function
  hash_class = hash_alg
  N,g = get_ng( ng_type, n_hex, g_hex )
  _v = long_to_hex( pow(g,  gen_x( hash_class, salt, username, password ), N) ) 
  return _v
  
def test():
  '''  
  This test() routine will install a user with email "test@email.com" and
  password marvin on a local meteor installation on a nitrous.io box the author used
  during development.
  
  It will then pull the user record for test@email.com from the mongodb and display it
  '''
  ufo = UFO()
  ufo.orbit('mongodb://localhost:3001/meteor')
  u = MeteorUser(email=u'test@email.com',password=u'marvin')
  ufo.beamDown(u)
  print repr(ufo.beamUp(u'test@email.com').user)

