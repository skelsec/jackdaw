import zipfile
import json
import codecs
import pprint

from jackdaw.dbmodel import *
from jackdaw.dbmodel.adinfo import ADInfo
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.aduser import ADUser
from jackdaw.dbmodel.adgroup import Group
from jackdaw.dbmodel.adou import ADOU

class BHImport:
	def __init__(self, db_conn = None, db_session = None):
		self.zipfile = None
		self.files = None
		self.db_conn = db_conn
		self.db_session = db_session

		self.is_zip = False
		self.fd = {}
		self.ads = {}
		self.adn = {} #name -> ad_id

		#self.setup_db()

	def setup_db(self):
		if self.db_session is None:
			self.db_session = get_session(self.db_conn)

	def import_machines(self):
		print('Importing machines!')
		for machine in self.get_file('computers')['computers']:
			#pprint.pprint(machine)
			#input()
			
			m = Machine()
			m.ad_id = self.ads[machine['Properties']['objectsid'].rsplit('-',1)[0]]
			m.sAMAccountName = machine['Name'].split('.', 1)[0] + '$'
			m.objectSid = machine['Properties']['objectsid']
			m.description = machine['Properties']['description']
			m.operatingSystemVersion  = machine['Properties']['operatingsystem']

			self.db_session.add(m)
		self.db_session.commit()

	def import_users(self):
		print('Importing users!')
		for user in self.get_file('users')['users']:
			#pprint.pprint(user)
			#input()
			
			m = ADUser()
			m.ad_id = self.ads[user['Properties']['objectsid'].rsplit('-',1)[0]]
			m.name = user['Name'].split('@', 1)[0]
			m.objectSid = user['Properties']['objectsid']
			m.description = user['Properties']['description']
			m.displayName  = user['Properties']['displayname']
			m.email  = user['Properties']['email']

			self.db_session.add(m)
		self.db_session.commit()

	def import_sessions(self):
		print('Importing sessions!')
		for session in self.get_file('sessions')['sessions']:
			#pprint.pprint(session)
			#input()
			try:
				if session['ComputerName'].startswith('['):
					continue
				ad_name = session['UserName'].rsplit('@', 1)[1]
				cname = session['ComputerName'] + '$'
				if session['ComputerName'].find('.') != -1:
					cname = session['ComputerName'].split('.', 1)[0] + '$'

				qry = self.db_session.query(
					Machine.id
					).filter_by(ad_id = self.adn[ad_name]
					).filter(Machine.sAMAccountName == cname
					)
				machine_id = qry.first()
				if machine_id is None:
					raise Exception('Could not find machine!')
				m = NetSession()
				m.machine_id = machine_id[0]
				m.username = session['UserName'].split('@', 1)[0]

				self.db_session.add(m)
			except Exception as e:
				#print(e)
				#pprint.pprint(session)
				#input()
				continue
		self.db_session.commit()

	def import_ous(self):
		print('Importing ous!')
		for ou in self.get_file('ous')['ous']:
			#pprint.pprint(groups)
			#input()
			try:
				ad_name = ou['Name'].rsplit('@', 1)[1]
				m = ADOU()
				m.ad_id = self.adn[ad_name]
				m.name = ou['Name'].split('@', 1)[0]
				m.objectSid = ou['Properties']['objectsid']
				m.description = ou['Properties'].get('description', None)

				self.db_session.add(m)
			except Exception as e:
				print(e)
				pprint.pprint(ou)
				input()
				continue
		self.db_session.commit()

	def import_domains(self):
		print('Importing domains!')
		for domain in self.get_file('domains')['domains']:#['computers']:
			#pprint.pprint(domain)
			#input()

			di = ADInfo()
			di.name = domain['Name']
			di.objectSid = domain['Properties']['objectsid']

			self.db_session.add(di)
			self.db_session.commit()
			self.db_session.refresh(di)
			self.ad_id = di.id

			self.ads[di.objectSid] = di.id
			self.adn[di.name] = di.id

	def import_gpos(self):
		print('Importing gpos!')
		for gpo in self.get_file('gpos')['gpos']:
			pprint.pprint(gpo)
			input()
			try:
				ad_name = ou['Name'].rsplit('@', 1)[1]
				m = ADOU()
				m.ad_id = self.adn[ad_name]
				m.name = ou['Name'].split('@', 1)[0]
				m.objectSid = ou['Properties']['objectsid']
				m.description = ou['Properties'].get('description', None)

				self.db_session.add(m)
			except Exception as e:
				print(e)
				pprint.pprint(ou)
				input()
				continue
		self.db_session.commit()

	def import_groups(self):
		print('Importing groups!')
		for groups in self.get_file('groups')['groups']:
			#pprint.pprint(groups)
			#input()
			try:
				ad_name = groups['Name'].rsplit('@', 1)[1]
				m = Group()
				m.ad_id = self.adn[ad_name]
				m.name = groups['Name'].split('@', 1)[0]
				m.objectSid = groups['Properties']['objectsid']
				m.description = groups['Properties'].get('description', None)

				self.db_session.add(m)
			except Exception as e:
				print(e)
				pprint.pprint(groups)
				input()
				continue
		self.db_session.commit()

	def get_file(self, filetype):
		if self.is_zip is True:
			with zipfile.ZipFile(filepath, 'r') as zf:
				with zf.open(self.fd[filetype]) as data:
					return json.load(data)

	@staticmethod
	def from_zipfile(filepath):
		bh = BHImport()
		if not zipfile.is_zipfile(filepath):
			raise Exception('The file on this path doesnt look like a valid zip file! %s' % filepath)
		
		bh.is_zip = True
		zip = zipfile.ZipFile(filepath, 'r')
		for filename in zip.namelist():
			if filename.find('_computers.json') != -1:
				bh.fd['computers'] = filename
			elif filename.find('_domains.json') != -1:
				bh.fd['domains'] = filename
			elif filename.find('_gpos.json') != -1:
				bh.fd['gpos'] = filename
			elif filename.find('_groups.json') != -1:
				bh.fd['groups'] = filename
			elif filename.find('_ous.json') != -1:
				bh.fd['ous'] = filename
			elif filename.find('_sessions.json') != -1:
				bh.fd['sessions'] = filename
			elif filename.find('_users.json') != -1:
				bh.fd['users'] = filename

		return bh

	def from_folder(self, folderpath):
		pass

	def run(self):
		#DO NOT CHANGE THIS ORDER!!!!
		self.setup_db()
		self.import_domains()
		#self.import_groups()
		#self.import_machines()
		#self.import_users()
		#self.import_sessions()
		self.import_gpos()


		#self.import_ous() #not working!


if __name__ == '__main__':
	import sys
	db_conn = 'sqlite:///bhtest.db'
	filepath = sys.argv[1]

	create_db(db_conn)
	
	bh = BHImport.from_zipfile(filepath)
	bh.db_conn = db_conn
	bh.run()

