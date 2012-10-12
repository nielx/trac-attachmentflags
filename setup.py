#!/usr/bin/env python

 #
 # Copyright 2009, Niels Sascha Reedijk <niels.reedijk@gmail.com>
 # All rights reserved. Distributed under the terms of the MIT License.
 #

from setuptools import setup

setup(
    name = 'TracAttachmentFlags',
    version = '0.1.3',
    packages = ['attachmentflags'],
#    package_data = { 'attachmentflags': ['htdocs/*.js'] },

    author = 'Niels Sascha Reedijk',
    author_email = 'niels.reedijk@gmail.com',
    description = 'Provides support for attachment flags.',
    license = 'BSD',
    keywords = 'trac plugin attachment flags',
    url = 'http://hg.haiku-os.org/trac-attachmentflags',
    classifiers = [
        'Framework :: Trac',
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    
    install_requires = ['Trac>=0.12', 'Genshi>=0.6'],

    entry_points = {
        'trac.plugins': [
            'attachmentflags.api = attachmentflags.api',
            'attachmentflags.web_ui = attachmentflags.web_ui',
        ]
    }
)
