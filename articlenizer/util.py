import argparse

def apply_regex_list(s, regex):
    """Substitute list of given regex in a string

    Args:
        s (string): string in which subsitutions are made
        regex (list):  tuples of regular expressions and replacements

    Returns:
        string: transformed string
    """
    for r, t in regex:
        s = r.sub(t, s)
    return s

def chunk_list(seq, num):
    """Divide a list in num equal chunks

    Args:
        seq (list): elements to chunk
        num (int): number of chunks

    Returns:
        list of lists: list of chunks
    """
    avg = len(seq) / float(num)
    out = []
    last = 0.0
    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg
    return out

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'True', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'False', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
    