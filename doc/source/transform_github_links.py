# based on the idea from
# https://github.com/andsens/bootstrap-vz/blob/5250f8233215f6f2e3a571be2f5cf3e09accd4b6/docs/transform_github_links.py
#
# Copyright 2013-2014 Anders Ingemann <anders@ingemann.de>
# Copyright 2016 Darragh Bailey <dbailey@hpe.com>


from docutils import nodes
import os.path


def transform_github_links(app, doctree, fromdocname):
    """Convert file referencs for github to correct target

    Scans the doctree for links directly referencing ReSTructured
    text documents within this repository. It converts these links
    to a suitable target for sphinx generated docs.

    Such references as <file>.rst are used by source code hosting
    sites such as GitHub when rendering documents directly from
    individual source files without parsing the entire doctree.

    However referencing the original <file>.rst is not useful for
    sphinx generated documentation as <file>.rst will not exist in
    the resulting documentation as it will also have been converted
    to the chosen format e.g. <file>.html

    Supporting automatic conversion ensures that GitHub/BitBucket
    and any other git hosting site performing rendering on a file
    by file basis can allow users to navigate through the
    documentation, while still ensuring the output from fully
    generated sphinx docs will point to the correct target.
    """

    try:
        target_format = app.builder.link_suffix
    except AttributeError:
        # if the builder has no link_suffix, then no need to modify
        # the current links.
        return

    source_suffix = app.config.source_suffix
    # Links are either absolute against the repository or relative to
    # the current document's directory. Note that this is not
    # necessarily app.srcdir, which is the documentation root
    # directory.
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

        # Replace the suffix with the correct target format file ending,
        # but only if the link ends with both the correct source suffix
        # and refers to a local file.
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
