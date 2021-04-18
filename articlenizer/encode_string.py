import re
import string
import unicodedata

from pathlib import Path
from collections import Counter

from articlenizer import sentenize

def handle_unicode_characters(s):
    """Handle unicode characters appearing in string. Some do actually contain valuable information for NLP applications. But there is also a lot of "unnecessary" unicode in scientific texts (at least from an Software-NER perspective). It can either be dropped, or different codes can be summarized by one characters. 

    Args:
        s (string): string to transform

    Returns:
        string: unicode 'normalized' string
    """
    dropped_char_indices = []
    running_count = 0
    out_s = ''
    for char in s:
        if re.match(r"[A-Za-z0-9\s]", char) is not None or char in string.punctuation:
            # keep "normal" chars
            out_s += char
            running_count += 1
        else:
            # here we will deal with unicode
            if char in ['©', '™', '®']:
                # 'TradeMarks' are tricky but often used to indicate external equipment in studies
                out_s += '™'
                running_count += 1
                continue

            if char == '°':
                # Temperatures are almost always indicated by °
                out_s += char
                running_count += 1
                continue

            # some unicodes are combined and based on 'normal' characters -> we want to keep the base characters, e.g. á -> a
            unicode_matched = False
            #char_
            u_map = unicodedata.decomposition(char)
            if u_map and len(u_map) > 1:
                split_codes = [code for code in u_map.split() if not re.match(r'<.*>', code)]
                for code in split_codes:
                    code_char = chr(int(code, 16))
                    if re.match(r'[a-zA-Z]', code_char):
                        out_s += code_char # TODO
                        unicode_matched = True
                        running_count += 1
                        break
            if unicode_matched: 
                continue

            # normalized unicode for everything else just to be save.. 
            char = unicodedata.normalize('NFC', char)

            if len(char) > 1:
                print(RuntimeWarning("Unkown unicode character with length > 1: {} -- ignored".format(char)))
                continue

            # we want to keep basic greek letters no matter what
            if char == 'µ': # yes, they are actually different: this is the 'micro sign'
                char = 'μ' # this the greek letter..
            if ( ord(char) >= 945 and ord(char) <= 970 ) or ( ord(char) >= 913 and ord(char) <= 938 ):
                out_s += char
                running_count += 1
                continue

            # the rest is based on unicode categories some of which are considered important and others are not
            category = unicodedata.category(char)
            if category == 'Pi':
                if  ord(char) == 8216 or ord(char) == 8219:
                    out_s += char
                else:
                    out_s += '“'
                running_count += 1
            elif category == 'Pf':
                if ord(char) == 8217:
                    out_s += '’'
                else:
                    out_s += '”'
                running_count += 1
            elif category == 'Pd':
                char = '-'
                out_s += char
                running_count += 1
            elif category == 'Sc':
                out_s += char
                running_count += 1
            elif category in ['Pe', 'Cf', 'Ps', 'So', 'Sk', 'No']:
                dropped_char_indices.append([running_count, char])
                running_count += 1
            elif category == 'Lm':
                if ord(char) >= 697 and ord(char) <= 719:
                    char ="'"
                    running_count += 1
                    out_s += char
            elif category in ['Lu', 'Ll', 'Po']:
                # keep
                out_s += char
                running_count += 1
            elif category == 'Sm':
                # Mathsymbols, TODO: handle them better?
                out_s += char
                running_count += 1
                unicode_in_sent = True
            else:
                #print("Encountered an unhandled unicode character: {} - DROPPED".format(char))
                dropped_char_indices.append([running_count, char])
                running_count += 1
    
    return out_s, dropped_char_indices
