from jackdaw.dbmodel import *
from sqlalchemy import func
import string
import os
import errno

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
	
	
class PasswordsReport:
	def __init__(self, db_conn, cracking_speed = 60 * 10**9, out_folder = None):
		self.db_conn = db_conn
		self.out_folder = out_folder
		self.cracking_speed = cracking_speed #default = 10x 1080TI #password/second

		self.cracked_users = []
		self.pw_reuse_stats = {}
		self.pw_reuse = {}


	def get_cracking_time(self, he):
		alphabet_size = 0

		if he.pw_lower is True:
			alphabet_size += len(string.ascii_lowercase)

		if he.pw_upper is True:
			alphabet_size += len(string.ascii_uppercase)

		if he.pw_digit is True:
			alphabet_size += 10

		if he.pw_special is True:
			alphabet_size += len(" !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ ") #from hashcat

		res = (alphabet_size**he.pw_length) // self.cracking_speed
		return res

		
	def generate(self, ad_id = -1):
		"""
		If with_domain is True, you also must include ad_id to identify which AD to make the queries against!
		"""
		dbsession = get_session(self.db_conn)
		pw_sharing_hash = {}
		pw_sharing_total = 0
		pw_sharing_cracked = 0
		pw_sharing_notcracked = 0

		if self.out_folder:
			try:
				os.makedirs(self.out_folder)
			except OSError as e:
				if e.errno != errno.EEXIST:
					raise

		
		if ad_id == -1:
			qry = dbsession.query(Credential, HashEntry).outerjoin(HashEntry, Credential.nt_hash == HashEntry.nt_hash).filter(HashEntry.nt_hash != None).filter(Credential.history_no == 0)
			if self.out_folder:
				with open(os.path.join(self.out_folder, 'cracked_users.tsv'), 'w', newline = '') as o:
					o.write('\t'.join(['domain', 'username', 'hashtype', 'pw_length', 'pw_lower', 'pw_upper', 'pw_digit', 'pw_special', 'crack_times_sec']) + '\r\n')
					for cred, he in qry.all():
						res = [str(cred.domain), str(cred.username), 'NT', str(he.pw_length), str(he.pw_lower), str(he.pw_upper), str(he.pw_digit), str(he.pw_special), str(self.get_cracking_time(he))]
						o.write('\t'.join(res) + '\r\n')
			
			else:
				for cred, he in qry.all():
					res = [cred.domain, cred.username, 'NT', he.pw_length, he.pw_lower, he.pw_upper, he.pw_digit, he.pw_special, self.get_cracking_time(he)]
					print(res)

			#PW SHARING
			occurrence_ctr = {}
			qry = dbsession.query(
					func.count(Credential.nt_hash),
						Credential.nt_hash
						).filter(Credential.history_no == 0
						).group_by(
							Credential.nt_hash
						).having(
							func.count(Credential.nt_hash) > 1
						)
			
			if self.out_folder:
				with open(os.path.join(self.out_folder, 'pw_reuse.tsv'), 'w', newline = '') as o:
					hdr = '%s\r\n' % ('\t'.join(['amount', 'users']))
					o.write(hdr)
					for occurrence, nthash in qry.all():
						pw_sharing_total += 1
						pw_sharing_hash[nthash] = 1
						users = []
						for user in dbsession.query(Credential.username).filter(Credential.history_no == 0).filter_by(nt_hash = nthash).distinct(Credential.username):
							users.append(user.username)
						res = '%s\t%s\r\n' % (len(users),'|'.join(users))
						o.write(res)

			else:
				for occurrence, nthash in qry.all():
					pw_sharing_total += 1
					pw_sharing_hash[nthash] = 1
					if occurrence not in occurrence_ctr:
						occurrence_ctr[occurrence] = 0
					occurrence_ctr[occurrence] += 1

					users = []
					for user in dbsession.query(Credential.username).filter(Credential.history_no == 0).filter_by(nt_hash = nthash).distinct(Credential.username):
						users.append(user.username)
					
					line = '%s %s'% (len(users),' '.join(users))
				
					print(line)


			for nthash in pw_sharing_hash:
				exists = dbsession.query(HashEntry.id).filter_by(nt_hash=nthash).scalar() is not None
				if exists is True:
					pw_sharing_cracked += 1
				else:
					pw_sharing_notcracked += 1

						#how many objects
			total_objects = dbsession.query(Credential).filter(Credential.history_no == 0).filter(Credential.history_no == 0).count()
			
			#how many users
			total_comps = dbsession.query(Credential).filter(Credential.username.endswith('$')).filter(Credential.history_no == 0).filter(Credential.history_no == 0).count()
			

			#how many users
			total_users = total_objects - total_comps
			

			#how many total cracked
			total_objects_cracked = dbsession.query(Credential, HashEntry).outerjoin(HashEntry, Credential.nt_hash == HashEntry.nt_hash).filter(HashEntry.nt_hash != None).filter(Credential.history_no == 0).count()
			

			#how many total cracked
			total_comps_cracked = dbsession.query(Credential, HashEntry).outerjoin(HashEntry, Credential.nt_hash == HashEntry.nt_hash).filter(Credential.username.endswith('$')).filter(HashEntry.nt_hash != None).filter(Credential.history_no == 0).count()
			

			#how many users
			total_users_cracked = total_objects_cracked - total_comps_cracked


			hdr = ['total_objects', 'total_comps', 'total_users', 'total_objects_cracked', 'total_comps_cracked', 'total_users_cracked', 'pw_sharing_total', 'pw_sharing_cracked', 'pw_sharing_notcracked']
			data = [total_objects, total_comps, total_users, total_objects_cracked, total_comps_cracked, total_users_cracked, pw_sharing_total, pw_sharing_cracked, pw_sharing_notcracked]
			data = [str(x) for x in data]
			if self.out_folder:
				with open(os.path.join(self.out_folder, 'overall_stats.tsv'), 'w', newline = '') as o:
					o.write('\t'.join(hdr) + '\r\n')
					o.write('\t'.join(data) + '\r\n')


			else:
				print(pw_sharing_total)
				print(pw_sharing_cracked)
				print(pw_sharing_notcracked)
				print(total_objects)
				print(total_comps)
				print(total_users)
				print(total_objects_cracked)
				print(total_comps_cracked)
				print(total_users_cracked)



			

		else:
			qry = dbsession.query(Credential, HashEntry, JackDawADUser)\
							.filter(Credential.nt_hash == HashEntry.nt_hash)\
							.filter(Credential.username == JackDawADUser.sAMAccountName)\
							.filter(HashEntry.nt_hash != None)\
							.filter(Credential.history_no == 0)\
							.filter(JackDawADUser.ad_id == ad_id)
							
			for cred, he, aduser in qry.all():
				print(cred.domain, cred.username, 'NT', he.pw_length, he.pw_lower, he.pw_upper, he.pw_digit, he.pw_special, aduser.when_pw_expires)

