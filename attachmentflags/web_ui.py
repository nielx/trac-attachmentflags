 #
 # Copyright 2009, Niels Sascha Reedijk <niels.reedijk@gmail.com>
 # All rights reserved. Distributed under the terms of the MIT License.
 #

from pkg_resources import resource_filename
from genshi.builder import tag
from genshi.filters.transform import Transformer

from trac.core import *
from trac.ticket import model
from trac.util.text import unicode_quote_plus
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, ITemplateStreamFilter, add_notice, add_script
from trac.ticket.roadmap import TicketGroupStats

class AttachmentFlagsModule(Component):
    """Implements attachment flags for Trac's interface."""
    
    implements(IRequestFilter, ITemplateStreamFilter)
 
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type        
 

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        return stream
