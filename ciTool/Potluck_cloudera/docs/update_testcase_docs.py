#!/usr/bin/env python
"""
.. moduleauthor:: Sandeep Nanda <sandeep.nanda@guavus.com>

Recursively iterate the testcases directory and update the docs
with the docstring of each testcase
"""
import os
import sys
from fnmatch import filter as fnfilter
import ast

DOCS_DIR = os.path.abspath(os.path.dirname(__file__))
TC_DOCS_DIR = os.path.join(DOCS_DIR, "source", "testcases")
SRC_DIR = os.path.join(os.path.dirname(DOCS_DIR), "src")
sys.path.append(SRC_DIR)

DocFormat = """
%(TcId)s
**************************************************************

%(TcDocString)s

Source
======
::

    %(TcSource)s
"""

CategoryDocFormat = """%(title)s
**************************************************************

.. toctree::
    :glob:
    :maxdepth: 2

    */index
    *
"""
SubcatDocFormat = """%(title)s
**************************************************************

.. toctree::
    :glob:

    **
"""
def main():
    from settings import SCRIPTS_DIR
    from os.path import join as path_join
    for dirpath, dirnames, filenames in os.walk(SCRIPTS_DIR):
        for filepath, filename in ((path_join(dirpath, name), name) for name in fnfilter(filenames, "[!_]*.py")):
            relative_filepath = os.path.relpath(filepath, SCRIPTS_DIR)

            with open(filepath) as fh:
                file_contents = fh.read()

            try:
                node = ast.parse(file_contents)
            except:
                print("Error while parsing file %s" % filepath)
                continue
            doc_string = ast.get_docstring(node)
            if doc_string:
                tc_doc_path = path_join(TC_DOCS_DIR, relative_filepath).replace(".py", ".rst")
                tc_doc_dir = os.path.dirname(tc_doc_path)

                print("Updating docs for %s" % tc_doc_path)
                if not os.path.exists(tc_doc_dir):
                    os.makedirs(tc_doc_dir)

                # Make the category index, if required
                splitted_path = relative_filepath.split(os.sep)
                category = splitted_path[0]
                category_file = path_join(TC_DOCS_DIR, category, "index.rst")
                with open(category_file, "w") as fh:
                    fh.write(CategoryDocFormat % {"title" : category.title()})
                    del splitted_path [0]

                if (splitted_path) > 1:
                    subcat = splitted_path[0]
                    subcat_file = path_join(TC_DOCS_DIR, category, subcat, "index.rst")
                    with open(subcat_file, "w") as fh:
                        fh.write(SubcatDocFormat % {"title" : subcat.title()})
                        del splitted_path [0]

                # Write the testcase docs
                DocDetails = {
                    "TcId" : "/ ".join(splitted_path).replace("_", " ").replace(".py", "").title(),
                    "TcDocString" : doc_string,
                    "TcSource" : file_contents.replace(doc_string, "Source").replace("\n", "\n    "),
                }
                with open(tc_doc_path, "w") as fh:
                    fh.write(DocFormat % DocDetails)



if __name__ == "__main__":
    main()
