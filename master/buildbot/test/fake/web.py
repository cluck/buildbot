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

from mock import Mock

from twisted.web.http import RESPONSES

from twisted.internet import defer

class MockRequest( Mock ):
    """
    A fake Twisted Web Request object, including some pointers to the
    buildmaster and an addChange method on that master which will append its
    arguments to self.addedChanges.
    """
    def __init__(self, *args, **kwargs):

        self.args = kwargs
        for k, v in kwargs.items():
            setattr( self, k, v )

        if isinstance( self.__dict__.setdefault( 'prepath', [] ), basestring ):
            self.prepath = self.prepath.split('/')
        if isinstance( self.__dict__.setdefault( 'postpath', [] ), basestring ):
            self.postpath = self.postpath.split('/')

        self.__dict__.setdefault( 'site', Mock() )
        self.site.__dict__.setdefault( 'buildbot_service', Mock() )
        master = self.site.buildbot_service.__dict__.setdefault( 'master', Mock() )

        self.addedChanges = []
        def addChange(**kwargs):
            self.addedChanges.append(kwargs)
            return defer.succeed(Mock())
        master.addChange = addChange

        self.d = defer.Deferred()

        Mock.__init__(self)


    def setResponseCode( self, code, message=None ):
        """
        Set the HTTP response code.
        """
        if not isinstance(code, (int, long)):
            raise TypeError("HTTP response code must be int or long")
        self.code = code
        if message:
            self.code_message = message
        else:
            self.code_message = RESPONSES.get(code, "Unknown Status")

    def finish( self ):
        if self.d:
            d, self.d = self.d, None
            d.callback( self )

    def _x_finish( self ):
        if not self.d:
            return defer.succeed( self )
        d = defer.Deferred()
        d.addCallback( self.d.callback )
        self.d, d = d, self.d
        return d

