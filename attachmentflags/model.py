 #
 # Copyright 2009, Niels Sascha Reedijk <niels.reedijk@gmail.com>
 # All rights reserved. Distributed under the terms of the MIT License.
 #
 
from trac.attachment import Attachment
 
class AttachmentFlags(object):
    def __init__(self, env, attachment):
        if not isinstance(attachment, Attachment):
            raise TypeError
        self.attachment = attachment
        self.env = env
        
        self.flags = {}
        
        db = env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT flag, value FROM attachmentflags WHERE "
                       "type=%s AND id=%s AND filename=%s", 
                       (attachment.parent_realm, attachment.parent_id, attachment.filename))
        for flag, value in cursor:
            self.flags[flag] = value

    def __contains__(self, item):
        return item in self.flags
    
    def __get_item__(self, item):
        return self.flags[item]
    
    def __len__(self):
        return len(self.flags)
                