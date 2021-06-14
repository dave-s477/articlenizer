"""Based structure of the sentence splitter was adapted from the implemention 
in BRAT (https://brat.nlplab.org/) that is in turn based on GeniaSS 
(http://www.nactem.ac.uk/y-matsu/geniass/)
"""

import re

from pathlib import Path

from articlenizer.util import apply_regex_list
from articlenizer import ABBREVIATIONS

# remove leading and trailing spaces for all lines to get rid of potential confusion.
NORM_REGEX = []
NORM_REGEX.append((re.compile(r'\n(?P<leading_spaces>\s+)'), '\n'))
NORM_REGEX.append((re.compile(r'^(?P<leading_spaces> +)'), ''))
NORM_REGEX.append((re.compile(r'^(?P<leading_newlines>\n+)'), ''))
NORM_REGEX.append((re.compile(r'(?P<trailing_spaces> +)$'), ''))
NORM_REGEX.append((re.compile(r'(?P<leading_spaces> +)\n'), '\n'))
NORM_REGEX.append((re.compile(r'\n(?P<trailing_spaces> +)'), '\n'))
NORM_REGEX.append((re.compile(r'(?P<multi_spaces>[ \u200a]{2,})'), ' '))
NORM_REGEX.append((re.compile(r'(?P<multi_newline>\n{2,})'), '\n'))

# regex to split everything there is to split on ".!?" (but not on "Word.Word")
SPLIT_REGEX = re.compile(r'\S.*?(:?(:?(\.|!|\?|。|！|？)+(?=\s+))|(:?(?=\n+))|(:?(?=\s*$)))')

# splitter assumes new lines as sentence splits. Here new lines are added between costructions that are likely to indicate new sentences. 
REFINED_SPLIT_REGEX_KEEP_LENGTH = []
REFINED_SPLIT_REGEX_KEEP_LENGTH.append( # add "save" cases that capture stuff such as: "word.word" "232.word" "word).Next"
    (
        re.compile(r'(?P<first_sentence_element> ([A-Za-z\(\)\[\]]+|[\d\(\)\[\]]+) ?[\?\!\.]) (?P<second_sentence_element>[A-Za-z]+ )'), # regex
        r'\g<first_sentence_element>\n\g<second_sentence_element>') # replacement (based on original input)
    ) 
REFINED_SPLIT_REGEX_KEEP_LENGTH.append( 
    (
        re.compile(r'(?P<first_sentence_element> ([A-Za-z\(\)\[\]]+|[\d\(\)\[\]]+) ?[\?\!\.][«”❞’"]) (?P<second_sentence_element>[A-Za-z]+ )'), 
        r'\g<first_sentence_element>\n\g<second_sentence_element>') 
    ) 
REFINED_SPLIT_REGEX_KEEP_LENGTH.append( 
    (
        re.compile(r'(?P<first_sentence_element> formtok) (?P<second_sentence_element>[A-Z][a-z]+ )'), 
        r'\g<first_sentence_element>\n\g<second_sentence_element>') 
    ) 
# TODO: add more cases?

REFINED_SPLIT_REGEX_CHANGE_LENGTH = []
REFINED_SPLIT_REGEX_CHANGE_LENGTH.append( # add "save" cases that capture stuff such as: "word.word" "232.word" "word).Next"
    (
        re.compile(r'(?P<first_sentence_element> ([A-Za-z\(\)\[\]]{2,}|[\d\(\)\[\]]+) ?[\?\!\.])(?P<second_sentence_element>[A-HJ-UWYZ][a-z]+ )'), # regex
        r'\g<first_sentence_element>\n\g<second_sentence_element>') # replacement (based on original input)
    )
REFINED_SPLIT_REGEX_CHANGE_LENGTH.append( 
    (
        re.compile(r'(?P<first_sentence_element> ([A-Za-z\(\)\[\]]{2,}|[\d\(\)\[\]]+) ?[\?\!\.][«”❞’"])(?P<second_sentence_element>[A-HJ-UWYZ][a-z]+ )'), 
        r'\g<first_sentence_element>\n\g<second_sentence_element>') 
    ) 

REFINED_SPLIT_REGEX = REFINED_SPLIT_REGEX_KEEP_LENGTH + REFINED_SPLIT_REGEX_CHANGE_LENGTH

