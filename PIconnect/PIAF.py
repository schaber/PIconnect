""" PIAF
    Core containers for connections to the PI Asset Framework.
"""
# Copyright 2017 Hugo van den Berg, Stijn de Jong

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# pragma pylint: disable=unused-import, redefined-builtin
from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import (
    ascii,
    bytes,
    chr,
    dict,
    filter,
    hex,
    input,
    int,
    list,
    map,
    next,
    object,
    oct,
    open,
    pow,
    range,
    round,
    str,
    super,
    zip,
)

try:
    from __builtin__ import str as BuiltinStr
except ImportError:
    BuiltinStr = str
# pragma pylint: enable=unused-import, redefined-builtin
from warnings import warn

from PIconnect.AFSDK import AF
from PIconnect.PIAFBase import PIAFBaseElement
from PIconnect.PIConsts import EventFrameSearchMode


class PIAFDatabase(object):
    """PIAFDatabase

    Context manager for connections to the PI Asset Framework database.
    """

    version = "0.2.0"

    servers = {
        s.Name: {"server": s, "databases": {d.Name: d for d in s.Databases}}
        for s in AF.PISystems()
    }
    default_server = servers[AF.PISystems().DefaultPISystem.Name]

    def __init__(self, server=None, database=None):
        self.server = None
        self.database = None
        self._initialise_server(server)
        self._initialise_database(database)

    def _initialise_server(self, server):
        if server and server not in self.servers:
            message = 'Server "{server}" not found, using the default server.'
            warn(message=message.format(server=server), category=UserWarning)
        server = self.servers.get(server, self.default_server)
        self.server = server["server"]

    def _initialise_database(self, database):
        server = self.servers.get(self.server.Name)
        if not server["databases"]:
            server["databases"] = {x.Name: x for x in self.server.Databases}
        if database and database not in server["databases"]:
            message = 'Database "{database}" not found, using the default database.'
            warn(message=message.format(database=database), category=UserWarning)
        default_db = self.server.Databases.DefaultDatabase
        self.database = server["databases"].get(database, default_db)

    def __enter__(self):
        self.server.Connect()
        return self

    def __exit__(self, *args):
        pass
        # Disabled disconnecting because garbage collection sometimes impedes
        # connecting to another server later
        # self.server.Disconnect()

    def __repr__(self):
        return "%s(\\\\%s\\%s)" % (
            self.__class__.__name__,
            self.server_name,
            self.database_name,
        )

    @property
    def server_name(self):
        """Return the name of the connected PI AF server."""
        return self.server.Name

    @property
    def database_name(self):
        """Return the name of the connected PI AF database."""
        return self.database.Name

    @property
    def children(self):
        """Return a dictionary of the direct child elements of the database."""
        return {c.Name: PIAFElement(c) for c in self.database.Elements}

    def descendant(self, path):
        """Return a descendant of the database from an exact path."""
        return PIAFElement(self.database.Elements.get_Item(path))

    def event_frames(
        self,
        start_time=None,
        start_index=0,
        max_count=1000,
        search_mode=EventFrameSearchMode.STARTING_AFTER,
        search_full_hierarchy=False,
    ):
        if not start_time:
            start_time = AF.Time.AFTime.Now
        return {
            frame.Name: PIAFEventFrame(frame)
            for frame in AF.EventFrame.AFEventFrame.FindEventFrames(
                self.database,
                None,
                start_time,
                start_index,
                max_count,
                search_mode,
                None,
                None,
                None,
                None,
                search_full_hierarchy,
            )
        }


class PIAFElement(PIAFBaseElement):
    """Container for PI AF elements in the database."""

    version = "0.1.0"

    @property
    def parent(self):
        """Return the parent element of the current element, or None if it has none."""
        if not self.element.Parent:
            return None
        return self.__class__(self.element.Parent)

    @property
    def children(self):
        """Return a dictionary of the direct child elements of the current element."""
        return {c.Name: self.__class__(c) for c in self.element.Elements}

    def descendant(self, path):
        """Return a descendant of the current element from an exact path."""
        return self.__class__(self.element.Elements.get_Item(path))


class PIAFEventFrame(PIAFBaseElement):
    """Container for PI AF Event Frames in the database."""

    version = "0.1.0"

    @property
    def event_frame(self):
        return self.element

    @property
    def parent(self):
        """Return the parent element of the current element, or None if it has none."""
        if not self.element.Parent:
            return None
        return self.__class__(self.element.Parent)
