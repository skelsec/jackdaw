#https://www.ietf.org/rfc/rfc1035.txt
import enum
import io
import asyncio
import ipaddress
import socket

class DNSResponseCode(enum.Enum):
	NOERR = 0 #No error condition
	FORMATERR = 1 #Format error - The name server was  unable to interpret the query.
	SERVERERR = 2 #Server failure - The name server was unable to process this query due to a problem with the name server.
	NAMEERR = 3 #Name Error - Meaningful only for responses from an authoritative name server, this code signifies that the domain name referenced in the query does not exist.
	NOTIMPL = 4 #Not Implemented - The name server does not support the requested kind of query.
	REFUSED = 5 #Refused - The name server refuses to perform the specified operation for policy reasons.
	RESERVED6 = 6
	RESERVED7 = 7
	RESERVED8 = 8
	RESERVED9 = 9
	RESERVED10 = 10
	RESERVED11 = 11
	RESERVED12 = 12
	RESERVED13 = 13
	RESERVED14 = 14
	RESERVED15 = 15

class DNSType(enum.Enum):
	A          = 1 #a host address (IPv4)
	NS         = 2 #an authoritative name server
	MD         = 3 #a mail destination (Obsolete - use MX)
	MF         = 4 #a mail forwarder (Obsolete - use MX)
	CNAME      = 5 #the canonical name for an alias
	SOA        = 6 #marks the start of a zone of authority
	MB         = 7 #a mailbox domain name (EXPERIMENTAL)
	MG         = 8 #a mail group member (EXPERIMENTAL)
	MR         = 9 #a mail rename domain name (EXPERIMENTAL)
	NULL       = 10 #a null RR (EXPERIMENTAL)
	WKS        = 11 #a well known service description
	PTR        = 12 #a domain name pointer
	HINFO      = 13 #host information
	MINFO      = 14 #mailbox or mail list information
	MX         = 15 #mail exchange
	TXT        = 16 #text strings
	RP         = 17 #RFC 1183 	Responsible Person 	Information about the responsible person(s) for the domain. Usually an email address with the @ replaced by a .
	AFSDB      = 18 #RFC 1183 	AFS database record 	Location of database servers of an AFS cell. This record is commonly used by AFS clients to contact AFS cells outside their local domain. A subtype of this record is used by the obsolete DCE/DFS file system.
	SIG        = 24 #RFC 2535 	Signature 	Signature record used in SIG(0) (RFC 2931) and TKEY (RFC 2930).[7] RFC 3755 designated RRSIG as the replacement for SIG for use within DNSSEC.[7]
	KEY        = 25 #RFC 2535[3] and RFC 2930[4] 	Key record 	Used only for SIG(0) (RFC 2931) and TKEY (RFC 2930).[5] RFC 3445 eliminated their use for application keys and limited their use to DNSSEC.[6] RFC 3755 designates DNSKEY as the replacement within DNSSEC.[7] RFC 4025 designates IPSECKEY as the replacement for use with IPsec.[8]
	AAAA       = 28 #RFC 3596[2] 	IPv6 address record 	Returns a 128-bit IPv6 address, most commonly used to map hostnames to an IP address of the host.
	LOC        = 29 #RFC 1876 	Location record 	Specifies a geographical location associated with a domain name
	SRV        = 33 #RFC 2782 	Service locator 	Generalized service location record, used for newer protocols instead of creating protocol-specific records such as MX.
	NAPTR      = 35 #RFC 3403 	Naming Authority Pointer 	Allows regular-expression-based rewriting of domain names which can then be used as URIs, further domain names to lookups, etc.
	KX         = 36 #RFC 2230 	Key Exchanger record 	Used with some cryptographic systems (not including DNSSEC) to identify a key management agent for the associated domain-name. Note that this has nothing to do with DNS Security. It is Informational status, rather than being on the IETF standards-track. It has always had limited deployment, but is still in use.
	CERT       = 37 #RFC 4398 	Certificate record 	Stores PKIX, SPKI, PGP, etc.
	DNAME      = 39 #RFC 6672 		Alias for a name and all its subnames, unlike CNAME, which is an alias for only the exact name. Like a CNAME record, the DNS lookup will continue by retrying the lookup with the new name.
	OPT        = 41 #RFC 6891 	Option 	This is a "pseudo DNS record type" needed to support EDNS
	APL        = 42 #RFC 3123 	Address Prefix List 	Specify lists of address ranges, e.g. in CIDR format, for various address families. Experimental.
	DS         = 43 #RFC 4034 	Delegation signer 	The record used to identify the DNSSEC signing key of a delegated zone
	SSHFP      = 44 #RFC 4255 	SSH Public Key Fingerprint 	Resource record for publishing SSH public host key fingerprints in the DNS System, in order to aid in verifying the authenticity of the host. RFC 6594 defines ECC SSH keys and SHA-256 hashes. See the IANA SSHFP RR parameters registry for details.
	IPSECKEY   = 45 #RFC 4025 	IPsec Key 	Key record that can be used with IPsec
	RRSIG      = 46 #RFC 4034 	DNSSEC signature 	Signature for a DNSSEC-secured record set. Uses the same format as the SIG record.
	NSEC       = 47 #RFC 4034 	Next Secure record 	Part of DNSSEC—used to prove a name does not exist. Uses the same format as the (obsolete) NXT record.
	DNSKEY     = 48 #RFC 4034 	DNS Key record 	The key record used in DNSSEC. Uses the same format as the KEY record.
	DHCID      = 49 #RFC 4701 	DHCP identifier 	Used in conjunction with the FQDN option to DHCP
	NSEC3      = 50 #RFC 5155 	Next Secure record version 3 	An extension to DNSSEC that allows proof of nonexistence for a name without permitting zonewalking
	NSEC3PARAM = 51 #RFC 5155 	NSEC3 parameters 	Parameter record for use with NSEC3
	TLSA       = 52 #RFC 6698 	TLSA certificate association 	A record for DANE. RFC 6698 defines "The TLSA DNS resource record is used to associate a TLS server certificate or public key with the domain name where the record is found, thus forming a 'TLSA certificate association'".
	HIP        = 55 #RFC 8005 	Host Identity Protocol 	Method of separating the end-point identifier and locator roles of IP addresses.
	CDS        = 59 #RFC 7344 	Child DS 	Child copy of DS record, for transfer to parent
	CDNSKEY    = 60 #RFC 7344 	Child DNSKEY 	Child copy of DNSKEY record, for transfer to parent
	OPENPGPKEY = 61 #RFC 7929 	OpenPGP public key record 	A DNS-based Authentication of Named Entities (DANE) method for publishing and locating OpenPGP public keys in DNS for a specific email address using an OPENPGPKEY DNS resource record.
	TKEY       = 249 #RFC 2930 	Transaction Key record 	A method of providing keying material to be used with TSIG that is encrypted under the public key in an accompanying KEY RR.[10]
	TSIG       = 250 #RFC 2845 	Transaction Signature 	Can be used to authenticate dynamic updates as coming from an approved client, or to authenticate responses as coming from an approved recursive name server[11] similar to DNSSEC.
	IXFR 	   = 251 #RFC 1996 	Incremental Zone Transfer 	Requests a zone transfer of the given zone but only differences from a previous serial number. This request may be ignored and a full (AXFR) sent in response if the authoritative server is unable to fulfill the request due to configuration or lack of required deltas.
	AXFR       = 252 #RFC 1035[1] 	Authoritative Zone Transfer 	Transfer entire zone file from the master name server to secondary name servers.
	ANY        = 255 #ANYTHING
	URI        = 256 #RFC 7553 	Uniform Resource Identifier 	Can be used for publishing mappings from hostnames to URIs.
	CAA        = 257 #RFC 6844 	Certification Authority Authorization 	DNS Certification Authority Authorization, constraining acceptable CAs for a host/domain
	


