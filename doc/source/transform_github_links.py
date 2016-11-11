# based on the idea from
# https://github.com/andsens/bootstrap-vz/blob/5250f8233215f6f2e3a571be2f5cf3e09accd4b6/docs/transform_github_links.py
#
# Copyright 2013-2014 Anders Ingemann <anders@ingemann.de>
# Copyright 2016 Darragh Bailey <dbailey@hpe.com>


from docutils import nodes
import os.path


def transform_github_links(app, doctree, fromdocname):
    # Convert relative links in repo document source tree directly to
    # source ReSTructured text documents to links the resulting
    # document type according to the builder as this allows linking
    # within the source tree to work correctly for GitHub, while
    # converting the links correctly for the sphinx generated output.

    try:
        target_format = app.builder.link_suffix
    except AttributeError:
        # if the builder has no link_suffix, then no need to modify
        # the current links and allow it to check
        return

    source_suffix = app.config.source_suffix
    # app.srcdir is the source directory of the docs, but it's more
    # important to have the source directory of the current document
    # the doctree is coming from as links are either relative to
    # it's path or absolute.
    doc_path = doctree.attributes['source']
    doc_dir = os.path.dirname(doc_path)

    for node in doctree.traverse(nodes.reference):
        if 'refuri' not in node:
            continue
        if node['refuri'].startswith('http'):
            continue

        try:
            link, anchor = node['refuri'].split('#', 1)
            anchor = '#' + anchor
        except ValueError:
            link = node['refuri']
            anchor = ''

        if link is None:
            continue

        # only if ending with source file suffix and referencing a local file
        # perform the replacement removing the suffix and adding the correct
        # format ending
        if link.endswith(source_suffix):
            # absolute paths are considered relative to repo
            if link.startswith("/"):
                basepath = ""
            # relative paths are against the current doctree source path
            else:
                basepath = doc_dir
            if os.path.exists(os.path.join(basepath, link)):
                node['refuri'] = (link[:-len(source_suffix)] + target_format +
                                  anchor)


def setup(app):
    app.connect('doctree-resolved', transform_github_links)
    return {'version': '0.1'}
