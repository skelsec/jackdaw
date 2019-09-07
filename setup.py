from setuptools import setup, find_packages

setup(
	# Application name:
	name="jackdaw",

	# Version number (initial):
	version="0.0.3",

	# Application author details:
	author="Tamas Jos",
	author_email="info@skelsec.com",

	# Packages
	packages=find_packages(),

	# Include additional files into the package
	include_package_data=True,
	
	# Details
	url="https://github.com/skelsec/jackdaw",

	zip_safe = True,
	#
	# license="LICENSE.txt",
	description="Gathering shiny things from your domain",

	# long_description=open("README.txt").read(),
	python_requires='>=3.6',
	classifiers=(
		"Programming Language :: Python :: 3.6",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	),
	install_requires=[
		'winrecon>=0.0.1',
		'aiosmb>=0.0.2',
		'msldap>=0.1.0',
		'sqlalchemy',
		'dnspython',
		'pyvis',
	],

	
)