class DNSClass(enum.Enum):
	IN = 1 #the Internet
	CS = 2 #the CSNET class (Obsolete - used only for examples in some obsolete RFCs)
	CH = 3 #the CHAOS class
	HS = 4 #Hesiod [Dyer 87]
	ANY = 255

class DNSOpcode(enum.Enum):
	QUERY = 0 #a standard query ()
	IQUERY = 1 #an inverse query ()
	STATUS = 2 #a server status request ()
	RESERVED3 = 3
	RESERVED4 = 4
	RESERVED5 = 5
	RESERVED6 = 6
	RESERVED7 = 7
	RESERVED8 = 8
	RESERVED9 = 9
	RESERVED10 = 10
	RESERVED11 = 11
	RESERVED12 = 12
	RESERVED13 = 13
	RESERVED14 = 14
	RESERVED15 = 15

#the upper bit is always zero and must never be set
class DNSFlags(enum.IntFlag):
	AA         = 0x0040 #Authoritative Answer
	TC         = 0x0020 #TrunCation
	RD         = 0x0010 #Recursion Desired
	RA         = 0x0008  #Recursion Available
	RESERVED1  = 0x0004
	RESERVED2  = 0x0002
	RESERVED3  = 0x0001

class DNSResponse(enum.Enum):
	REQUEST = 0 #Query
	RESPONSE = 1

