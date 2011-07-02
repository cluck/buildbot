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


from twisted.plugin import IPlugin


class IBuildbotWebhookDialect( IPlugin ):

    def dialects():
        """Iterator of strings of supported dialects."""

    def changes( request, options=None ):
        """Iterator of changes (dict).

        Changes with non-false key _discard_change will be discarded.
        """

