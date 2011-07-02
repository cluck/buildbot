# -*- Mode: Python, coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

# code inspired/copied from contrib/github_buildbot
#  and inspired from code from the Chromium project
# otherwise, Andrew Melo <andrew.melo@gmail.com> wrote the rest
# but "the rest" is pretty minimal

from twisted.web import resource
from twisted.python import log
from twisted.internet import defer
from twisted.web import server
from twisted.web.resource import NoResource
from twisted.python.failure import Failure

from twisted.plugin import getPlugins, IPlugin
from buildbot.status.web.api import IBuildbotWebhookDialect



class ChangeHookResource(resource.Resource):

     # this is a cheap sort of template thingy

    contentType = "text/html; charset=utf-8"
    #children    = {}

    def __init__(self, dialects={}):

        """
        The keys of 'dialects' select a modules to load under
        master/buildbot/status/web/hooks/
        The value is passed to the module's getChanges function, providing
        configuration options to the dialect.
        """

        resource.Resource.__init__( self )

        self.dialects = {
            'base': False,
            'error': False,
            'invalid': False,
            'null': False,
            'one': False,
        }
        self.dialects.update( dialects )

        import buildbot.plugins
        for p in getPlugins(IPlugin, buildbot.plugins):
            log.msg( 'IBuildbotWebhookDialect plugin in use: ' + repr(p) )
            for dialect in list( p.dialects() ):
                if dialect in dialects and dialects[dialect] != False:
                    log.msg( ' - supports dialect ' + dialect )
                else:
                    log.msg( ' - supports dialect ' + dialect + ' (disabled)' )


    def getChild(self, name, request):
        if not name:
            name = 'base'
        if name == 'sync_call':
            raise NotImplementedError( 'synchronized call not implemented' )
        if name in self.dialects or name is 'base':
            if 'base' not in self.dialects or self.dialects[name] == False:
                msg = "Dialect '%s' is disabled for this instance of WebStatus()" % name
                log.err( msg )
                return NoResource( msg )
            else:
                return DialectResource( name, self.dialects[name] )
        else:
            msg = 'Unknown WebStatus() dialect ' + name
            log.err( msg )
            return NoResource( msg )



class DialectResource( resource.Resource ):


    contentType = "text/html; charset=utf-8"
    isLeaf = True


    def __init__( self, dialect, options ):
        resource.Resource.__init__( self )
        self.dialect = dialect
        self.options = options


    def render_GET( self, request ):
        """
        Responds to events and starts the build process
          different implementations can decide on what methods they will accept
        """
        return self.render_POST( request )


    def render_POST( self, request ):
        """
        Responds to events and starts the build process
          different implementations can decide on what methods they will accept

        :arguments:
            request
                the http request object
        """

        try:
            changes = list( self.get_changes( request ) )
        except ValueError, e:
            request.setResponseCode( 400, e.args[0] ) # Client Error 4xx / 400 Bad Request
            request.finish()
            return server.NOT_DONE_YET
        except NotImplementedError, e:
            request.setResponseCode( 501, e.args[0] ) # Server Error 5xx / 501 Not Implemented
            request.finish()
            return server.NOT_DONE_YET
        except Exception, e:
            log.err(e)
            import traceback
            traceback.print_exc()
            request.setResponseCode( 500, e.args[0] ) # Server Error 5xx
            request.finish()
            return server.NOT_DONE_YET

        if not changes:
            log.msg( 'No dialect generated changes for request' )
            request.setResponseCode( 200, 'OK no changes' )
            request.finish()
            return server.NOT_DONE_YET

        d = self.submit_changes( changes, request )
        d.addBoth( self._cb_render_POST, request, changes )
        d.addErrback( log.err )
        return server.NOT_DONE_YET


    def _cb_render_POST( self, result, request, changes ):
        log.msg( 'Queued %d changes' % len(changes) )
        if isinstance( result, Failure ):
            request.setResponseCode( 400, result.getErrorMessage() )
        else:
            request.setResponseCode( 200, 'OK %d changes' % len(changes) )
        request.finish()
        return result


    def get_changes(self, request ):
        """
        Take the logic from the change hook, and then delegate it
        to the proper handler
        http://localhost/change_hook/DIALECT will load up
        buildmaster/status/web/hooks/DIALECT.py

        and call getChanges()

        the return value is a list of changes

        if DIALECT is unspecified, a sample implementation is provided
        """

        import buildbot.plugins
        for plugin in getPlugins(IBuildbotWebhookDialect, buildbot.plugins):
            for di in iter(plugin.dialects()):
                if di == self.dialect:
                    for change in plugin.changes( request, self.dialect, self.options ):
                        log.msg( 'change from %s' % plugin )
                        yield change


    @defer.deferredGenerator
    def submit_changes(self, changes, request):
        master = request.site.buildbot_service.master
        for chdict in changes:
            if chdict.get('_discard_change', False) != False:
                log.msg( 'discarding change as requested by plugin' )
                continue
            wfd = defer.waitForDeferred( master.addChange(**chdict) )
            yield wfd
            change = wfd.getResult()
            log.msg( "Injected change %s" % change )