class DNSPacket():
	def __init__(self, proto = socket.SOCK_STREAM):
		self.proto     = proto
		self.PACKETLEN = None #this is for TCP
		self.TransactionID = None
		self.QR = None
		self.Opcode = None
		self.FLAGS = None
		self.Rcode = None
		self.QDCOUNT = None
		self.ANCOUNT = None
		self.NSCOUNT = None
		self.ARCOUNT = None

		self.Questions = []
		self.Answers   = []
		self.Authorities = []
		self.Additionals = []

	@staticmethod
	async def from_streamreader(reader, proto = socket.SOCK_DGRAM):
		if proto == socket.SOCK_DGRAM:
			data = await reader.read()
			return DNSPacket.from_bytes(data)
		else:
			plen_bytes = await reader.readexactly(2)
			plen = int.from_bytes(plen_bytes, byteorder = 'big', signed=False)
			data = await reader.readexactly(plen)
			return DNSPacket.from_bytes(plen_bytes + data, proto = proto)

	@staticmethod
	async def from_queue(in_q, prevdata, proto = socket.SOCK_DGRAM):
		if proto == socket.SOCK_DGRAM:
			data = await in_q.get()
			return DNSPacket.from_bytes(data)
		else:
			t, err = await in_q.get()
			if err is not None:
				raise err

			prevdata += t
			plen_bytes = prevdata[:2]
			plen = int.from_bytes(plen_bytes, byteorder = 'big', signed=False)
			return DNSPacket.from_bytes(plen_bytes + prevdata[2:2+plen], proto = proto), prevdata[plen:]

	@staticmethod
	def from_bytes(bbuff, proto = socket.SOCK_DGRAM):
		return DNSPacket.from_buffer(io.BytesIO(bbuff), proto)

	@staticmethod
	def from_buffer(buff, proto = socket.SOCK_DGRAM):
		packet = DNSPacket()
		packet.proto = proto
		if packet.proto == socket.SOCK_STREAM:
			packet.PACKETLEN = int.from_bytes(buff.read(2), byteorder = 'big', signed=False)
			buff = io.BytesIO(buff.read()) #need to repack this to a new buffer because the length field is not taken into account when calculating compressed DNSName 

		packet.TransactionID = buff.read(2)
		temp = int.from_bytes(buff.read(2), byteorder = 'big', signed=False)

		packet.QR     = DNSResponse(temp >> 15)
		packet.Opcode = DNSOpcode((temp & 0x7800) >> 11) 
		packet.FLAGS  = DNSFlags((temp  >> 4) & 0x7F)
		packet.Rcode  = DNSResponseCode(temp & 0xF)

		packet.QDCOUNT = int.from_bytes(buff.read(2), byteorder = 'big', signed=False)
		packet.ANCOUNT = int.from_bytes(buff.read(2), byteorder = 'big', signed=False)
		packet.NSCOUNT = int.from_bytes(buff.read(2), byteorder = 'big', signed=False)
		packet.ARCOUNT = int.from_bytes(buff.read(2), byteorder = 'big', signed=False)
		
		for i in range(0, packet.QDCOUNT):
			dnsq = DNSQuestion.from_buffer(buff)
			packet.Questions.append(dnsq)

		
		for i in range(0, packet.ANCOUNT):
			dnsr = DNSResourceParser.from_buffer(buff)
			packet.Answers.append(dnsr)

		for i in range(0, packet.NSCOUNT):
			dnsr = DNSResourceParser.from_buffer(buff)
			packet.Authorities.append(dnsr)

		for i in range(0, packet.ARCOUNT):
			dnsr = DNSResourceParser.from_buffer(buff)
			packet.Additionals.append(dnsr)

		return packet
		

	def __repr__(self):
		t = '== DNS Packet ==\r\n'
		t+= 'TransactionID:  %s\r\n' % self.TransactionID.hex()
		t+= 'QR:  %s\r\n' % self.QR.name
		t+= 'Opcode: %s\r\n' % self.Opcode.name
		t+= 'FLAGS: %s\r\n' % repr(self.FLAGS)
		t+= 'Rcode: %s\r\n' % self.Rcode.name
		t+= 'QDCOUNT: %s\r\n' % self.QDCOUNT
		t+= 'ANCOUNT: %s\r\n' % self.ANCOUNT
		t+= 'NSCOUNT: %s\r\n' % self.NSCOUNT
		t+= 'ARCOUNT: %s\r\n' % self.ARCOUNT

		if len(self.Questions) > 0:
			for question in self.Questions:
				t+= repr(question)

		if len(self.Answers) > 0:
			for answer in self.Answers:
				t+= repr(answer)

		if len(self.Authorities) > 0:
			for answer in self.Authorities:
				t+= repr(answer)

		if len(self.Additionals) > 0:
			for answer in self.Additionals:
				t+= repr(answer)

		return t

	def to_bytes(self):
		t = self.TransactionID

		a  = self.Rcode.value
		a |= (self.FLAGS << 4 ) & 0x7F0
		a |= (self.Opcode.value << 11) & 0x7800
		a |= (self.QR.value << 15) & 0x8000
		t += a.to_bytes(2, byteorder = 'big', signed = False)

		t += self.QDCOUNT.to_bytes(2, byteorder = 'big', signed=False)
		t += self.ANCOUNT.to_bytes(2, byteorder = 'big', signed=False)
		t += self.NSCOUNT.to_bytes(2, byteorder = 'big', signed=False)
		t += self.ARCOUNT.to_bytes(2, byteorder = 'big', signed=False)


		for q in self.Questions:
			t += q.to_bytes()

		for q in self.Answers:
			t += q.to_bytes()

		for q in self.Authorities:
			t += q.to_bytes()

		for q in self.Additionals:
			t += q.to_bytes()
		
		if self.proto == socket.SOCK_STREAM:
			self.PACKETLEN = len(t)
			t = self.PACKETLEN.to_bytes(2, byteorder = 'big', signed=False) + t

		return t

	@staticmethod
	def construct(TID, response,  flags = 0, opcode = DNSOpcode.QUERY, rcode = DNSResponseCode.NOERR, 
					questions= [], answers= [], authorities = [], additionals = [], proto = socket.SOCK_DGRAM):
		packet = DNSPacket()
		packet.proto   = proto
		packet.TransactionID = TID
		packet.QR      = response
		packet.Opcode  = opcode
		packet.FLAGS   = flags
		packet.Rcode   = rcode
		packet.QDCOUNT = len(questions)
		packet.ANCOUNT = len(answers)
		packet.NSCOUNT = len(authorities)
		packet.ARCOUNT = len(additionals)

		packet.Questions   = questions
		packet.Answers     = answers
		packet.Authorities = authorities
		packet.Additionals = additionals

		return packet


