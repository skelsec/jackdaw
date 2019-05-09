from jackdaw.dbmodel import *

class PasswordReportTableEntry:
	def __init__(self):
		self.domain = None
		self.username = None
		self.hash_type = None
		self.pw_length = None
		self.pw_lower = None
		self.pw_upper = None
		self.pw_digit = None
		self.pw_special = None
		
		self.has_spn = None
		
		#self.milyen_regi_az_account = None
		#self.mikor_kell_jelszo_valtoztatni = None
		#self.
	
#mi a sinztje a leggyengebb hasznalt jelszavaknak
#mennyi ido volt feltorni
#mi a feltort jelszavak aranya a teljes DBre nezve
#milyen csoportban vannak az emberek
#mi a baseline -> a szakerto mit mond a jo jelszora (mitol jo a jelszo?) ezt a reportba
#mit csinaljanak hogy jo legyen
#mikor volt a krbtgt user jelszava lecserelve
#

#javitasi lehetoseg:
#1. osszes szervice user gms account legyen
#2. jelszotarolo alkalmazas, lehetoleg ne centralizalt!!!
#3. milyen a korenyzet? raknak-e ki jelszavakat postitre
#4. 
	
	
class PasswordsReport:
	def __init__(self, db_conn):
		self.db_conn = db_conn
		self.cracking_speed = None
		
	def generate(self, ad_id = None):
		"""
		If with_domain is True, you also must include ad_id to identify which AD to make the queries against!
		"""
		dbsession = get_session(self.db_conn)
		
		if not ad_id:
			qry = dbsession.query(Credential, HashEntry).outerjoin(HashEntry, Credential.nt_hash == HashEntry.nt_hash).filter(HashEntry.nt_hash != None).filter(Credential.history_no == 0)
			for cred, he in qry.all():
				print(cred.domain, cred.username, 'NT', he.pw_length, he.pw_lower, he.pw_upper, he.pw_digit, he.pw_special)
			
		else:
			qry = dbsession.query(Credential, HashEntry, JackDawADUser)\
							.filter(Credential.nt_hash == HashEntry.nt_hash)\
							.filter(Credential.username == JackDawADUser.sAMAccountName)\
							.filter(HashEntry.nt_hash != None)\
							.filter(Credential.history_no == 0)\
							.filter(JackDawADUser.ad_id == ad_id)
							
			for cred, he, aduser in qry.all():
				print(cred.domain, cred.username, 'NT', he.pw_length, he.pw_lower, he.pw_upper, he.pw_digit, he.pw_special, aduser.when_pw_expires)
			