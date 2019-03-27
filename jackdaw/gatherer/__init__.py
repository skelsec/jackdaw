import platform
from .ldap_enumerator import *

if platform.system() == 'Windows':
	from .windows.session_monitor import *
	from .windows.share_enumerator import *
	
else:
	from .linux.session_monitor import *
	from .linux.share_enumerator import *

__all__ = ['LDAPEnumerator','SessionMonitor','ShareEnumerator']