# go in the reverse direction and check for cases where splits are wrong, e.g. when brackets are opened, and only closed on a new line. 
SUBSENTENCE_REGEX = []
SUBSENTENCE_REGEX.append((re.compile(r'(?P<open>\([^\[\]\(\)]*)\n(?P<close>[^\[\]\(\)]*\))'), r'\g<open> \g<close>')) # round bracket - no square inbetween
SUBSENTENCE_REGEX.append((re.compile(r'(?P<open>\[[^\[\]\(\)]*)\n(?P<close>[^\[\]\(\)]*\])'), r'\g<open> \g<close>')) # square bracket - no round inbetween
SUBSENTENCE_REGEX.append((re.compile(r'(?P<open>\([^\(\)]{0,250})\n(?P<close>[^\(\)]{0,250}\))'), r'\g<open> \g<close>')) # round within 250 chars
SUBSENTENCE_REGEX.append((re.compile(r'(?P<open>\[[^\[\]]{0,250})\n(?P<close>[^\[\]]{0,250}\])'), r'\g<open> \g<close>')) # square within 250 chars
SUBSENTENCE_REGEX.append((re.compile(r'(?P<open>\((?:[^\(\)]|\([^\(\)]*\)){0,250})\n(?P<close>(?:[^\(\)]|\([^\(\)]*\)){0,250}\))'), r'\g<open> \g<close>')) # round nested
SUBSENTENCE_REGEX.append((re.compile(r'(?P<open>\[(?:[^\[\]]|\[[^\[\]]*\]){0,250})\n(?P<close>(?:[^\[\]]|\[[^\[\]]*\]){0,250}\])'), r'\g<open> \g<close>')) # square nested
SUBSENTENCE_REGEX.append((re.compile(r'(?P<open>[»“❝‘"][^»“❝‘"«”❞’"]{0,250})\n(?P<close>[^\(\)]{0,250}[«”❞’"])'), r'\g<open> \g<close>')) # quotations within 250 chars

# take back even more splits that are not desired
RECOMBINE_REGEX = []
RECOMBINE_REGEX.append((re.compile(r'[\.\,]\n(?P<normal_word>[a-z]{2}[a-z-]*[ \.\:\,\;])'), r'. \g<normal_word>')) # sentence cannot start with a "normal" lowercase word.
RECOMBINE_REGEX.append((re.compile(r'(?P<abbr>\b[A-Z]\.)\n(?P<name>[a-z]{3,}\b)'), r'\g<abbr> \g<name>')) # names such as: "S. cerevisiae"
RECOMBINE_REGEX.append((re.compile(r'(?P<word1>\s[a-z]{2,})\n(?P<word2>[a-z]{2,}\s)'), r'\g<word1> \g<word2>')) # recombine very "save", "weird" cases e.g. we performed\ntests.
RECOMBINE_REGEX.append((re.compile(r'(?P<word1>\s[A-Z][a-z]{1,})\n(?P<word2>[a-z]{2,}\s)'), r'\g<word1> \g<word2>')) # recombine very "save", "weird" cases e.g. we performed\ntests.
RECOMBINE_REGEX.append((re.compile(r'(?P<word1>\s[a-z]{2,})\n(?P<word2>http.+?\s)'), r'\g<word1> \g<word2>')) # url..
RECOMBINE_REGEX.append((re.compile(r'(?P<word1>\s[A-Z][a-z]{1,})\n(?P<word2>http.+?\s)'), r'\g<word1> \g<word2>')) # url..
RECOMBINE_REGEX.append( # names such as "Anton P. Chekhov", "A. P. Chekhov"
    (
        re.compile(r'(?P<given_names>\b(?:[A-Z]\.|[A-Z][a-z]{2,}) [A-Z]\.)\n(?P<surname>[A-Z][a-z]+\b)'),
        r'\g<given_names> \g<surname>')
    )
RECOMBINE_REGEX.append((re.compile(r'\n(?P<word_list>(?:and|or|but|nor|yet|of|in|by|as|on|at|to|via|for|with|that|than|from|into|upon|after|while|during|within|through|between|whereas|whether) )'), r' \g<word_list>')) # a number of words where there should not be an accidental split.
RECOMBINE_REGEX.append((re.compile(r'(?P<t1>\b[ei]\.)\n(?P<t2>[gev]\.\,?)'), r'\g<t1> \g<t2>')) #specific abbreviations
RECOMBINE_REGEX.append( # more abbreviations
    (
        re.compile(r'(?P<abbr> (' + r'|'.join(ABBREVIATIONS) + r'))\n'),
        r'\g<abbr> ')
    )
RECOMBINE_REGEX.append( # still more abbreviations
    (re.compile(r'(?P<abbr>\b([Aa]pprox\.|[Nn]o\.|[Ff]igs?\.|[Tt]bls?\.|[Ee]qs?\.))\n(?P<number>\d+)'), r'\g<abbr> \g<number>'))