class DNSQuestion():
	def __init__(self):
		self.QNAME  = None
		self.QTYPE  = None
		self.QCLASS = None
		self.QU     = None

	@staticmethod
	def from_bytes(bbuff):
		return DNSQuestion.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff):
		qst = DNSQuestion()
		qst.QNAME  = DNSName.from_buffer(buff)
		qst.QTYPE  = DNSType(int.from_bytes(buff.read(2), byteorder = 'big', signed = False))
		temp = int.from_bytes(buff.read(2), byteorder = 'big', signed = False)
		qst.QCLASS = DNSClass(temp & 0x7fff)
		qst.QU     = bool((temp & 0x8000) >> 15)

		return qst

	def to_bytes(self):
		t  = self.QNAME.to_bytes()
		t += self.QTYPE.value.to_bytes(2, byteorder = 'big', signed = False)
		a  = self.QCLASS.value
		a |= int(self.QU) << 15
		t += a.to_bytes(2, byteorder = 'big', signed = False)

		return t

	@staticmethod
	def construct(qname, qtype, qclass, qu = False):
		qst = DNSQuestion()
		qst.QNAME     = DNSName.construct(qname)
		qst.QTYPE     = qtype
		qst.QCLASS    = qclass
		qst.QU        = qu
		return qst

	def __repr__(self):
		t = '== DNSQuestion ==\r\n'
		t+= 'QNAME:  %s\r\n' % self.QNAME.name
		t+= 'QTYPE:  %s\r\n' % self.QTYPE.name
		t+= 'QCLASS: %s\r\n' % self.QCLASS.name
		t+= 'QU    : %s\r\n' % self.QU
		return t

