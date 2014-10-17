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

import argparse
import os
import sys


class AppendReplaceAction(argparse._AppendAction):
    """Allows setting of a default value which is overriden by the first use
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


def get_subcommands(subparsers):

    subcommands = _find_actions(subparsers, os.path.dirname(__file__))

    return subcommands


# partially taken from python-keystoneclient
def _find_actions(subparsers, module_path):
    subcommands = {}
    for mod in (p[:-len('.py')] for p in os.listdir(module_path) if
                p.endswith('.py')):
        __import__(__name__ + '.' + mod)
        module = sys.modules[__name__ + '.' + mod]
        for attr in (a for a in dir(module) if a.startswith('do_')):
            command = attr[3:].replace('_', '-')
            func = getattr(module, attr)
            desc = func.__doc__ or ''
            help = desc.strip().split('\n')[0]
            args = getattr(func, 'arguments', [])

            subparser = subparsers.add_parser(
                command,
                help=help,
                description=desc)
            subparser.register('action', 'append_replace', AppendReplaceAction)

            for (args, kwargs) in args:
                subparser.add_argument(*args, **kwargs)
            subparser.set_defaults(func=func)
            subcommands[command] = subparser

    return subcommands
