 #
 # Copyright 2009, Niels Sascha Reedijk <niels.reedijk@gmail.com>
 # All rights reserved. Distributed under the terms of the MIT License.
 #

import datetime
import time

from trac.attachment import Attachment
from trac.util.datefmt import to_timestamp, utc
 
class AttachmentFlags(object):
    def __init__(self, env, attachment):
        if not isinstance(attachment, Attachment):
            raise TypeError
        self.attachment = attachment
        self.env = env
        
        self.__flags = {}
        self.__updatedflags = []
        
        db = env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT flag, value, updated_on, updated_by FROM attachmentflags WHERE "
                       "type=%s AND id=%s AND filename=%s", 
                       (attachment.parent_realm, attachment.parent_id, attachment.filename))
        for flag, value, updated_on, updated_by in cursor:
            self.__flags[flag] = {"value": value, 
                                "updated_on": updated_on, 
                                "updated_by": updated_by}

    def __contains__(self, item):
        return item in self.__flags
    
    def __getitem__(self, item):
        return self.__flags[item]
    
    def __len__(self):
        return len(self.__flags)
    
    def setflag(self, flag, value, author, db=None):
        if not db:
            db = self.env.get_db_cnx()

        cursor = db.cursor()
        timestamp = time.time()
        # It still needs to be added
        if flag not in self.__flags:
            cursor.execute("INSERT INTO attachmentflags VALUES "
                           "(%s,%s,%s,%s,%s,%s,%s,%s)", (self.attachment.parent_realm,
                           self.attachment.parent_id, self.attachment.filename, flag, value,
                           author, timestamp, author))
            self.__updatedflags.append(flag)
            db.commit()

        self.__updatedflags.append(flag)
        self.__flags[flag] = {"value": value,
                              "updated_on": timestamp,
                              "updated_by": author}
        db.commit()
    
    def finishupdate(self, db=None):
        if not db:
            db = self.env.get_db_cnx()

        dbflags = self.__flags.keys()

        for flag in self.__updatedflags:
            if flag in dbflags:
                dbflags.remove(flag)
        
        if len(dbflags) > 0:
            for flag in dbflags:
                cursor = db.cursor()
                cursor.execute("DELETE FROM attachmentflags WHERE type=%s AND "
                               "id=%s AND filename=%s AND flag=%s", 
                               (self.attachment.parent_realm, self.attachment.parent_id, 
                                self.attachment.filename, flag))
        db.commit()
        