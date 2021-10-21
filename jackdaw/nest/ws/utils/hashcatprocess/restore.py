import io
from typing import List

# https://hashcat.net/wiki/doku.php?id=restore
class HashcatResoreStruct:
	def __init__(self):
		self.version_bin:int = None
		self.cwd:str = None #[256];
		self.dicts_pos:int = None
		self.masks_pos:int = None
		self.words_cur:int = None #QWORD
		self.argc:int = None
		self.argv:List[str] = []

	@staticmethod
	def from_bytes(bbuff):
		lineterm = b'\n'
		msg = HashcatResoreStruct()
		msg.version_bin   = int.from_bytes(bbuff[:4], byteorder='little', signed = False)
		msg.cwd  = bbuff[4:259].decode()
		msg.dicts_pos = int.from_bytes(bbuff[260:264], byteorder='little', signed = False)
		msg.masks_pos = int.from_bytes(bbuff[264:268], byteorder='little', signed = False)
		msg.words_cur = int.from_bytes(bbuff[272:280], byteorder='little', signed = False)
		msg.argc  = int.from_bytes(bbuff[280:284], byteorder='little', signed = False)
		i = 0
		for _ in range(msg.argc):
			temp = b''
			c = b''
			while c != lineterm or i > 4096:
				temp += c
				c = bbuff[296+i:296+i+1]
				i += 1
			msg.argv.append(temp.decode())
		return msg

	def __repr__(self):
		t = '==== HashcatResoreStruct ====\r\n'
		t += 'version_bin: %s\r\n' % self.version_bin
		t += 'cwd: %s\r\n' % self.cwd
		t += 'dicts_pos: %s\r\n' % self.dicts_pos
		t += 'masks_pos: %s\r\n' % self.masks_pos
		t += 'words_cur: %s\r\n' % self.words_cur
		
		t += 'argc: %s\r\n' % self.argc
		t += 'argv: %s\r\n' % self.argv

		return t