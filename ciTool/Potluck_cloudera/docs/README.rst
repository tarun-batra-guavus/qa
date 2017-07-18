Generate docs
=============

The raw documentation is stored in `docs/source` directory. Execute the following commands to create html documentation:

    cd docs

    # Update the docs with the new/updated testcases
    ./update_testcase_docs.py

    # Generate HTML files
    make html

This will process the documents in `source` directory and create html files in `build` directory
