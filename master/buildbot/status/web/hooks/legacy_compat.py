#!/usr/bin/env python
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


from zope.interface import implements

from twisted.plugin import IPlugin
from buildbot.status.web.api import IBuildbotWebhookDialect

from twisted.python.reflect import namedModule

import os
from os.path import splitext, basename
import glob

from twisted.python import log



DUMMY_CHANGE = dict(
    revision = 0,
    author='root', #who='root',
    comments = 'nope',
    branch = 'trunk',
    category = 'main',
    revlink = 'http://example.org/',
    repository = '297f711d-216a-466b-9181-f5a93ec79a14',
    project = 'TestCase',
    files = ('/dev/null', '/dev/zero',),
    _discard_change = True,
)


class DummyDialectsPlugin( object ):

    """This plugins implements fake responses for testing functionality.

    The error dialect simulates an internal failure for any request,
    the null dialect consumes any request and sees no changes in it,
    the invalid dialect submits a bogus change with does not validate,
    the one dialect generates a valid, dummy change (marked to be discarded later).

    The dialects null, error and one are probably most useful to test
    software producing web calls to Buildbot.
    """

    implements( IPlugin, IBuildbotWebhookDialect )

    _DIALECTS = 'error/null/invalid/one'

    def dialects( self ):
        for dialect in self._DIALECTS.split('/'):
            yield dialect

    def changes( self, request, dialect, options=None ):
        if dialect == 'error':
            raise ValueError('Error as per request')
        if dialect == 'null':
            raise StopIteration
        if dialect == 'invalid':
            yield dict(malformed_on_purpose=True)
            raise StopIteration
        if dialect == 'one':
            yield DUMMY_CHANGE
            raise StopIteration
        raise RuntimeError('unknown dialect '+dialect)

    def __repr__( self ):
        return '<%s: %s>' % (type(self).__name__, self._DIALECTS)



class LegacyWebhookPluginAdapter( object ):

    implements( IPlugin, IBuildbotWebhookDialect )

    def __init__( self, dialect, mod ):
        self.dialect = dialect
        self.m = mod

    def dialects( self ):
        yield self.dialect

    def changes( self, request, dialect, options=None ):
        changes = self.m.getChanges( request, options )
        if changes:
            for change in changes:
                yield change

    def __repr__( self ):
        return '<%s: %s>' % (type(self).__name__, self.dialect)



_dummy_dialects = DummyDialectsPlugin()

_compats = globals()

for py in glob.glob( os.path.join( os.path.dirname( __file__ ), '*.py' ) ):
    dialect = splitext( basename( py ) )[0]
    if dialect in ('__init__', 'legacy_compat'):
        continue
    try:
        mod = namedModule( 'buildbot.status.web.hooks.' + dialect )
        getattr( mod, 'getChanges' )
    except AttributeError, e:
        continue
    k = 'compat_plugin: '+dialect    # any string is OK in python
    _compats[k] = LegacyWebhookPluginAdapter( dialect, mod )
    log.msg( 'legacy plugin for dialect %s loaded' %( dialect, ) )

