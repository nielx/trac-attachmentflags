 #
 # Copyright 2009, Niels Sascha Reedijk <niels.reedijk@gmail.com>
 # All rights reserved. Distributed under the terms of the MIT License.
 #

import datetime
from pkg_resources import resource_filename
from genshi.builder import tag
from genshi.filters.transform import Transformer

from trac.attachment import IAttachmentChangeListener
from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, ITemplateStreamFilter, add_notice, add_script
from trac.util.datefmt import to_timestamp, utc

class AttachmentFlagsModule(Component):
    """Implements attachment flags for Trac's interface.
    Currently there are two default fixed attributes available:
     * patch:    marks the attachment as a patch
     * obsolete: marks the attachment as obsolete (i.o.w. a soft delete)
    """
    
    implements(IAttachmentChangeListener, IRequestFilter, ITemplateStreamFilter)
 
    known_flags = ["patch", "obsolete",]
    
    salvaged_data = {}
 
    # IAttachmentChangeListener methods
    def attachment_added(self, attachment):
        """Called when an attachment is added. Add the flags that we intercepted
        during a new command. No need to check permissions: if the user did have
        permission to create the attachment, he can create the flags."""
        if len(self.salvaged_data) == 0:
            return
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        for flag, value in self.salvaged_data.items():
            cursor = db.cursor()
            cursor.execute("INSERT INTO attachmentflags VALUES "
                           "(%s,%s,%s,%s,%s,%s,%s,%s)", (attachment.parent_realm,
                           attachment.parent_id, attachment.filename, flag, value,
                           attachment.author, to_timestamp(attachment.date) , attachment.author))
        db.commit()
    
    def attachment_deleted(self, attachment):
        """Called when an attachment is deleted."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("DELETE FROM attachmentflags WHERE type=%s AND id=%s "
                       "AND filename=%s", (attachment.parent_realm, attachment.parent_id,
                                           attachment.filename))
        db.commit()
 
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if req.path_info.startswith('/attachment/'):
            # override the attachment's own routines here
            action = req.args.get('action', 'view')
            if req.method == 'POST' and action == "new":
                # Salvage all attachment flags.
                for flag in self.known_flags:
                    data = req.args.get('flag_' + flag)
                    if data:
                        self.salvaged_data[flag] = data

        return handler
    
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type        
 

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == "attachment.html":
            if data["mode"] == "new":
                stream |= Transformer("//fieldset").after(self._generate_attachmentflags_fieldset())
        return stream
    
    # Internal
    def _generate_attachmentflags_fieldset(self):
        return tag.fieldset(tag.legend("Attachment Flags") +  \
                            tag.input("Patch", \
                                      type='checkbox', id='flag_patch', \
                                      name='flag_patch') + tag.br() + \
                            tag.input("Obsolete", \
                                      type='checkbox', id='flag_obsolete', \
                                      name='flag_obsolete'))                                      
