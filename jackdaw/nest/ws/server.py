
import asyncio
import websockets
import pathlib
import functools
import os
from http import HTTPStatus
from urllib.parse import urlparse, parse_qs

from jackdaw import logger
from jackdaw.nest.ws.operator.operator import NestOperator
from jackdaw.nest.ws.guac.guacproxy import GuacProxy
from jackdaw.dbmodel import get_session
from jackdaw.dbmodel.adcomp import Machine
from jackdaw.dbmodel.dnslookup import DNSLookup
from jackdaw.dbmodel.credential import Credential
from jackdaw.dbmodel.storedcreds import StoredCred
from jackdaw.dbmodel.customtarget import CustomTarget

# https://gist.github.com/artizirk/04eb23d957d7916c01ca632bb27d5436
# https://www.howtoforge.com/how-to-install-and-configure-guacamole-on-ubuntu-2004/

class NestWebSocketServer:
	def __init__(self, listen_ip, listen_port, db_url, work_dir, backend, ssl_ctx = None):
		self.listen_ip = listen_ip
		self.listen_port = listen_port
		self.ssl_ctx = ssl_ctx
		self.db_url = db_url
		self.db_session = None
		self.server = None
		self.msg_queue = None
		self.operators = {}
		self.work_dir = pathlib.Path(work_dir)
		self.graph_backend = backend
		self.graph_type = None
		self.subprotocols = ['guacamole']

		self.guac_ip = '127.0.0.1'
		self.guac_port = 4822
		self.guac_html_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'guac', 'html')
		self.guac_html_rdp_path = os.path.join(self.guac_html_folder, 'rdp.html')
		self.guac_html_vnc_path = os.path.join(self.guac_html_folder, 'vnc.html')
		self.guac_html_ssh_path = os.path.join(self.guac_html_folder, 'ssh.html')
		self.guac_html_js_folder = os.path.join(self.guac_html_folder, 'js')

	def get_target_address(self, ad_id, taget_sid):
		hostname = None
		if str(ad_id) == '0':
			res = self.db_session.query(CustomTarget).get(taget_sid)
			if res is not None:
				hostname = res.hostname
		else:
			res = self.db_session.query(Machine.dNSHostName).filter_by(objectSid = taget_sid).filter(Machine.ad_id == ad_id).first()
			if res is not None:
				hostname = res[0]
			else:
				res = self.db_session.query(DNSLookup.ip).filter_by(sid = taget_sid).filter(DNSLookup.ad_id == ad_id).first()
				if res is not None:
					hostname = res[0]

		print(hostname)
		return hostname

	def get_stored_cred(self, ad_id, user_sid):
		domain = None
		username = None
		password = None

		if str(ad_id) == '0':
			res = self.db_session.query(StoredCred).get(user_sid)
			
		else:
			res = self.db_session.query(Credential).filter_by(object_sid = user_sid).filter(Credential.ad_id == ad_id).first()
		
		if res is None:
			return False, None, None, None
		
		domain   = res.domain
		username = res.username
		password = res.password
		return True, domain, username, password

	async def handle_operator(self, websocket, path):
		remote_ip, remote_port = websocket.remote_address
		logger.info('Operator connected from %s:%s' % (remote_ip, remote_port))
		operator = NestOperator(websocket, self.db_url, self.msg_queue, self.work_dir, self.graph_type)
		self.operators[operator] = 1
		await operator.run()
		logger.info('Operator disconnected! %s:%s' % (remote_ip, remote_port))
	
	async def handle_guac(self, websocket, path, protocol):
		

		o = urlparse(path)
		q = parse_qs(o.query)
		print(q)
		
		#these parameters are mandatory!
		target_ad_id = q['tadid'][0]
		target_sid = q['target'][0]
		user_ad_id = q['uadid'][0]
		user_sid = q['user'][0]

		hostname = self.get_target_address(target_ad_id, target_sid)
		res, domain, username, password = self.get_stored_cred(user_ad_id, user_sid)
		#if res is False:
		#	print('Couldnt find credentials for user id %s' % user_sid)
		#	return

		gp = GuacProxy(self.guac_ip, self.guac_port, websocket)

		gp.video_width = q.get('width', ['1024'])[0]
		gp.video_height = q.get('height', ['768'])[0]
		gp.video_dpi = q.get('dpi', ['96'])[0]

		if protocol == 'rdp':
			port = q.get('port', ['3389'])[0]
			await gp.connect_rdp(
				hostname= hostname, 
				port = port,
				domain = domain,
				username= username,
				password= password
			)
		elif protocol == 'ssh':
			port = q.get('port', ['22'])[0]
			await gp.connect_ssh(
				hostname='10.10.10.101', 
				port = port,
				domain = None, 
				username= 'jackdaw', 
				password= 'jackdaw'
			)
		elif protocol == 'vnc':
			port = q.get('port', ['5900'])[0]
			await gp.connect_vnc(
				hostname='10.10.10.102', 
				port = port,
				domain = None, 
				username='test', 
				password= 'test'
			)
		
		return

	async def handle_incoming(self, websocket, path):
		print(path)
		if path == '/':
			await self.handle_operator(websocket, path)
		elif path.startswith('/guac/rdp'):
			await self.handle_guac(websocket, path, 'rdp')
		elif path.startswith('/guac/ssh'):
			await self.handle_guac(websocket, path, 'ssh')
		elif path.startswith('/guac/vnc'):
			await self.handle_guac(websocket, path, 'vnc')
		else:
			logger.info('Cant handle path %s' % path)

	async def preprocess_request(self, path, request_headers):
		try:
			"""Serves a file when doing a GET request with a valid path."""

			if "Upgrade" in request_headers:
				return  # Probably a WebSocket connection
			
			print(path)
			#print(request_headers)
			response_headers = [
				('Server', 'JackDaw webserver'),
				('Connection', 'close'),
			]

			if path.startswith('/guac/js/guacamole-common-js/all.min.js'):
				with open(os.path.join(self.guac_html_js_folder, 'guacamole-common-js','all.min.js'), 'rb') as f:
					body = f.read()

				response_headers.append(('Content-Type', 'text/javascript'))
				return HTTPStatus.OK, response_headers, body


			elif path.startswith('/guac/rdp'):
				with open(self.guac_html_rdp_path, 'rb') as f:
					body = f.read()

				response_headers.append(('Content-Type', 'text/html'))
				return HTTPStatus.OK, response_headers, body
			
			elif path.startswith('/guac/vnc'):
				with open(self.guac_html_vnc_path, 'rb') as f:
					body = f.read()

				response_headers.append(('Content-Type', 'text/html'))
				return HTTPStatus.OK, response_headers, body

			elif path.startswith('/guac/ssh'):
				with open(self.guac_html_ssh_path, 'rb') as f:
					body = f.read()

				response_headers.append(('Content-Type', 'text/html'))
				return HTTPStatus.OK, response_headers, body

		except Exception as e:
			print(e)
			return HTTPStatus.INTERNAL_SERVER_ERROR, response_headers, b''

	async def run(self):
		if self.db_url is None:
			raise Exception('db_url must be either sqlalchemy url or an established db session')
		if isinstance(self.db_url, str):
			self.db_session = get_session(self.db_url)
		else:
			self.db_session = self.db_url

		if self.graph_backend.upper() == 'networkx'.upper():
			from jackdaw.nest.graph.backends.networkx.domaingraph import JackDawDomainGraphNetworkx
			self.graph_type = JackDawDomainGraphNetworkx
		elif self.graph_backend.upper() == 'igraph'.upper():
			from jackdaw.nest.graph.backends.igraph.domaingraph import JackDawDomainGraphIGraph
			self.graph_type = JackDawDomainGraphIGraph
		elif self.graph_backend.upper() == 'graphtools'.upper():
			from jackdaw.nest.graph.backends.graphtools.domaingraph import JackDawDomainGraphGrapthTools
			self.graph_type = JackDawDomainGraphGrapthTools

		pathlib.Path(self.work_dir).mkdir(parents=True, exist_ok=True)
		pathlib.Path(self.work_dir).joinpath('graphcache').mkdir(parents=True, exist_ok=True)

		self.msg_queue = asyncio.Queue()
		#handler = functools.partial(process_request, os.getcwd())
		self.server = await websockets.serve(
			self.handle_incoming, 
			self.listen_ip, 
			self.listen_port, 
			ssl=self.ssl_ctx,
			process_request=self.preprocess_request,
			subprotocols=self.subprotocols
		)
		print('[+] Server is running!')
		await self.server.wait_closed()


async def amain(args):
	server = NestWebSocketServer(args.listen_ip, args.listen_port, args.sql, args.work_dir, args.backend, ssl_ctx = None)
	await server.run()

def main():
	import argparse
	parser = argparse.ArgumentParser(description='WS server')
	parser.add_argument('--sql', help='SQL connection string. When using SQLITE it works best with FULL FILE PATH!!!')
	parser.add_argument('--listen-ip',  default = '127.0.0.1', help='IP address to listen on')
	parser.add_argument('--listen-port',  type=int, default = 5001, help='IP address to listen on')
	parser.add_argument('--work-dir', default = './workdir', help='Working directory for caching and tempfiles')
	parser.add_argument('--backend', default = 'networkx', help='graph backend, pls dont change this')

	args = parser.parse_args()

	asyncio.run(amain(args))


if __name__ == '__main__':
	main()