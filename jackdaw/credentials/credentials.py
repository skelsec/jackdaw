
from jackdaw.dbmodel import create_db, get_session, Credential, HashEntry
from jackdaw.representation.passwords_report import PasswordsReport
from sqlalchemy import exc


class JackDawCredentials:
	def __init__(self, db_conn, domain_id = -1):
		self.domain_id = domain_id
		self.db_conn = db_conn

	def add_credentials_impacket(self, impacket_file):
		ctr = 0
		ctr_fail = 0
		dbsession = get_session(self.db_conn)
		try:
			for cred in Credential.from_impacket_file(impacket_file, self.domain_id):
				try:
					dbsession.add(cred)
					if ctr % 10000 == 0:
						print(ctr)
						dbsession.commit()
					
				except exc.IntegrityError as e:
					ctr_fail += 1
					dbsession.rollback()
					continue
				else:
					ctr += 1

			dbsession.commit()
			
			print('Added %d users. Failed inserts: %d' % (ctr, ctr_fail))
		except Exception as e:
			print(e)
		finally:
			dbsession.close()
	
	def add_cracked_passwords(self, potfile, disable_usercheck, disable_passwordcheck):
		mem_filter = {}
		dbsession = get_session(self.db_conn)
		try:
			ctr = 0
			for he in HashEntry.from_potfile(potfile):
				if he.nt_hash in mem_filter:
					continue
				mem_filter[he.nt_hash] = 1

				exists = False

				if disable_passwordcheck is False:
					#check if hash is already in HashEntry, if yes, skip
					if he.nt_hash:
						exists = dbsession.query(HashEntry.id).filter_by(nt_hash=he.nt_hash).scalar() is not None
					elif he.lm_hash:
						exists = dbsession.query(HashEntry.id).filter_by(lm_hash=he.lm_hash).scalar() is not None
					else:
						continue

					#print(exists)
					if exists is True:
						continue
				
				
				if disable_usercheck is False:
					#check if hash actually belongs to a user, if not, skip, otherwise put it in DB
					if he.nt_hash:
						qry = dbsession.query(Credential.nt_hash).filter(Credential.nt_hash == he.nt_hash)
					elif he.lm_hash:
						qry = dbsession.query(Credential.lm_hash).filter(Credential.lm_hash == he.lm_hash)
					else:
						continue
					
					exists = True if qry.first() else False
				
				if exists is True:
					try:
						dbsession.add(he)
						if ctr % 10000 == 0:
							print(ctr)
						#	dbsession.commit()
						dbsession.commit()
						

					except exc.IntegrityError as e:
						print(e)
						dbsession.rollback()
						continue
					else:
						ctr += 1

			dbsession.commit()
			print('Added %d plaintext passwords to the DB' % ctr)

		except Exception as e:
			print(e)
		finally:
			dbsession.close()
		
	def get_uncracked_hashes(self, hash_type, history):
		dbsession = get_session(self.db_conn)
		try:
			if hash_type == 'NT':
				qry = dbsession.query(Credential.nt_hash).outerjoin(HashEntry, Credential.nt_hash == HashEntry.nt_hash).filter(Credential.nt_hash != None).distinct(Credential.nt_hash)
			else:
				qry = dbsession.query(Credential.lm_hash).outerjoin(HashEntry, Credential.lm_hash == HashEntry.lm_hash).filter(Credential.lm_hash != None).distinct(Credential.lm_hash)
			
			if history == False:
				qry = qry.filter(Credential.history_no == 0)
				
			for some_hash in qry.all():
				print(some_hash[0])
		except Exception as e:
			print(e)
		finally:
			dbsession.close()
	
	def generate_report(self, out_folder):
		report = PasswordsReport(self.db_conn, out_folder = 'test')
		report.generate(self.domain_id)
	
	def get_cracked_info(self):
		raise NotImplementedError()

