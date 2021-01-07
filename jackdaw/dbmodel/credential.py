from . import Basemodel, lf
import datetime
import hashlib
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Index, DateTime
from jackdaw.dbmodel.utils.serializer import Serializer

try:
	from pypykatz.pypykatz import pypykatz
	from pypykatz.utils.crypto.winhash import LM, NT
except ImportError:
	print('[JACKDAW] pypykatz not installed! storing creds will not work')
# It may be tempting to use SIDs to link credentials with users in the domain
# However some credentials format don't give SIDs (impacket) others have SIDs 
# that only identify the primary user, but not the owner of the actual credential
# Summary: we need to use the ad_id and the username<->samaccountname
#

class Credential(Basemodel, Serializer):
	__tablename__ = 'credentials'
	__table_args__ = (Index('Credential_uc', "ad_id", "domain", "username","nt_hash", "lm_hash", "history_no", unique = True), )

	id = Column(Integer, primary_key=True)
	ad_id = Column(Integer)
	machine_sid = Column(String, index=True)
	domain = Column(String, index=True, nullable= False)
	username = Column(String, index=True, nullable= False)
	nt_hash = Column(String, index=True, nullable= False)
	lm_hash = Column(String, index=True, nullable= False)
	krb_des_cbc = Column(String, index=True, nullable= True)
	krb_aes128 = Column(String, index=True, nullable= True)
	krb_aes256 = Column(String, index=True, nullable= True)
	krb_rc4_hmac = Column(String, index=True, nullable= True)
	history_no = Column(Integer, index=True, nullable= False)
	cred_type = Column(String, index=True, nullable= False)
	object_sid = Column(String, index=True)
	object_rid = Column(String, index=True)
	pwd_last_set = Column(DateTime, index = True)
	
	def __init__(self, domain = None, username = None, nt_hash = None, lm_hash = None, history_no = None, ad_id = -1):
		self.domain = domain
		self.username = username
		self.nt_hash = nt_hash
		self.lm_hash = lm_hash
		self.history_no = history_no
		self.ad_id = ad_id

	@staticmethod
	def from_samsecret(samsecret, ad_id = -1, machine_sid = -1):
		cred = Credential()
		cred.ad_id = ad_id
		cred.machine_sid = machine_sid
		cred.domain = 'LOCAL'
		cred.username = samsecret.username
		cred.nt_hash = samsecret.nt_hash.hex() if samsecret.nt_hash is not None else None
		cred.lm_hash = samsecret.lm_hash.hex() if samsecret.lm_hash is not None else None
		cred.history_no = 0
		cred.rid = samsecret.rid
		cred.cred_type = 'pypykatz-registry-sam'

		return cred

	@staticmethod
	def get_rid_from_sid(sid):
		if sid is None or sid == 'None':
			return None
		t = str(sid)
		_, rid = t.rsplit('-',1)
		return rid

	@staticmethod
	def from_aiosmb_secret(secret, ad_id = -1):
		# returns a complex touple in the format of (currentcred, [nthist], [lmhist], [cleartextcred], [pwds])
		creds = []
		pwds = []
		
		cred = Credential()
		cred.ad_id = ad_id
		cred.domain = secret.domain
		cred.username = secret.username
		cred.nt_hash = secret.nt_hash.hex() if secret.nt_hash is not None else None
		cred.lm_hash = secret.lm_hash.hex() if secret.lm_hash is not None else None
		cred.cred_type = 'aiosmb-dcsync-ntlm'
		cred.pwd_last_set = secret.pwd_last_set
		cred.history_no = 0

		if secret.object_sid is not None:
			cred.object_sid = str(secret.object_sid)
			t = str(secret.object_sid)
			_, rid = t.rsplit('-',1)
			cred.rid = rid

		for ktype, key in secret.kerberos_keys:
			if str(ktype) == 'aes128-cts-hmac-sha1-96':
				cred.krb_aes128 = str(key)
			elif str(ktype) == 'aes256-cts-hmac-sha1-96':
				cred.krb_aes256 = str(key)
			elif str(ktype) == 'des-cbc-md5':
				cred.krb_des_cbc = str(key)
			elif str(ktype) == 'rc4_hmac':
				cred.krb_rc4_hmac = str(key)

		creds.append(cred) # this is the main one
		
		if secret.cleartext is not None:
			for pw in secret.cleartext:
				cred = Credential()
				cred.ad_id = ad_id
				cred.domain = secret.domain
				cred.username = secret.username
				
				cred.nt_hash = NT(str(pw)).hex()
				cred.lm_hash = None
				cred.history_no = 0
				cred.cred_type = 'aiosmb-dcsync-cleartext'

				creds.append(cred)
				pwds.append(str(pw))

		if secret.lm_history is not None:
			for i, lm in enumerate(secret.lm_history):
				cred = Credential()
				cred.ad_id = ad_id
				cred.domain = secret.domain
				cred.username = secret.username
				cred.lm_hash = lm.hex()
				cred.history_no = i + 1
				cred.cred_type = 'aiosmb-dcsync-ntlm-history'

				creds.append(cred)

		if secret.nt_history is not None:
			for i, nt in enumerate(secret.nt_history):
				cred = Credential()
				cred.ad_id = ad_id
				cred.domain = secret.domain
				cred.username = secret.username
				cred.nt_hash = nt.hex()
				cred.history_no = i + 1
				cred.cred_type = 'aiosmb-dcsync-ntlm-history'

				creds.append(cred)
		
		return creds, pwds


	@staticmethod
	def from_impacket_line(line, ad_id = -1):
		cred = Credential()
		userdomainhist, flags, lm_hash, nt_hash, *t = line.split(':')
		#parsing history
		m = userdomainhist.find('_history')
		history_no = 0
		if m != -1:
			history_no = int(userdomainhist.split('_history')[1]) + 1
			userdomainhist = userdomainhist.split('_history')[0]
		m = userdomainhist.find('\\')
		domain = '<LOCAL>'
		username = userdomainhist
		if m != -1:
			domain = userdomainhist.split('\\')[0]
			username = userdomainhist.split('\\')[1]
		cred.ad_id = ad_id
		cred.nt_hash = nt_hash
		cred.lm_hash = lm_hash
		cred.history_no = history_no
		cred.username = username
		cred.domain = domain
		cred.cred_type = 'dcsync'
		return cred

	@staticmethod
	def from_impacket_stream(stream, ad_id = -1):
		for line in stream:
			yield Credential.from_impacket_line(line.decode(), ad_id = ad_id)

	@staticmethod
	def from_impacket_file(filename, ad_id = -1):
		"""
		Remember that this doesnt populate the foreign keys!!! You'll have to do it separately!
		important: historyno will start at 0. This means all history numbers in the file will be incremented by one
		"""
		with open(filename, 'r') as f:
			for line in f:
				yield Credential.from_impacket_line(line, ad_id = ad_id)

	@staticmethod
	def from_lsass_stream(stream, ad_id = -1):
		from pypykatz.pypykatz import pypykatz
		mimi = pypykatz.parse_minidump_buffer(stream)
		return Credential.lsass_generator(mimi, ad_id = ad_id)

	@staticmethod
	def from_lsass_dump(filename, ad_id = -1):
		
		mimi = pypykatz.parse_minidump_file(filename)
		return Credential.lsass_generator(mimi, ad_id = ad_id)

	@staticmethod
	def lsass_generator(mimi, ad_id):

		for luid in mimi.logon_sessions:
			sid = mimi.logon_sessions[luid].sid

			for cred in mimi.logon_sessions[luid].msv_creds:
				cr = Credential()
				cr.ad_id = ad_id
				cr.nt_hash = cred.NThash.hex() if cred.NThash is not None else '31d6cfe0d16ae931b73c59d7e0c089c0'
				cr.lm_hash = cred.LMHash if cred.LMHash is not None else 'aad3b435b51404eeaad3b435b51404ee'
				cr.history_no = 0
				cr.username = cred.username if cred.username is not None else 'NA'
				cr.domain = cred.domainname if cred.domainname is not None else '<LOCAL>'
				cr.cred_type = 'msv'
				yield cr, None, sid

			for cred in mimi.logon_sessions[luid].wdigest_creds:
				if cred.password is not None:
					cr = Credential()
					cr.ad_id = ad_id
					cr.nt_hash = NT(cred.password).hex()
					cr.lm_hash = None
					cr.history_no = 0
					cr.username = cred.username if cred.username is not None else 'NA'
					cr.domain = cred.domainname if cred.domainname is not None else '<LOCAL>'
					cr.cred_type = 'wdigest'
					yield cr, cred.password, sid

			for cred in mimi.logon_sessions[luid].ssp_creds:
				if cred.password is not None:
					cr = Credential()
					cr.ad_id = ad_id
					cr.nt_hash = NT(cred.password).hex()
					cr.lm_hash = None
					cr.history_no = 0
					cr.username = cred.username if cred.username is not None else 'NA'
					cr.domain = cred.domainname if cred.domainname is not None else '<LOCAL>'
					cr.cred_type = 'ssp'
					yield cr, cred.password, sid

			for cred in mimi.logon_sessions[luid].livessp_creds:
				if cred.password is not None:
					cr = Credential()
					cr.ad_id = ad_id
					cr.nt_hash = NT(cred.password).hex()
					cr.lm_hash = None
					cr.history_no = 0
					cr.username = cred.username if cred.username is not None else 'NA'
					cr.domain = cred.domainname if cred.domainname is not None else '<LOCAL>'
					cr.cred_type = 'live_ssp'
					yield cr, cred.password, sid

			#for cred in mimi.logon_sessions[luid]['dpapi_creds']:
			# dpapi credentials are not used in this database (for now)

			for cred in mimi.logon_sessions[luid].kerberos_creds:
				if cred.password is not None:
					cr = Credential()
					cr.ad_id = ad_id
					cr.nt_hash = NT(cred.password).hex()
					cr.lm_hash = None
					cr.history_no = 0
					cr.username = cred.username if cred.username is not None else 'NA'
					cr.domain = cred.domainname if cred.domainname is not None else '<LOCAL>'
					cr.cred_type = 'kerberos'
					yield cr, cred.password, sid

			for cred in mimi.logon_sessions[luid].credman_creds:
				if cred.password is not None:
					cr = Credential()
					cr.ad_id = ad_id
					cr.nt_hash = NT(cred.password).hex()
					cr.lm_hash = None
					cr.history_no = 0
					cr.username = cred.username if cred.username is not None else 'NA'
					cr.domain = cred.domainname if cred.domainname is not None else '<LOCAL>'
					cr.cred_type = 'credman'
					yield cr, cred.password, sid

			for cred in mimi.logon_sessions[luid].tspkg_creds:
				if cred.password is not None:
					cr = Credential()
					cr.ad_id = ad_id
					cr.nt_hash = NT(cred.password).hex()
					cr.lm_hash = None
					cr.history_no = 0
					cr.username = cred.username if cred.username is not None else 'NA'
					cr.domain = cred.domainname if cred.domainname is not None else '<LOCAL>'
					cr.cred_type = 'tpskg'
					yield cr, cred.password, sid

				
	@staticmethod
	def from_aiosmb_stream(stream, ad_id = -1):
		for line in stream:
			if line is None or len(line) == 0:
				continue
			yield Credential.from_aiosmb_line(line.decode(), ad_id = ad_id)

	@staticmethod
	def from_aiosmb_file(filename, ad_id = -1):
		"""
		Remember that this doesnt populate the foreign keys!!! You'll have to do it separately!
		important: historyno will start at 0. This means all history numbers in the file will be incremented by one
		"""
		with open(filename, 'r') as f:
			for line in f:
				if line is None or len(line) == 0:
					continue
				yield Credential.from_aiosmb_line(line, ad_id = ad_id)


	@staticmethod
	def from_aiosmb_line(line, ad_id = -1):
		cred = Credential()
		line = line.strip()
		if line.find(':') == -1:
			return None, None
		data = line.split(':')
		pw = None
		if data[0] == 'ntlm':
			cred.ad_id = ad_id
			uac = data[3]
			cred.domain = data[1]
			cred.username = data[2]
			cred.nt_hash = data[6]
			cred.lm_hash = data[5]
			cred.object_sid = data[4]
			cred.object_rid = Credential.get_rid_from_sid(data[4])
			cred.history_no = 0
			cred.cred_type = 'aiosmb-dcsync-ntlm'
		
		elif data[0] == 'ntlm_history':
			cred.ad_id = ad_id
			cred.domain = data[1]
			cred.username = data[2]
			cred.nt_hash = data[6]
			cred.lm_hash = data[5]
			cred.object_sid = data[4]
			cred.object_rid = Credential.get_rid_from_sid(data[4])
			cred.history_no = int(data[7].replace('history_',''))
			cred.cred_type = 'aiosmb-dcsync-ntlm-history'

		elif data[0] == 'cleartext':
			cred.ad_id = ad_id
			_, cred.domain, cred.username, cred.object_sid, pw = line.split(':', 4) #reparsing needed, pw might contain colon
			
			cred.object_rid = Credential.get_rid_from_sid(cred.object_sid)
			cred.nt_hash = NT(pw).hex()
			cred.lm_hash = None
			cred.history_no = 0
			cred.cred_type = 'aiosmb-dcsync-cleartext'

		return cred, pw