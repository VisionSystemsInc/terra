# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.environ['TERRA_CWD']))
sys.path.insert(0, os.path.abspath(os.path.join(os.environ['VSI_COMMON_DIR'],
                                                'python')))
sys.path.append(os.path.abspath("./_ext"))
# Disable logging from fully initializing. It's just a mess we don't need
os.environ['TERRA_UNITTEST']='1'

temp = tempfile.NamedTemporaryFile(mode='w')
temp.write('{}')
temp.flush()

# Don't load terra here, it'll mess up the monkey patching sphinx does
os.environ['TERRA_SETTINGS_FILE']=temp.name

# -- Project information -----------------------------------------------------

project = 'Terra'
copyright = '2020, VSI'
author = 'VSI'

# The short X.Y version
version = ''
# The full version, including alpha/beta/rc tags
release = '0.0.1'


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.napoleon',
    'sphinx.ext.mathjax',
    'sphinx.ext.intersphinx',
    'vsi_domains',
    'celerydocs'
]

# Link to other documentation (e.g., numpy, python, terra, etc.)
intersphinx_mapping = {
    'python': ('https://docs.python.org/3.6', None),
    'vsi_common': ('https://visionsystemsinc.github.io/vsi_common/', None),
    'celery': ('https://docs.celeryproject.org/en/stable/', None),
    'filelock': ('https://filelock.readthedocs.io/en/latest/', None)
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
source_suffix = ['.rst', '.md']
# source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None

# Napoleon parameters
napoleon_google_docstring = False
napoleon_use_param = True
napoleon_use_ivar = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True

# Autodoc parameters

autodoc_mock_imports = [
    "terra._terra",
    "yaml",
    "celery",
]

nitpick_ignore = [
    ('py:class', 'vsi.tools.python.BasicDecorator'),
    ('py:mod',   'django.conf'),
    ('py:class', 'django.db.utils.ConnectionHandler'),
    ('py:class', 'json.encoder.JSONEncoder'),
    ('py:class', '_thread._local'),
    ('py:class', 'concurrent.futures._base.Executor'),
    ('py:class', 'concurrent.futures._base.Future'),
    ('py:class', 'concurrent.futures.process.ProcessPoolExecutor'),
    ('py:class', 'concurrent.futures.thread.ThreadPoolExecutor'),
    ('py:class', 'argparse._AppendAction'),
    ('py:data',  'logging.DEBUG'),
    ('py:data',  'logging.WARNING'),
    # Since I'm not including 'celery.contrib.sphinx' yet
    # https://stackoverflow.com/questions/33416296/sphinx-not-autodocumenting-decorated-celery-tasks
    ('py:class', 'celery.app.task.')
]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'


# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'Terradoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'Terra.tex', 'Terra Documentation',
     'VSI', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'terra', 'Terra Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'Terra', 'Terra Documentation',
     author, 'Terra', 'One line description of project.',
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


# -- Extension configuration -------------------------------------------------

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True