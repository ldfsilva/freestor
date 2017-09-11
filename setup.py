# coding: utf-8
from setuptools import setup
import os


README = os.path.join(os.path.dirname(__file__), 'README.rst')
REQUIREMENTS = os.path.join(os.path.dirname(__file__), 'requirements.txt')


if __name__ == "__main__":
    setup(name='freestor',
          version='0.1',
          description='A python library to interact with FalconStor FreeStor REST API',
          long_description=open(README).read(),
          author='Leandro Silva', author_email='ldfsilva@gmail.com',
          url='http://github.com/ldfsilva/freestor',
          keywords=['freestor', 'requests', 'falconstor', 'ipstor'],
          install_requires=open(REQUIREMENTS).readlines(),
          packages=['freestor'],
          package_dir={'freestor': 'freestor'},
          entry_points={
              'console_scripts': [
              'freestor = freestor.cli:main',
          ]
          },
          zip_safe=False,
          platforms='any',
          include_package_data=True,
          classifiers=[
              'Development Status :: 4 - Beta',
              'Environment :: Console',
              'Intended Audience :: Developers',
              'Intended Audience :: System Administrators',
              'Natural Language :: English',
              'Programming Language :: Python :: 2.6',
              'Programming Language :: Python :: 2.7',
              'Programming Language :: Python :: 3.5',
              'Programming Language :: Python :: 3.6',
              'Programming Language :: Python :: 3.7',
              'Topic :: System :: Systems Administration',
              'Topic :: Utilities',
          ])