class DNSOPT():
	def __init__(self):
		self.Code   = None
		self.Length = None
		self.Value  = None

		#temp variable!
		self.size = None

	@staticmethod
	def from_bytes(buff):
		return DNSOPT.from_buffer(io.BytesIO(buff))

	@staticmethod
	def from_buffer(buff):
		o = DNSOPT()
		o.Code = int.from_bytes(buff.read(2), byteorder = 'big', signed = False)
		o.Length = int.from_bytes(buff.read(2), byteorder = 'big', signed = False)
		o.Value = buff.read(o.Length)
		o.size = o.Length + 2
		return o


class DNSOPTResource():
	#https://tools.ietf.org/html/rfc6891 Section 6.1.2.
	#Comments from the author: <REDACTED PROFANITIES> Seriosuly why did you re-invent the format????
	def __init__(self):
		self.NAME     = None
		self.TYPE     = None
		self.UDPSIZE  = None
		self.EXTRCODE = None
		self.VERSION  = None
		self.DO       = None
		self.Z        = None
		self.RDLENGTH = None
		self.RDATA    = None

		self.options = []

	@staticmethod
	def from_bytes(bbuff):
		return DNSOPTResource.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff):
		rsc = DNSOPTResource()
		rsc.NAME     = DNSName.from_buffer(buff)
		rsc.TYPE     = DNSType(int.from_bytes(buff.read(2), byteorder = 'big', signed = False))
		rsc.UDPSIZE  = int.from_bytes(buff.read(2), byteorder = 'big', signed = False)
		rsc.EXTRCODE = int.from_bytes(buff.read(1), byteorder = 'big', signed = False)
		rsc.VERSION  = int.from_bytes(buff.read(1), byteorder = 'big', signed = False)
		temp = int.from_bytes(buff.read(2), byteorder = 'big', signed = False)
		rsc.DO       = bool(temp & 0x8000)
		rsc.Z        = temp & 0x7fff
		rsc.RDLENGTH = int.from_bytes(buff.read(2), byteorder = 'big', signed = False)

		rsc.RDATA    = buff.read(rsc.RDLENGTH)

		#TODO Further parsing the opt elements
		"""
		i = rsc.RDLENGTH
		if rsc.RDLENGTH > 0:
			opt = DNSOPT.from_bytes(rsc.RDATA)
			rsc.options.append(opt)
		"""
		return rsc

	def __repr__(self):
		t = '== DNSOPTResource ==\r\n'
		t+= 'NAME:  %s\r\n' % self.NAME.name
		t+= 'TYPE:  %s\r\n' % self.TYPE.name
		t+= 'UDPSIZE : %d\r\n' % self.UDPSIZE
		t+= 'EXTRCODE: %s\r\n' % self.EXTRCODE
		t+= 'VERSION: %s\r\n' % self.VERSION
		t+= 'DO: %s\r\n' % repr(self.DO)
		t+= 'RDLENGTH: %d\r\n' % self.RDLENGTH
		t+= 'RDATA: %s\r\n' % repr(self.RDATA)
		return t

	def to_bytes(self):
		t  = self.NAME.to_bytes()
		t += self.TYPE.value.to_bytes(2, byteorder = 'big', signed = False)
		t += self.UDPSIZE.to_bytes(2, byteorder = 'big', signed = False)
		t += self.EXTRCODE.to_bytes(1, byteorder = 'big', signed = False)
		t += self.VERSION.to_bytes(1, byteorder = 'big', signed = False)

		a = self.Z
		a |= int(self.DO) << 15
		t += a.to_bytes(2, byteorder = 'big', signed = False)
		t += self.RDLENGTH.to_bytes(2, byteorder = 'big', signed = False)
		t += self.RDATA

		return t

