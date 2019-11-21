from setuptools import setup, find_packages

setup(
	# Application name:
	name="jackdaw",

	# Version number (initial):
	version="0.1.6",

	# Application author details:
	author="Tamas Jos",
	author_email="info@skelsec.com",

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
		'aiosmb>=0.1.7',
		'msldap>=0.2.4',
		'sqlalchemy',
		'dnspython',
		'tqdm',
		'networkx',
		'connexion',
		'flask-sqlalchemy',
		'connexion[swagger-ui]',
		'pypykatz>=0.2.4',
        'swagger-ui-bundle>=0.0.2'
	],
	entry_points={
		'console_scripts': [
			'jackdaw = jackdaw.__main__:main',
		],
	}
)
