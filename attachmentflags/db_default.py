 #
 # Copyright 2009, Niels Sascha Reedijk <niels.reedijk@gmail.com>
 # All rights reserved. Distributed under the terms of the MIT License.
 #
 
from trac.db import Table, Column

name = 'attachmentflags'
version = 1
tables = [
    Table('attachmentflags', key=('type','id','filename','flag')) [
        Column('type'),
        Column('id'),
        Column('filename'),
        Column('flag'),
        Column('value'),
        Column('requested_by'),
        Column('updated_on', type="int"),
        Column('updated_by'),
    ],
]