class DNSResource():
	def __init__(self):
		self.NAME     = None
		self.TYPE     = None
		self.CLASS    = None
		self.CFLUSH   = None
		self.TTL      = None
		self.RDLENGTH = None
		self.RDATA    = None

	#this method will parse the Resource object until RDATA, which will be parsed by the object inheriting it
	def parse_header(self, buff):
		self.NAME     = DNSName.from_buffer(buff)
		self.TYPE     = DNSType(int.from_bytes(buff.read(2), byteorder = 'big', signed = False))
		temp = int.from_bytes(buff.read(2), byteorder = 'big', signed = False)
		self.CLASS    = DNSClass(temp & 0x7fff)
		self.CFLUSH   = bool((temp & 0x8000) >> 15)
		self.TTL      = int.from_bytes(buff.read(4), byteorder = 'big', signed = False)
		self.RDLENGTH = int.from_bytes(buff.read(2), byteorder = 'big', signed = False)
		#this is here to support proxying of packets
		pos = buff.tell()
		self.RDATA    = buff.read(self.RDLENGTH)
		buff.seek(pos, io.SEEK_SET)
		return

	@staticmethod
	def from_bytes(bbuff):
		return DNSResource.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff):
		res = DNSResource()
		res.parse_header(buff)
		res.RDATA = buff.read(res.RDLENGTH)
		return res
	
	def to_bytes(self):
		t  = self.NAME.to_bytes()
		t += self.TYPE.value.to_bytes(2, byteorder = 'big', signed = False)
		a  = self.CLASS.value
		a |= int(self.CFLUSH) << 15
		t += a.to_bytes(2, byteorder = 'big', signed = False)
		t += self.TTL.to_bytes(4, byteorder = 'big', signed = False)
		t += self.RDLENGTH.to_bytes(2, byteorder = 'big', signed = False)
		t += self.RDATA

		return t

	def construct(self, rname, rtype, rdata, ttl = 30, rclass = DNSClass.IN, cflush = False):
		res = DNSResource()
		res.NAME     = DNSName.construct(rname)
		res.TYPE     = rtype
		res.CLASS    = rclass
		res.CFLUSH   = cflush
		res.TTL      = ttl
		res.RDATA    = rdata
		return res


	def __repr__(self):
		t = '== DNSResource ==\r\n'
		t+= 'NAME:  %s\r\n' % self.NAME.name
		t+= 'TYPE:  %s\r\n' % self.TYPE.name
		t+= 'CLASS : %s\r\n' % self.CLASS.name
		t+= 'CFLUSH: %s\r\n' % self.CFLUSH
		t+= 'TTL: %s\r\n' % self.TTL
		t+= 'RDLENGTH: %s\r\n' % self.RDLENGTH
		t+= 'RDATA: %s\r\n' % repr(self.RDATA)
		return t
		
