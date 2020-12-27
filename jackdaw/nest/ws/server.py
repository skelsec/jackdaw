
import asyncio
import websockets
import pathlib

from jackdaw import logger
from jackdaw.nest.ws.operator.operator import NestOperator
from jackdaw.nest.ws.guac.guacproxy import GuacProxy


class NestWebSocketServer:
	def __init__(self, listen_ip, listen_port, db_url, work_dir, backend, ssl_ctx = None):
		self.listen_ip = listen_ip
		self.listen_port = listen_port
		self.ssl_ctx = ssl_ctx
		self.db_url = db_url
		self.server = None
		self.msg_queue = None
		self.operators = {}
		self.work_dir = pathlib.Path(work_dir)
		self.graph_backend = backend
		self.graph_type = None

	async def handle_operator(self, websocket, path):
		remote_ip, remote_port = websocket.remote_address
		logger.info('Operator connected from %s:%s' % (remote_ip, remote_port))
		operator = NestOperator(websocket, self.db_url, self.msg_queue, self.work_dir, self.graph_type)
		self.operators[operator] = 1
		await operator.run()
		logger.info('Operator disconnected! %s:%s' % (remote_ip, remote_port))
	
	async def handle_guac_rdp(self, websocket, path):
		guac_ip = '127.0.0.1'
		guac_port = 4822
		gp = GuacProxy(guac_ip, guac_port, websocket)
		await gp.connect_rdp('10.10.10.102', domain ='TEST', username='victim', password= 'Passw0rd!1')
		return

	async def handle_incoming(self, websocket, path):
		print(path)
		if path == '/':
			await self.handle_operator(websocket, path)
		elif path.startswith('/rdp/'):
			await self.handle_guac_rdp(websocket, path)
		else:
			logger.info('Cant handle path %s' % path)

	async def run(self):
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
		self.server = await websockets.serve(self.handle_incoming, self.listen_ip, self.listen_port, ssl=self.ssl_ctx)
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