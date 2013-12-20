#
# Copyright (c) 2012, 2013 Hewlett-Packard Development Company, L.P.
#
# Confidential computer software. Valid license from HP required for
# possession, use or copying. Consistent with FAR 12.211 and 12.212,
# Commercial Computer Software, Computer Software Documentation, and
# Technical Data for Commercial Items are licensed to the U.S. Government
# under vendor's standard commercial license.
#

""" Automatically generate the man page from argparse"""

import datetime
import argparse
from distutils.command.build import build
from distutils.core import Command
from distutils.errors import DistutilsOptionError

class create_manpage(Command):

    user_options = []

    def initialize_options(self):
        from ghp import main

        self._output = self.distribution.get_name() + '.1'
        self._seealso = ["git:1"]
        self._today = datetime.date.today()
        self._commands, self._parser = main.get_parser()
        self._parser.formatter = ManPageFormatter()

    def finalize_options(self):
        pass

    def _markup(self, txt):
        return txt.replace('-', '\\-')

    def _write_header(self):
        version = self.distribution.get_version()
        appname = self.distribution.get_name()
        ret = []
        ret.append('.TH %s 1 %s "%s v.%s"\n' % (self._markup(appname),
                                      self._today.strftime('%Y\\-%m\\-%d'),
                                      appname, version))
        description = self.distribution.get_description()
        if description:
            name = self._markup('%s - %s' % (self._markup(appname),
                                             description.splitlines()[0]))
        else:
            name = self._markup(appname)
        ret.append('.SH NAME\n%s\n' % name)
        synopsis = self._parser.format_help()
        if synopsis:
            synopsis = synopsis.replace('%s ' % appname, '')
            ret.append('.SH SYNOPSIS\n.B %s\n%s\n' % (self._markup(appname),
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

    def _write_seealso (self):
        ret = []
        if self._seealso is not None:
            ret.append('.SH "SEE ALSO"\n')

            for i in self._seealso:
                name, sect = i.split(":")

                if len(ret) > 1:
                    ret.append(',\n')

                ret.append('.BR %s (%s)' % (name, sect))

        return ''.join(ret)

    def _write_footer(self):
        ret = []
        appname = self.distribution.get_name()
        author = '%s <%s>' % (self.distribution.get_author(),
                              self.distribution.get_author_email())
        ret.append(('.SH AUTHORS\n.B %s\nwas written by %s.\n'
                    % (self._markup(appname), self._markup(author))))

        return ''.join(ret)

    def run(self):
        manpage = []
        manpage.append(self._write_header())
        manpage.append(self._write_options())
        manpage.append(self._write_footer())
        manpage.append(self._write_seealso())
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

    def _markup(self, txt):
        return txt.replace('-', '\\-')

    def format_usage(self, usage):
        return self._markup(usage)

    def format_heading(self, heading):
        if self.level == 0:
            return ''
        return '.TP\n%s\n' % self._markup(heading.upper())

    def format_option(self, option):
        result = []
        opts = self.option_strings[option]
        result.append('.TP\n.B %s\n' % self._markup(opts))
        if option.help:
            help_text = '%s\n' % self._markup(self.expand_default(option))
            result.append(help_text)
        return ''.join(result)


build.sub_commands.append(('create_manpage', None))