#the logic here is: all resource types contain different data in the RDATA filed
#we describe the custom data for each and every different type
#and define a new object inheriting for the base object 
class DNSAResource(DNSResource):
	def __init__(self):
		DNSResource.__init__(self)
		self.ipaddress = None

	@staticmethod
	def from_bytes(bbuff):
		return DNSAResource.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff):
		res = DNSAResource()
		res.parse_header(buff)
		res.ipaddress = ipaddress.IPv4Address(buff.read(res.RDLENGTH))
		return res

	@staticmethod
	def construct(rname, ipv4, ttl = 3000, rclass = DNSClass.IN, cflush = False):
		res = DNSAResource()
		res.NAME     = DNSName.construct(rname)
		res.TYPE     = DNSType.A
		res.CLASS    = rclass
		res.CFLUSH   = cflush
		res.TTL      = ttl
		res.ipaddress = ipv4
		
		res.RDATA    = res.ipaddress.packed
		res.RDLENGTH = len(res.RDATA) #should be 4

		return res

	def __repr__(self):
		t = '=== DNS A ===\r\n'
		t += DNSResource.__repr__(self)
		t += 'IP address: %s\r\n' % str(self.ipaddress)
		return t


class DNSAAAAResource(DNSResource):
	def __init__(self):	
		DNSResource.__init__(self)
		self.ipaddress = None

	@staticmethod
	def from_bytes(bbuff):
		return DNSAAAAResource.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff):
		res = DNSAAAAResource()
		res.parse_header(buff)
		res.ipaddress = ipaddress.IPv6Address(buff.read(res.RDLENGTH))
		return res

	@staticmethod
	def construct(rname, ipv6, ttl = 3000, rclass = DNSClass.IN, cflush = False):
		res = DNSAAAAResource()
		res.NAME     = DNSName.construct(rname)
		res.TYPE     = DNSType.AAAA
		res.CLASS    = rclass
		res.CFLUSH   = cflush
		res.TTL      = ttl
		res.ipaddress = ipv6
		
		res.RDATA    = res.ipaddress.packed
		res.RDLENGTH = len(res.RDATA) #should be 16

		return res

	def __repr__(self):
		t = '=== DNS AAAA ===\r\n'
		t += DNSResource.__repr__(self)
		t += 'IP address: %s\r\n' % str(self.ipaddress)
		return t

class DNSPTRResource(DNSResource):
	def __init__(self):	
		DNSResource.__init__(self)
		self.domainname = None

	@staticmethod
	def from_bytes(bbuff):
		return DNSPTRResource.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff):
		res = DNSPTRResource()
		res.parse_header(buff)
		res.domainname = DNSName.from_buffer(buff)
		return res

	@staticmethod
	def construct(rname, domainname, ttl = 3000, rclass = DNSClass.IN, cflush = False):
		res = DNSPTRResource()
		res.NAME     = DNSName.construct(rname)
		res.TYPE     = DNSType.PTR
		res.CLASS    = rclass
		res.CFLUSH   = cflush
		res.TTL      = ttl
		res.domainname = domainname
		
		res.RDATA    = DNSName.construct(res.domainname)
		res.RDLENGTH = len(res.RDATA) #should be 16

		return res

	def __repr__(self):
		t = '=== DNS PTR ===\r\n'
		t += DNSResource.__repr__(self)
		t += 'PTR name: %s\r\n' % str(self.domainname)
		return t

