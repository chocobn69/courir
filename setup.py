#!/usr/bin/env python

from setuptools import setup

setup(name='courir',
      version='0.1',
      license='GNU',
      description='Python Ssh to runabove / ovh cloud helper',
      author='Nicolas Baccelli',
      author_email='nicolas.baccelli@gmail.com',
      url='https://github.com/chocobn69/courir',
      packages=['sergent', ],
      scripts=['scripts/sergent'],
      install_requires=[
          'python-runabove>=1.3',
      ],
      classifiers=[
          #  How mature is this project? Common values are
          #   3 - Alpha
          #   4 - Beta
          #   5 - Production/Stable
          'Development Status :: 4 - Beta',

          'Environment :: Console',

          # Indicate who your project is intended for
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'Topic :: Software Development :: Build Tools',

          # Pick your license as you wish (should match "license" above)
          'License :: OSI Approved :: GNU General Public License (GPL)',

          # Specify the Python versions you support here. In particular, ensure
          # that you indicate whether you support Python 2, Python 3 or both.
          'Programming Language :: Python :: 3',
          ]
)
