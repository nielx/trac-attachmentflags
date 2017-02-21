 #
 # Copyright 2009-2017, Niels Sascha Reedijk <niels.reedijk@gmail.com>
 # All rights reserved. Distributed under the terms of the MIT License.
 #

import time

from trac.attachment import Attachment

class AttachmentFlags(object):
    def __init__(self, env, attachment):
        if not isinstance(attachment, Attachment):
            raise TypeError
        self.attachment = attachment
        self.env = env
        
        self.__flags = {}
        self.__updatedflags = []
        
        with env.db_query as db:
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
    
    def setflag(self, flag, value, author):
        with self.env.db_transaction as db:
            timestamp = time.time()
            # It still needs to be added
            if flag not in self.__flags:
                db.cursor().execute("INSERT INTO attachmentflags VALUES "
                               "(%s,%s,%s,%s,%s,%s,%s)", (self.attachment.parent_realm,
                               self.attachment.parent_id, self.attachment.filename, flag, value,
                               timestamp, author))
                self.__updatedflags.append(flag)

            self.__updatedflags.append(flag)
            self.__flags[flag] = {"value": value,
                                  "updated_on": timestamp,
                                  "updated_by": author}

    def finishupdate(self):
        dbflags = self.__flags.keys()

        for flag in self.__updatedflags:
            if flag in dbflags:
                dbflags.remove(flag)

        with self.env.db_transaction as db:
            if len(dbflags) > 0:
                for flag in dbflags:
                    cursor = db.cursor()
                    cursor.execute("DELETE FROM attachmentflags WHERE type=%s AND "
                                   "id=%s AND filename=%s AND flag=%s",
                                   (self.attachment.parent_realm, self.attachment.parent_id,
                                    self.attachment.filename, flag))
                    del self.__flags[flag]
        self.__updatedflags = []
