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

from buildbot.status.web import change_hook
from buildbot.util import json
from buildbot.test.fake.web import MockRequest
#from mock import Mock

from twisted.web.resource import getChildForRequest, Resource, NoResource
from twisted.web import server

from twisted.trial import unittest
from twisted.internet import defer


class TestChangeHookUnconfigured(unittest.TestCase):

    def setUp(self):
        self.changeHook = change_hook.ChangeHookResource()
        self.resource = Resource()
        self.resource.putChild( 'change_hook', self.changeHook )

    def testBadUrl1(self):
        self.request = MockRequest( prepath='', postpath='completely/offtopic' )
        d = defer.maybeDeferred( getChildForRequest, self.resource, self.request )
        def check( res ):
            self.failUnlessIsInstance( res, NoResource )
        d.addCallback( check )
        return d

    def testBadUrl2(self):
        self.request = MockRequest( prepath='', postpath='change_hook' )
        d = defer.maybeDeferred( getChildForRequest, self.resource, self.request )
        def check( res ):
            self.failUnlessIsInstance( res, change_hook.ChangeHookResource )
        d.addCallback( check )
        return d

    def testBadUrl3(self):
        self.request = MockRequest( prepath='', postpath='change_hook/null/overrun' )
        d = defer.maybeDeferred( getChildForRequest, self.resource, self.request )
        def check( res ):
            self.failUnlessIsInstance( res, NoResource )
        d.addCallback( check )
        return d

    def testBuiltinDialectsDisabled(self):
        for tok in ( 'error', 'null', 'invalid', 'one', 'base' ):
            self.request = MockRequest( prepath='', postpath=['change_hook', tok] )
            d = defer.maybeDeferred( getChildForRequest, self.resource, self.request )
            def check( res ):
                self.failUnlessIsInstance( res, NoResource )
                self.failUnless( 'disabled' in res.detail.lower(), repr(res.__dict__) )
            d.addCallback( check )
            return d

    def testDefaultDialectIsBase(self):
        r1 = MockRequest( prepath='', postpath='change_hook/' )
        r2 = MockRequest( prepath='', postpath='change_hook/base' )
        d1 = defer.maybeDeferred( getChildForRequest, self.resource, r1 )
        d2 = defer.maybeDeferred( getChildForRequest, self.resource, r2 )
        d = defer.DeferredList( ( d1, d2 ) )
        def check( res, d1, d2 ):
            self.failUnless( type(d1.result) == type(d2.result) )
        d.addCallback( check, d1, d2 )
        return d

    def testUnkownDialect(self):
        self.request = MockRequest( prepath='', postpath='change_hook/no_such_dialect' )
        d = defer.maybeDeferred( getChildForRequest, self.resource, self.request )
        def check( res ):
            self.failUnlessIsInstance( res, NoResource )
            self.failUnless( 'unknown' in res.detail.lower(), repr(res.__dict__) )
        d.addCallback( check )
        return d





