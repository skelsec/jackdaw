from setuptools import setup, find_packages
import re

VERSIONFILE="jackdaw/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))


setup(
	# Application name:
	name="jackdaw",

	# Version number (initial):
	version=verstr,

	# Application author details:
	author="Tamas Jos",
	author_email="skelsecprojects@gmail.com",

	# Packages
	packages=find_packages(),

	# Include additional files into the package
	include_package_data=True,
	
	# Details
	url="https://github.com/skelsec/jackdaw",

	zip_safe = False,
	#
	# license="LICENSE.txt",
	description="Gathering shiny things from your domain",

	# long_description=open("README.txt").read(),
	python_requires='>=3.6',
	classifiers=(
		"Programming Language :: Python :: 3.6",
		"Operating System :: OS Independent",
	),
	install_requires=[
		'aiosmb>=0.2.21',
		'msldap>=0.3.10',
		'sqlalchemy',
		'tqdm',
		'networkx',
		'connexion',
		'flask-sqlalchemy',
		'connexion[swagger-ui]',
		'pypykatz>=0.3.6',
        'swagger-ui-bundle>=0.0.2',
		'werkzeug==0.16.1',
		'bidict',
		'colorama; platform_system=="Windows"',
		'winacl>=0.0.6; platform_system=="Windows"',
	],
	entry_points={
		'console_scripts': [
			'jackdaw = jackdaw.__main__:main',
		],
	}
)
