from setuptools import setup, find_packages

setup(name='aiocmd',
      packages=find_packages("."),
      version='0.1.4',
      author='Dor Green',
      author_email='dorgreen1@gmail.com',
      description='Coroutine-based CLI generator using prompt_toolkit',
      url='http://github.com/KimiNewt/aiocmd',
      keywords=['asyncio', 'cmd'],
      license='MIT',
      install_requires=[
          'prompt_toolkit>=2.0.9'
      ],
      classifiers=[
          'License :: OSI Approved :: MIT License',

          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7'
      ])