RECOMBINE_REGEX.append((re.compile(r'(\.\s*)\n(\s*,)'), r'\1 \2')) # commas
RECOMBINE_REGEX.append((re.compile(r'\n(?P<t1>\(.{0,250}\))'), r' \g<t1>')) #specific abbreviations
RECOMBINE_REGEX.append((re.compile(r'(?P<t0>\d{1,4}\.?)\n(?P<t1>\d{1,4}\.)'), r'\g<t0> \g<t1>')) 
RECOMBINE_REGEX.append((re.compile(r'\n(?P<t1>\[[0-9\-,\?]+\])'), r' \g<t1>')) 
RECOMBINE_REGEX.append((re.compile(r'(?P<t1>\d{1,2}\.)\n(?P<t2>[12]\d{3})'), r'\g<t1> \g<t2>')) 


SPLIT_ENUM_REGEX_KEEP_LENGTH = []
SPLIT_ENUM_REGEX_KEEP_LENGTH.append((re.compile(r'(?P<leading>[\)\.,;:\d]) (?P<enum>\([A-Z0-9]\)) (?P<next>[A-Z][a-z]+)'), r'\g<leading>\n\g<enum> \g<next>')) # commas

SPLIT_ENUM_REGEX_CHANGE_LENGTH = []
SPLIT_ENUM_REGEX_CHANGE_LENGTH.append((re.compile(r'(?P<leading>[\)\.,;:\d])(?P<enum>\([A-Z0-9]\)) (?P<next>[A-Z][a-z]+)'), r'\g<leading>\n\g<enum> \g<next>')) # commas

SPLIT_ENUM_REGEX = SPLIT_ENUM_REGEX_KEEP_LENGTH + SPLIT_ENUM_REGEX_CHANGE_LENGTH

def _boundary_gen(text, regex):
    for match in regex.finditer(text):
        yield match.span()

def sentenize(s):
    """Sentenizes a string

    Args:
        s (string): string to sentenize

    Returns:
        string: sentenized string
    """
    s = apply_regex_list(s, NORM_REGEX)
    offsets = [o for o in _boundary_gen(s, SPLIT_REGEX)]
    s = '\n'.join((s[o[0]:o[1]] for o in offsets))
    s = apply_regex_list(s, REFINED_SPLIT_REGEX)
    s = apply_regex_list(s, SUBSENTENCE_REGEX)
    s = apply_regex_list(s, RECOMBINE_REGEX)
    s = apply_regex_list(s, SPLIT_ENUM_REGEX)

    return s

def sentenize_with_index(s):
    """Sentenizes a string but remember at what position a change is made

    Args:
        s (string): string to sentenize

    Returns:
        string, positions: corrected string
    """
    indices = []
    offsets = [o for o in _boundary_gen(s, SPLIT_REGEX)]
    s = '\n'.join((s[o[0]:o[1]] for o in offsets))
    for r, t in REFINED_SPLIT_REGEX_CHANGE_LENGTH:
        regex_matches = r.finditer(s)
        for match in reversed(list(regex_matches)):
            indices.append(match.span(1)[1])
    s = apply_regex_list(s, REFINED_SPLIT_REGEX_CHANGE_LENGTH)
    s = apply_regex_list(s, REFINED_SPLIT_REGEX_KEEP_LENGTH)
    s = apply_regex_list(s, SUBSENTENCE_REGEX)
    s = apply_regex_list(s, RECOMBINE_REGEX)
    s = apply_regex_list(s, SPLIT_ENUM_REGEX_KEEP_LENGTH)
    for r, t in SPLIT_ENUM_REGEX_CHANGE_LENGTH:
        regex_matches = r.finditer(s)
        for match in reversed(list(regex_matches)):
            indices.append(match.span(1)[1])
    s = apply_regex_list(s, SPLIT_ENUM_REGEX_CHANGE_LENGTH)
    return s, indices

def normalize(s):
    """Whitespace normalize a string

    Args:
        s (string): string to normalize

    Returns:
        string: whitespace normalized string
    """
    replacement_length = []
    for r, t in NORM_REGEX:
        regex_matches = r.finditer(s)
        for match in reversed(list(regex_matches)):
            s = s[:match.span(0)[0]] + t + s[match.span(0)[1]:]
            replacement_length.append([match.group(0), t, match.span(0)[0], match.span(0)[1]])
    return s, replacement_length