class TestChangeHookConfigured(unittest.TestCase):

    def setUp(self):
        dialects = dict(error=True, null=True, invalid=True, one=True, base=True,)
        self.change_hook = change_hook.ChangeHookResource(dialects=dialects)
        self.resource = Resource()
        self.resource.putChild( 'change_hook', self.change_hook )

    def testDefaultDialectIsBase(self):
        r1 = MockRequest( prepath='', postpath='change_hook/' )
        r2 = MockRequest( prepath='', postpath='change_hook/base' )
        d1 = defer.maybeDeferred( getChildForRequest, self.resource, r1 )
        d2 = defer.maybeDeferred( getChildForRequest, self.resource, r2 )
        d = defer.DeferredList( ( d1, d2 ) )
        def check( res, d1, d2 ):
            self.failUnless( type(d1.result) == type(d2.result) )
        d.addCallback( check, d1, d2 )
        return d

    def testInvalidRequest( self, dialect='error' ):
        self.request = MockRequest( prepath='', postpath='change_hook/'+dialect )
        res = getChildForRequest( self.resource, self.request )
        def check_request( res ):
            self.failUnless( res == server.NOT_DONE_YET, # = int(1) btw
                'expected server.NOT_DONE_YET from render_GET|render_POST' )
        def check_response( req ):
            self.failUnless( req.code % 400 + 400 == req.code,
                'Error code %03d (%s) for internal failure not in 2xx' % (req.code, req.code_message) )
        d1 = defer.maybeDeferred( res.render_GET, self.request )
        d1.addCallback( check_request )
        d2 = self.request._x_finish()
        d2.addCallback( check_response )
        return defer.DeferredList( ( d1, d2 ) )

    def testNullRequest( self, dialect='null' ):
        self.request = MockRequest( prepath='', postpath='change_hook/'+dialect )
        res = getChildForRequest( self.resource, self.request )
        def check_request( res ):
            self.failUnless( res == server.NOT_DONE_YET, # = int(1) btw
                'expected server.NOT_DONE_YET from render_GET|render_POST' )
        def check_response( req ):
            self.failUnless( req.code % 200 + 200 == req.code,
                'Error code %03d (%s) for internal failure not in 2xx' % (req.code, req.code_message) )
        d1 = defer.maybeDeferred( res.render_GET, self.request )
        d1.addCallback( check_request )
        d2 = self.request._x_finish()
        d2.addCallback( check_response )
        return defer.DeferredList( ( d1, d2 ) )

    def testDeferredInternalFailure( self, dialect='invalid' ):
        self.request = MockRequest( prepath='', postpath='change_hook/'+dialect )
        res = getChildForRequest( self.resource, self.request )
        def check_request( res ):
            self.failUnless( res == server.NOT_DONE_YET, # = int(1) btw
                'expected server.NOT_DONE_YET from render_GET|render_POST' )
        def check_response( req ):
            self.failUnless( req.code % 200 + 200 == req.code,
                'Error code %03d (%s) for internal failure not in 2xx' % (req.code, req.code_message) )
        d1 = defer.maybeDeferred( res.render_GET, self.request )
        d1.addCallback( check_request )
        d2 = self.request._x_finish()
        d2.addCallback( check_response )
        return defer.DeferredList( ( d1, d2 ) )

    def no_testImmediateInternalFailure( self, dialect='invalid' ):
        self.request = MockRequest( prepath='', postpath='change_hook/sync_call/'+dialect )
        res = getChildForRequest( self.resource, self.request )
        def check_request( res ):
            self.failUnless( res == server.NOT_DONE_YET, # = int(1) btw
                'expected server.NOT_DONE_YET from render_GET|render_POST' )
        def check_response( req ):
            self.failUnless( req.code % 500 + 500 == req.code,
                'Error code %03d (%s) for internal failure not in 2xx' % (req.code, req.code_message) )
        d1 = defer.maybeDeferred( res.render_GET, self.request )
        d1.addCallback( check_request )
        d2 = self.request._x_finish()
        d2.addCallback( check_response )
        return defer.DeferredList( ( d1, d2 ) )
    #testImmediateInternalFailure.skip = 'Blocking web hooks not yet implemented'

    def testValidRequest( self, dialect='one' ):
        self.request = MockRequest( prepath='', postpath='change_hook/'+dialect )
        res = getChildForRequest( self.resource, self.request )
        def check_request( res ):
            self.failUnless( res == server.NOT_DONE_YET, # = int(1) btw
                'expected server.NOT_DONE_YET from render_GET|render_POST' )
        def check_response( req ):
            self.failUnless( req.code % 200 + 200 == req.code,
                'Error code %03d (%s) for internal failure not in 2xx' % (req.code, req.code_message) )
        d1 = defer.maybeDeferred( res.render_GET, self.request )
        d1.addCallback( check_request )
        d2 = self.request._x_finish()
        d2.addCallback( check_response )
        return defer.DeferredList( ( d1, d2 ) )

    def testDefaultDialectGetNullChange(self):
        self.request = MockRequest( prepath='', postpath='change_hook/' )
        res = getChildForRequest( self.resource, self.request )
        def check_request( res ):
            self.failUnless( res == server.NOT_DONE_YET, # = int(1) btw
                'expected server.NOT_DONE_YET from render_GET|render_POST' )
        def check_response( req ):
            self.failUnless( req.code % 200 + 200 == req.code,
                'Error code %03d (%s) for internal failure not in 2xx' % (req.code, req.code_message) )
            self.assertEquals(len(req.addedChanges), 1)
            change = req.addedChanges[0]
            self.assertEquals(change["category"], None)
            self.assertEquals(len(change["files"]), 0)
            self.assertEquals(change["repository"], None)
            self.assertEquals(change["when"], None)
            self.assertEquals(change["who"], None)
            self.assertEquals(change["revision"], None)
            self.assertEquals(change["comments"], None)
            self.assertEquals(change["project"], None)
            self.assertEquals(change["branch"], None)
            self.assertEquals(change["revlink"], None)
            self.assertEquals(len(change["properties"]), 0)
            self.assertEquals(change["revision"], None)
        d1 = defer.maybeDeferred( res.render_GET, self.request )
        d1.addCallback( check_request )
        d2 = self.request._x_finish()
        d2.addCallback( check_response )
        return defer.DeferredList( ( d1, d2 ) )

    # Test 'base' hook with attributes. We should get a json string representing
    # a Change object as a dictionary. All values show be set.
    def testDefaultDialectWithChange(self):
        args = { "category" : ["mycat"],
                       "files" : [json.dumps(['file1', 'file2'])],
                       "repository" : ["myrepo"],
                       "when" : [1234],
                       "who" : ["Santa Claus"],
                       "number" : [2],
                       "comments" : ["a comment"],
                       "project" : ["a project"],
                       "at" : ["sometime"],
                       "branch" : ["a branch"],
                       "revlink" : ["a revlink"],
                       "properties" : [json.dumps( { "prop1" : "val1", "prop2" : "val2" })],
                       "revision" : [99] }
        self.request = MockRequest( prepath='', postpath='change_hook/', **args )
        res = getChildForRequest( self.resource, self.request )
        def check_request( res ):
            self.failUnless( res == server.NOT_DONE_YET, # = int(1) btw
                'expected server.NOT_DONE_YET from render_GET|render_POST' )
        def check_response( req ):
            self.failUnless( req.code % 200 + 200 == req.code,
                'Error code %03d (%s) for internal failure not in 2xx' % (req.code, req.code_message) )
            self.assertEquals(len(req.addedChanges), 1)
            change = req.addedChanges[0]
            self.assertEquals(change["category"], "mycat")
            self.assertEquals(change["repository"], "myrepo")
            self.assertEquals(change["when"], 1234)
            self.assertEquals(change["who"], "Santa Claus")
            self.assertEquals(change["revision"], 99)
            self.assertEquals(change["comments"], "a comment")
            self.assertEquals(change["project"], "a project")
            self.assertEquals(change["branch"], "a branch")
            self.assertEquals(change["revlink"], "a revlink")
            self.assertEquals(change['properties'], dict(prop1='val1', prop2='val2'))
            self.assertEquals(change['files'], ['file1', 'file2'])
        d1 = defer.maybeDeferred( res.render_GET, self.request )
        d1.addCallback( check_request )
        d2 = self.request._x_finish()
        d2.addCallback( check_response )
        return defer.DeferredList( ( d1, d2 ) )

