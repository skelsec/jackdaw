import platform
from .ldap_enumerator import *

if platform.system() == 'Windows':
	from .windows.session_enumerator import *
	from .windows.share_enumerator import *
	
else:
	from .linux.session_enumerator import *
	from .linux.share_enumerator import *

__all__ = ['']