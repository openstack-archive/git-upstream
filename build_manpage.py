#
# Copyright (c) 2012, 2013, 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

""" Automatically generate the man page from argparse"""

import argparse
import datetime
from distutils.core import Command
import os


class BuildManpage(Command):

    user_options = []
    command_name = 'build_manpage'

    def initialize_options(self):
        self._output = self.distribution.get_name() + '.1'
        self._see_also = ["git:1"]
        self._today = datetime.date.today()
        self._commands = self._parser = None

    def finalize_options(self):
        from git_upstream import main
        self._commands, self._parser = main.build_parsers()
        self._parser.formatter = ManPageFormatter()

    def _markup(self, txt):
        return txt.replace('-', '\\-')

    def _write_header(self):
        version = self.distribution.get_version()
        app_name = self.distribution.get_name()
        ret = list()
        ret.append('.TH %s 1 %s "%s v.%s"\n' % (self._markup(app_name),
                                                self._today.strftime(
                                                    '%Y\\-%m\\-%d'),
                                                app_name, version))
        description = self.distribution.get_description()
        if description:
            name = self._markup('%s - %s' % (app_name,
                                             description.splitlines()[0]))
        else:
            name = app_name
        ret.append('.SH NAME\n%s\n' % name)
        synopsis = self._parser.format_help()
        if synopsis:
            synopsis = synopsis.replace('%s ' % app_name, '')
            ret.append('.SH SYNOPSIS\n.B %s\n%s\n' % (app_name,
                                                      synopsis))
        long_desc = self.distribution.get_long_description()
        if long_desc:
            ret.append('.SH DESCRIPTION\n%s\n' % self._markup(long_desc))

        return ''.join(ret)

    def _write_options(self):
        ret = ['.SH OPTIONS\n']
        for command in self._commands.keys():
            ret.append('.BR %s\n\n' % command)
            ret.append(self._commands[command].format_help())
            ret.append('\n')

        return ''.join(ret)

    def _write_see_also(self):
        ret = []
        if self._see_also is not None:
            ret.append('.SH "SEE ALSO"\n')

            for i in self._see_also:
                name, sect = i.split(":")

                if len(ret) > 1:
                    ret.append(',\n')

                ret.append('.BR %s (%s)' % (name, sect))

        return ''.join(ret)

    def _write_footer(self):
        ret = []
        app_name = self.distribution.get_name()
        author = '%s <%s>' % (self.distribution.get_author(),
                              self.distribution.get_author_email())
        ret.append(('.SH AUTHORS\n.B %s\nwas written by %s.\n'
                    % (self._markup(app_name), self._markup(author))))

        if os.path.exists('ACKNOWLEDGEMENTS'):
            acknowledgements = open('ACKNOWLEDGEMENTS', 'r').read()
            if acknowledgements != "":
                ret.append(('.SH ACKNOWLEDGEMENTS\n%s\n' % acknowledgements))

        return ''.join(ret)

    def run(self):
        manpage = list()
        manpage.append(self._write_header())
        manpage.append(self._write_options())
        manpage.append(self._write_footer())
        manpage.append(self._write_see_also())
        stream = open(self._output, 'w')
        stream.write(''.join(manpage))
        stream.close()


class ManPageFormatter(argparse.ArgumentDefaultsHelpFormatter):

    def __init__(self,
                 indent_increment=2,
                 max_help_position=24,
                 width=None,
                 short_first=1):
        argparse.HelpFormatter.__init__(self, indent_increment,
                                        max_help_position, width, short_first)

    @staticmethod
    def _markup(txt):
        return txt.replace('-', '\\-')

    def format_usage(self, usage):
        return ManPageFormatter._markup(usage)
