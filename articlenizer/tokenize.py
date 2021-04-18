import re

# TODO numbers such as 10,000 and stuff such as R&D
TOKENIZATION_REGEX = re.compile(r'((?:10.1371.journal.[a-z]+.[a-z0-9\.]+)|https?\:\/\/[a-zA-Z0-9\-\.]+[\w\/\._\-\:~\?=#%]*[\w\/_\-\:~\?=#%]|ftp\:\/\/[a-zA-Z0-9\-\.]+[\w\/\._\-\:~\?=#%]*[\w\/_\-\:~\?=#%]|www\.[a-zA-Z0-9\-\.]+[\w\/\._\-\:~\?=#%]*|[a-zA-Z0-9\-\.]+\.org\/[\w\/_\-\:~\?=#%]*|[a-zA-Z0-9\-\.]+\.edu\/[\w\/_\-\:~\?=#%]*|[\.0-9]+[0-9][a-zA-Z]+|v\.|ver\.|V\.|Ver\.|e\.g\.|i\.e\.|i\.v\.|[0-9]{1,3},[0-9]{3},[0-9]{3}|[0-9]{1,3},[0-9]{3}|\[[0-9\-,\?]+\]|[0-9\.]*\.[0-9]+[a-zA-Z]*|[\.0-9]+[a-zA-Z]+|[a-qs-uw-zA-QS-UW-Z]+[0-9][a-zA-Z]+|[a-qs-uw-zA-QS-UW-Z][0-9]+[a-zA-Z]?|[a-zA-Z]+&[a-zA-Z]+|[a-zA-Z]+\.[a-zA-Z]+|[a-zA-Z]+|[0-9]+|[^0-9a-zA-Z\s])')

def tokenize(line):
    """Tokenize a string based on a regular expression

    Args:
        line (string): string to tokenize

    Returns:
        list of string: list of individual tokens
    """
    return [t for t in TOKENIZATION_REGEX.split(line) if t]