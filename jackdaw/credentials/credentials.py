
from jackdaw.dbmodel import create_db, get_session, Credential, HashEntry, ADUser
from sqlalchemy import exc, func
from jackdaw import logger
import string

class JackDawCredentials:
	def __init__(self, db_conn, domain_id = -1, db_session = None, cracking_speed = 60 * 10**9):
		self.domain_id = domain_id
		self.db_conn = db_conn
		self.dbsession = db_session

		self.cracking_speed = cracking_speed #default = 10x 1080TI #password/second

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

	def get_dbsession(self):
		if not self.dbsession:
			self.dbsession = get_session(self.db_conn)

	def add_credentials_impacket(self, impacket_file):
		self.get_dbsession()
		ctr = 0
		ctr_fail = 0
		try:
			for cred in Credential.from_impacket_file(impacket_file, self.domain_id):
				try:
					self.dbsession.add(cred)
					if ctr % 10000 == 0:
						logger.info(ctr)
						self.dbsession.commit()
					
				except exc.IntegrityError as e:
					ctr_fail += 1
					self.dbsession.rollback()
					continue
				else:
					ctr += 1

			self.dbsession.commit()
			
			logger.info('Added %d users. Failed inserts: %d' % (ctr, ctr_fail))
		except Exception as e:
			logger.exception()
		finally:
			self.dbsession.close()

	def add_cracked_passwords_gen(self, gen, disable_usercheck, disable_passwordcheck):
		mem_filter = {}
		self.get_dbsession()
		try:
			ctr = 0
			for he in gen:
				if he.nt_hash in mem_filter:
					continue
				mem_filter[he.nt_hash] = 1

				exists = False

				if disable_passwordcheck is False:
					#check if hash is already in HashEntry, if yes, skip
					if he.nt_hash:
						exists = self.dbsession.query(HashEntry.id).filter_by(nt_hash=he.nt_hash).scalar() is not None
					elif he.lm_hash:
						exists = self.dbsession.query(HashEntry.id).filter_by(lm_hash=he.lm_hash).scalar() is not None
					else:
						continue

					#print(exists)
					if exists is True:
						continue
				
				
				if disable_usercheck is False:
					#check if hash actually belongs to a user, if not, skip, otherwise put it in DB
					if he.nt_hash:
						qry = self.dbsession.query(Credential.nt_hash).filter(Credential.nt_hash == he.nt_hash)
					elif he.lm_hash:
						qry = self.dbsession.query(Credential.lm_hash).filter(Credential.lm_hash == he.lm_hash)
					else:
						continue
					
					exists = True if qry.first() else False
				
				if exists is True:
					try:
						self.dbsession.add(he)
						if ctr % 10000 == 0:
							logger.info(ctr)
						#	self.dbsession.commit()
						self.dbsession.commit()
						

					except exc.IntegrityError as e:
						logger.exception(e)
						self.dbsession.rollback()
						continue
					else:
						ctr += 1

			self.dbsession.commit()
			logger.info('Added %d plaintext passwords to the DB' % ctr)

		except Exception as e:
			logger.exception(e)
		finally:
			self.dbsession.close()
	
	def add_cracked_passwords(self, potfile, disable_usercheck, disable_passwordcheck):
		gen = HashEntry.from_potfile(potfile)
		self.add_cracked_passwords_gen(gen, disable_usercheck, disable_passwordcheck)
		
	def get_uncracked_hashes(self, hash_type, history):
		self.get_dbsession()
		try:
			if hash_type == 'NT':
				qry = self.dbsession.query(Credential.nt_hash).outerjoin(HashEntry, Credential.nt_hash == HashEntry.nt_hash).filter(Credential.nt_hash != None).distinct(Credential.nt_hash)
			else:
				qry = self.dbsession.query(Credential.lm_hash).outerjoin(HashEntry, Credential.lm_hash == HashEntry.lm_hash).filter(Credential.lm_hash != None).distinct(Credential.lm_hash)
			
			if history == False:
				qry = qry.filter(Credential.history_no == 0)
				
			for some_hash in qry.all():
				yield some_hash[0]
		except Exception as e:
			print(e)
		finally:
			self.dbsession.close()

	def get_cracked_users(self):
		qry = self.dbsession.query(ADUser, Credential, HashEntry
						).outerjoin(HashEntry, Credential.nt_hash == HashEntry.nt_hash
						).filter(HashEntry.nt_hash != None
						).filter(Credential.history_no == 0
						).filter(ADUser.ad_id == self.domain_id
						).filter(Credential.ad_id == self.domain_id
						).filter(ADUser.sAMAccountName == Credential.username
						)

		cracked_users = []
		cracked_users.append(['domain', 'username', 'canLogon', 'hashtype', 'pw_length', 'pw_lower', 'pw_upper', 'pw_digit', 'pw_special', 'crack_times_sec'])
		for user, cred, he in qry.all():
			res = [str(cred.domain), str(user.sAMAccountName), str(user.canLogon), 'NT', str(he.pw_length), str(he.pw_lower), str(he.pw_upper), str(he.pw_digit), str(he.pw_special), str(self.get_cracking_time(he))]
			cracked_users.append(res)
		
		return cracked_users

	def get_pwsharing(self):
		occurrence_ctr = {}
		pw_sharing_cracked = 0
		pw_sharing_notcracked = 0
		pw_sharing_total = 0
		pw_sharing_hash = {}

		qry = self.dbsession.query(
				func.count(Credential.nt_hash),
					Credential.nt_hash
					).filter(Credential.history_no == 0
					).filter(Credential.ad_id == self.domain_id
					).group_by(
						Credential.nt_hash
					).having(
						func.count(Credential.nt_hash) > 1
					)

		for occurrence, nthash in qry.all():
			pw_sharing_total += 1
			pw_sharing_hash[nthash] = []
			if occurrence not in occurrence_ctr:
				occurrence_ctr[occurrence] = 0
			occurrence_ctr[occurrence] += 1

			users = []
			for user in self.dbsession.query(Credential.username
									).filter(Credential.history_no == 0
									).filter(Credential.ad_id == self.domain_id
									).filter_by(nt_hash = nthash
									).distinct(Credential.username):
				users.append(user.username)
					
			pw_sharing_hash[nthash] += users
		
		for nthash in pw_sharing_hash:
			exists = self.dbsession.query(HashEntry.id).filter_by(nt_hash=nthash).scalar() is not None
			if exists is True:
				pw_sharing_cracked += 1
			else:
				pw_sharing_notcracked += 1

		#anonymizing (removing nt hash from key, replacing with an int)
		new_pwshare = {}
		for i, key in enumerate(pw_sharing_hash):
			new_pwshare[i] = pw_sharing_hash[key]
		

		return pw_sharing_total, pw_sharing_cracked, pw_sharing_notcracked, new_pwshare

	def cracked_stats(self):
		
		pw_sharing_total, pw_sharing_cracked, pw_sharing_notcracked, _ = self.get_pwsharing()

		total_objects = self.dbsession.query(Credential
			).filter(Credential.history_no == 0
			).filter(Credential.history_no == 0
			).filter(Credential.ad_id == self.domain_id
			).count()
		
		
		#how many users
		total_comps = self.dbsession.query(Credential
			).filter(Credential.username.endswith('$')
			).filter(Credential.history_no == 0
			).filter(Credential.ad_id == self.domain_id
			).count()
			
		#how many users
		total_users = total_objects - total_comps

			
		#how many total cracked
		total_objects_cracked = self.dbsession.query(Credential, HashEntry
			).outerjoin(HashEntry, Credential.nt_hash == HashEntry.nt_hash
			).filter(HashEntry.nt_hash != None
			).filter(Credential.history_no == 0
			).filter(Credential.ad_id == self.domain_id
			).count()

			
		#how many total cracked
		total_comps_cracked = self.dbsession.query(Credential, HashEntry
			).outerjoin(HashEntry, Credential.nt_hash == HashEntry.nt_hash
			).filter(Credential.username.endswith('$')
			).filter(HashEntry.nt_hash != None
			).filter(Credential.history_no == 0
			).filter(Credential.ad_id == self.domain_id
			).count()

			
		#how many users
		total_users_cracked = total_objects_cracked - total_comps_cracked



		res = {
			'total_objects' : total_objects, 
			'total_comps' : total_comps,
			'total_users' : total_users, 
			'total_objects_cracked' : total_objects_cracked, 
			'total_comps_cracked' : total_comps_cracked, 
			'total_users_cracked' : total_users_cracked, 
			'pw_sharing_total' : pw_sharing_total, 
			'pw_sharing_cracked' : pw_sharing_cracked, 
			'pw_sharing_notcracked' : pw_sharing_notcracked,
		}
		return res

	
	def get_cracked_info(self):
		raise NotImplementedError()

