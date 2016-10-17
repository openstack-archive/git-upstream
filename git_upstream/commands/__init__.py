#
# Copyright (c) 2011 OpenStack LLC.
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

import abc
import argparse
import os
import textwrap


class AppendReplaceAction(argparse._AppendAction):
    """Allows setting of a default value which is overridden by the first use
    of the option, while subsequent calls will then append.
    """
    def __init__(self, *args, **kwargs):
        super(AppendReplaceAction, self).__init__(*args, **kwargs)
        self._reset_default = False
        self.default = list(self.default)

    def __call__(self, parser, namespace, values, option_string=None):
        if not self._reset_default:
            setattr(namespace, self.dest, [])
            self._reset_default = True
        super(AppendReplaceAction, self).__call__(parser, namespace, values,
                                                  option_string)


class GitUpstreamCommand(object):
    """Base command class

    To create commands simply subclass and implement the necessary abstract
    methods.
    """

    __metaclass__ = abc.ABCMeta
    usage = ""

    def __init__(self, parser):
        self.parser = parser
        self.args = None

    def validate(self):
        """Verify the arguments passed for this command"""

    def finalize(self):
        """Additional updating of the args to set values"""

    @abc.abstractmethod
    def execute(self):
        """Execute this command"""
        raise NotImplementedError

    def run(self, args):
        self.args = args
        self.finalize()
        self.validate()
        return self.execute()


def get_subcommands(parser):

    subparsers = parser.add_subparsers(title="commands", metavar='<command>',
                                       dest='subcommand')

    subcommands = _find_actions(subparsers, os.path.dirname(__file__))

    parser.set_defaults(subcommands=subcommands)

    return subcommands


# partially taken from python-keystoneclient
def _find_actions(subparsers, module_path):
    subcommands = {}
    for mod in (p[:-len('.py')] for p in os.listdir(module_path) if
                p.endswith('.py')):
        __import__(__name__ + '.' + mod)

    for cmd_class in GitUpstreamCommand.__subclasses__():
        command = cmd_class.name
        desc = cmd_class.__doc__ or ''

        parser_kwargs = {
            'help': desc.strip().split('\n')[0],
            'description': desc,
        }

        if cmd_class.usage:
            parser_kwargs['usage'] = textwrap.dedent(cmd_class.usage)

        subparser = subparsers.add_parser(command, **parser_kwargs)
        subparser.register('action', 'append_replace', AppendReplaceAction)
        subparser.set_defaults(cmd=cmd_class(subparser))
        subcommands[command] = subparser

    return subcommands
