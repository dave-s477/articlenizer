import re
import unicodedata

from articlenizer import ABBREVIATIONS
from articlenizer.util import apply_regex_list
from articlenizer.sentenize import _boundary_gen

CORRECTION_REGEX = []

# )word -> ) word and word;word -> word; word
CORRECTION_REGEX.append((re.compile(r'(?P<bracket>[\)\]])(?P<text>[A-Za-z]{2,})'), r'\g<bracket> \g<text>')) 
CORRECTION_REGEX.append((re.compile(r'(?P<text>\s[A-Za-z]{3,})(?P<bracket>[\(\[])'), r'\g<text> \g<bracket>')) 
CORRECTION_REGEX.append((re.compile(r'(?P<text>,)(?P<bracket>[\(\[])'), r'\g<text> \g<bracket>')) 
CORRECTION_REGEX.append((re.compile(r'(?P<semi_colon>[^\s]+;)(?P<any>[^\s])'), r'\g<semi_colon> \g<any>'))

MATH_EXPRESSION = re.compile(r'[^\s]+[^\.\!\?,;\s]\s') 
# word;word -> word; word

BASE_MATH_CHARS = ['+', '-', '/', '*']

WRONG_CITATION = re.compile(r'[^\]](?P<dot>[\.,])(?P<middle> ?)(?P<citation>\[[0-9\-,\?]+\])(?P<end>$|[^\.])')

abbr = re.compile(r'|'.join(ABBREVIATIONS))

def remove_math_expr(s):
    """Replace mathematical formulas by the placeholder 'formtok'.
    A (restrictive) heuristic is used in order to determine what counts as a formula. 

    Args:
        s (string): string to transform

    Returns:
        string: transformed string
    """
    potential_tokens = [o for o in _boundary_gen(s, MATH_EXPRESSION)]
    list_to_replace = []
    for o in potential_tokens:
        cs = s[o[0]:o[1]]
        if '°' in cs or '×' in cs:
            continue

        alphas = 0
        digits = 0
        unmatched = 0
        math_chars = 0 
        greek_letters = 0
        for char in cs:
            if char.isdigit():
                digits += 1
            elif char.isalpha():
                alphas += 1
            elif char in BASE_MATH_CHARS:
                pass
            elif unicodedata.category(char) == 'Sm':
                math_chars += 1
            elif ( ord(char) >= 945 and ord(char) <= 970 ) or ( ord(char) >= 913 and ord(char) <= 938 ):
                greek_letters += 1
            else:
                unmatched += 1

        if ( math_chars >= 2 and alphas >= 1 ) or ( math_chars >= 1 and greek_letters >= 1 ):
            matched = True
            left_error = False
            left_break = False
            right_error = False
            right_break = False
            for i in range(len(cs)):
                left = cs[i]
                if left in ['(', '{']:
                    left_break = True
                elif left in [')', '}'] and not left_break:
                    left_error = True

                right = cs[-(i+1)]
                if right in ['}', ')']:
                    right_break = True
                elif right in ['(', '{'] and not right_break:
                    right_error = True

            if not left_error and not right_error:
                list_to_replace.append([cs, 'formtok ', o[0], o[1]])
    
    for replacement in list_to_replace:
        s = s.replace(replacement[0], replacement[1])
        
    return s, reversed(list_to_replace)

def correct(s):
    """Correct a string

    Args:
        s (string): string to correct

    Returns:
        string: corrected string
    """
    s = apply_regex_list(s, CORRECTION_REGEX)

    return s

def correct_with_index(s):
    """Correct a string but remember at what position a change is made

    Args:
        s (string): string to correct

    Returns:
        string, positions: corrected string
    """
    indices = []
    for r, t in CORRECTION_REGEX:
        regex_matches = r.finditer(s)
        for match in reversed(list(regex_matches)):
            ind = match.span(2)[0]
            s = s[:ind] + ' ' + s[ind:]
            indices.append(ind-1)
    return s, reversed(indices)

def correct_citations(s):
    """Correct citations of the form ... as in. [5] -> ... as in [5].

    Args:
        s (string): plain article string

    Returns:
        string: transformed string
    """
    switches = []
    matches = WRONG_CITATION.finditer(s)
    for match in matches:
        indices = match.span(0)
        left_context = ''
        if indices[0] > 4:
            left_context = s[indices[0]-5:indices[0]+2]
        if left_context and abbr.search(left_context):
            pass
        else:
            s = s[:match.span("dot")[0]] + match.group("middle") + match.group("citation")+ match.group("dot") + match.group("end") + s[match.span("end")[1]:]
            switches.append([match.span("dot"), (match.span("middle")[0], match.span("citation")[1])])
            
    return s, switches