class DNSSRVResource(DNSResource):
	def __init__(self):	
		DNSResource.__init__(self)
		self.Service = None
		self.Proto = None
		self.Name = None
		self.Priority = None
		self.Weight = None
		self.Port = None
		self.Target = None

		#_Service._Proto.Name TTL Class SRV Priority Weight Port Target
		
	@staticmethod
	def from_bytes(bbuff):
		return DNSSRVResource.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff):
		res = DNSSRVResource()
		res.parse_header(buff)
		try:
			if res.NAME.name.count('.') == 4:
				res.Service, res.Proto, res.Name, tld = res.NAME.name.split('.')
				print(res.Service, res.Proto, res.Name, tld)
			else:
				res.Service = res.NAME.name
		except Exception as e:
			print(res.NAME.name)
			raise(e)
		res.Priority = int.from_bytes(buff.read(2), byteorder = 'big', signed = False)
		res.Weight = int.from_bytes(buff.read(2), byteorder = 'big', signed = False)
		res.Port = int.from_bytes(buff.read(2), byteorder = 'big', signed = False)
		res.Target = DNSName.from_buffer(buff)

		return res

	def __repr__(self):
		t = '=== DNS SRV ===\r\n'
		t += DNSResource.__repr__(self)
		t += 'Priority: %s\r\n' % str(self.Priority)
		t += 'Weight: %s\r\n' % str(self.Weight)
		t += 'Port: %s\r\n' % str(self.Port)
		t += 'Target: %s\r\n' % str(self.Target)
		return t

class DNSResourceParser:
	@staticmethod
	def from_bytes(bbuff):
		return DNSResourceParser.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff):
		pos = buff.tell()

		resname = DNSName.from_buffer(buff)
		restype = DNSType(int.from_bytes(buff.read(2), byteorder = 'big', signed = False))

		#Extended dns?
		if restype == DNSType.OPT:
			buff.seek(pos, io.SEEK_SET)
			return DNSOPTResource.from_buffer(buff)

		#nope.
		else:
			#rewinding the buffer
			buff.seek(pos, io.SEEK_SET)
			#now parse for various types
			if restype == DNSType.A:
				rsc = DNSAResource.from_buffer(buff)
			elif restype == DNSType.AAAA:
				rsc = DNSAAAAResource.from_buffer(buff)
			elif restype == DNSType.PTR:
				rsc = DNSPTRResource.from_buffer(buff)
			elif restype == DNSType.SRV:
				rsc = DNSSRVResource.from_buffer(buff)

			#catch-all for not fully implemented or unknown types
			#feel free to expand the if-else statement above...
			else:
				rsc = DNSResource.from_buffer(buff)
				

		return rsc


class DNSName():
	def __init__(self):
		self.name            = ''
		#variables below are for parsing only
		self.compressed      = False
		self.compressed_pos  = None
		self.compressed_done = False
			
	@staticmethod
	def from_bytes(bbuff):
		return DNSName.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff):
		dnsname = DNSName()
		dnsname.parse(buff)
		return dnsname
		

	def parse(self, data, rec = False):
		#this code is ugly :(
		if self.compressed_done:
			return
		temp = data.read(1)[0]
		if not self.compressed:
			self.compressed = (temp & 0xC0) >> 6 == 0x3
			if self.compressed:
				data.seek(-1, io.SEEK_CUR)
				self.compressed_pos = data.tell()
				temp = int.from_bytes(data.read(2), byteorder = 'big', signed = False)
				ptr = temp & 0x3fff
				data.seek(ptr, io.SEEK_SET)
				self.parse(data, rec)
				data.seek(self.compressed_pos + 2, io.SEEK_SET)
				self.compressed_done = True
				return
		
		length = temp
		if length == 0:			
			return

		if length < 63:
			if rec:
				self.name += '.' + data.read(length).decode()
			else:
				self.name += data.read(length).decode()
			self.parse(data, True)

	@staticmethod
	def construct(name):
		dnsname = DNSName()
		dnsname.name = name
		return dnsname


	def to_bytes(self):
		#not using compression here! implement yourself and do a PR please
		#will give you chokolate
		t = b''
		for label in self.name.split('.'):
			t += len(label).to_bytes(1, byteorder = 'big', signed = False)
			t += label.encode()

		t += b'\x00'
		return t

	def __repr__(self):
		return self.name

	"""
	def decode_NS(self, encoded_name):
		#encoded http://www.ietf.org/rfc/rfc1001.txt
		transform = [((i - 0x41)& 0x0F) for i in encoded_name]
		i = 0
		while i < len(transform):
			self.QNAME += chr(transform[i] << 4 | transform[i+1] ) 
			i+=2
	"""