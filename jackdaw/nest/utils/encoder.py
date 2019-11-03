import json
import enum
import ipaddress
import datetime
from connexion.apps.flask_app import FlaskJSONEncoder

class UniversalFlaskEncoder(FlaskJSONEncoder):
	"""
	Used to override the default json encoder to provide a direct serialization for formats
	that the default json encoder is incapable to serialize
	"""
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return obj.isoformat()
		elif isinstance(obj, enum.Enum):
			return obj.value
		elif isinstance(obj, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
			return str(obj)
		elif hasattr(obj, 'to_dict'):
			return obj.to_dict()
		else:
			return json.JSONEncoder.default(self, obj)