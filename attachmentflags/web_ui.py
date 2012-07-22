 #
 # Copyright 2010, Niels Sascha Reedijk <niels.reedijk@gmail.com>
 # All rights reserved. Distributed under the terms of the MIT License.
 #

import datetime
from pkg_resources import resource_filename
from genshi.builder import tag, Fragment
from genshi.filters.transform import Transformer
import re
import urllib

from trac.attachment import IAttachmentChangeListener, Attachment
from trac.core import *
from trac.ticket.model import Ticket
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, ITemplateStreamFilter, add_notice, add_script
from trac.util import get_reporter_id
from trac.util.datefmt import pretty_timedelta, format_datetime, to_timestamp, utc
from attachmentflags.model import AttachmentFlags

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
                           "(%s,%s,%s,%s,%s,%s,%s)", (attachment.parent_realm,
                           attachment.parent_id, attachment.filename, flag, value,
                           to_timestamp(attachment.date) , attachment.author))
                
        # Update patch flag of the ticket if needed
        if "patch" in self.salvaged_data and not "obsolete" in self.salvaged_data:
            ticket = Ticket(self.env, int(attachment.parent_id), db)
            ticket["patch"] = "1"
            ticket.save_changes(attachment.author, None, db=db)            
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
        if req.path_info.startswith('/attachment/') and 'ticket' in req.path_info:
            # Salvage flags for a new attachment. These will be stored
            # in attachment_added()
            action = req.args.get('action', 'view')
            if req.method == 'POST' and action == "new":
                # NOTE: no need to assert permissions: if it is not allowed
                # then the actual attachment will never be added.
                
                # Salvage all attachment flags.
                for flag in self.known_flags:
                    data = req.args.get('flag_' + flag)
                    if data:
                        self.salvaged_data[flag] = data
            # Update flags
            elif req.method == 'POST' and action == "update_flags":
                match = re.match(r'/attachment/([^/]+)/([^/]+)/(.+)?$',req.path_info)
                if match:
                    type, id, filename = match.groups()
                    
                    if type != "ticket":
                        return handler
                    
                    flags = {}
                    for flag in self.known_flags:
                        data = req.args.get('flag_' + flag)
                        if data:
                            flags[flag] = data
                    
                    db = self.env.get_db_cnx()
                    attachment = Attachment(self.env, type, id, filename, db=db)
                    attachmentflags = AttachmentFlags(self.env, attachment, db)
                    
                    # Permission check: everybody can add flags to their own attachments
                    # Else they need 'TICKET_MODIFY'
                    
                    if get_reporter_id(req) != attachment.author:
                        req.perm.require('TICKET_MODIFY')
                    
                    for flag, value in flags.items():
                        attachmentflags.setflag(flag, value, get_reporter_id(req), db)
                    attachmentflags.finishupdate()
                    
                    # Update the patch field on the ticket
                    cursorattachments = db.cursor()
                    cursorattachments.execute("SELECT filename FROM attachment WHERE type=%s "
                                              "AND id=%s", (attachment.parent_realm, attachment.parent_id))
                    attachments = []
                    for filename in cursorattachments: #I'm pretty sure we always end up with len>0
                        attachments.append(filename[0])
                    
                    patchcount = 0
                    for filename in attachments:
                        has_patch = False
                        cursorpatch = db.cursor()
                        cursorpatch.execute("SELECT value FROM attachmentflags WHERE type='ticket' "
                                            "AND flag='patch' AND id=%s AND filename=%s", (attachment.parent_id, filename))
                        if cursorpatch.fetchone():
                            # See whether the patch is obsoleted
                            cursorobsolete = db.cursor()
                            cursorobsolete.execute("SELECT filename FROM attachmentflags WHERE type='ticket' "
                                                "AND flag='obsolete' AND id=%s AND filename=%s", (attachment.parent_id,filename))
                            if not cursorobsolete.fetchone():
                                has_patch = True
                        if has_patch:
                            patchcount += 1
                                
                    ticket = Ticket(self.env,int(attachment.parent_id), db)
                    if patchcount > 0:
                        ticket["patch"] = "1"
                    else:
                        ticket["patch"] = "0"
                    ticket.save_changes(get_reporter_id(req), None)
                
                req.redirect(req.path_info)

        return handler
    
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type        
 

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == "attachment.html" and data["attachment"] and data["attachment"].parent_realm == "ticket":
            if data["mode"] == "new":
                stream |= Transformer("//fieldset").after(self._generate_attachmentflags_fieldset(readonly=False))
            elif data["mode"] == "list":
                stream = self._filter_obsolete_attachments_from_stream(stream, data["attachments"]["attachments"])
            elif data["mode"] == "view":
                flags = AttachmentFlags(self.env, data["attachment"])
                if 'TICKET_MODIFY' in req.perm or get_reporter_id(req) == data["attachment"].author:
                    stream |= Transformer("//div[@id='preview']").after(self._generate_attachmentflags_fieldset(readonly=False, current_flags=flags, form=True))
                else:
                    stream |= Transformer("//div[@id='preview']").after(self._generate_attachmentflags_fieldset(current_flags=flags))
        if filename == "ticket.html":
            if "attachments" in data:
                stream = self._filter_obsolete_attachments_from_stream(stream, data["attachments"]["attachments"])
            stream = self._disable_patch_field_edit(stream)
        return stream
    
    # Internal
    def _disable_patch_field_edit(self, stream):
        stream |= Transformer("//label[@for='field-patch']").wrap('strike')
        stream |= Transformer("//input[@id='field-patch']").attr('disabled','disabled')
        return stream
        
    def _generate_attachmentflags_fieldset(self, readonly=True, current_flags=None, form=False):
        fields = Fragment()
        for flag in self.known_flags:
            flagid = 'flag_' + flag
            if current_flags and flag in current_flags:
                date = datetime.datetime.fromtimestamp(current_flags[flag]["updated_on"],utc)
                text = tag.span(tag.strong(flag), " set by ", 
                                tag.em(current_flags[flag]["updated_by"]), ", ", tag.span(pretty_timedelta(date),
                                                  title=format_datetime(date)), " ago")
                if readonly == True:
                    fields += tag.input(text, \
                                        type='checkbox', id=flagid, \
                                        name=flagid, checked="checked",
                                        disabled="true") + tag.br()
                else:
                    fields += tag.input(text, \
                                        type='checkbox', id=flagid, \
                                        name=flagid, checked="checked") + tag.br()
            else:
                if readonly == True:
                    fields += tag.input(flag, \
                                        type='checkbox', id=flagid, \
                                        name=flagid, disabled="true") + tag.br()
                else:
                    fields += tag.input(flag, \
                                        type='checkbox', id=flagid, \
                                        name=flagid) + tag.br()
        if form and not readonly:
            return tag.form(tag.fieldset(tag.legend("Attachment Flags") + fields,
                                         tag.input(type="hidden", name="action", value="update_flags"),
                                         tag.input(type="submit", value="Update flags")),  
                            method="POST")
        return tag.fieldset(tag.legend("Attachment Flags") + fields)

    def _filter_obsolete_attachments_from_stream(self, stream, attachments):
        for attachment in attachments:
            flags = AttachmentFlags(self.env, attachment)
            if "obsolete" in flags:
                href = "/attachment/%s/%s/%s" % (attachment.parent_realm, attachment.parent_id, urllib.quote(attachment.filename))
                stream |= Transformer("//div[@id='attachments']/div/dl[@class='attachments']/dt/a[@href='" + href + "']").wrap('s')        
        return stream                
