#!/usr/bin/env python
# -*- Mode: Python, coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

from twisted.plugin import pluginPackagePaths
__path__.extend(pluginPackagePaths(__name__))

# specifically for transitioning legacy plugins, allow status/web/hooks too:
import pkg_resources
import os
for pkg in pkg_resources.require('buildbot'):
    also_support = os.path.join(pkg.location, 'buildbot', 'status', 'web', 'hooks')
    __path__.append( also_support )
    break # others are dependencies

__all__ = []

