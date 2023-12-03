"""
Description: 
"""

#   - - - - - Imports - - - - -   #


#   - - - - - Constants - - - - -   #


#   - - - - - Classes - - - - -   #

# Database file exceptions

class DataBaseFileNotFound(Exception):
    ...


class DataBaseFileContentInvalid(Exception):
    ...


class DataBaseFileTrailerIsNotValid(Exception):
    ...

# File system manager exceptions

#   - - - - - Functions - - - - -   #
