import pytest

from articlenizer import sentenize
from articlenizer.util import apply_regex_list

def test_string_normalization():
    s = '  This is    a test for  string normalization in    \n  all cases. '
    s = apply_regex_list(s, sentenize.NORM_REGEX)
    assert s == 'This is a test for string normalization in\nall cases.'

def test_split():
    s = 'This. should? be83 split2! on multip!e occ@s.ons but not. inside words.'
    offsets = [o for o in sentenize._boundary_gen(s, sentenize.SPLIT_REGEX)]
    s = '\n'.join((s[o[0]:o[1]] for o in offsets))
    assert s == 'This.\nshould?\nbe83 split2!\non multip!e occ@s.ons but not.\ninside words.'

def test_refined_split():
    s = 'The refined split shoud do even more.For example find "errors".'
    s = apply_regex_list(s, sentenize.REFINED_SPLIT_REGEX)
    assert s == 'The refined split shoud do even more.\nFor example find "errors".'

def test_subsentence_recognition():
    s = 'There should be no splits (even with stuff like this.\nBut well..).'
    s = apply_regex_list(s, sentenize.SUBSENTENCE_REGEX)
    assert s == 'There should be no splits (even with stuff like this. But well..).'

def test_recombination():
    s = 'Lets assume\nthere are splits.\nwhile there approx.\nshould be zero, e.\ng.\nBecause of abbreviations or Fig.\n5. As said by Test et al.\n[56].'
    s = apply_regex_list(s, sentenize.RECOMBINE_REGEX)
    assert s == 'Lets assume there are splits. while there approx. should be zero, e. g. Because of abbreviations or Fig. 5. As said by Test et al. [56].'

def test_split_enumerations():
    s = 'Something quite annoying: (1) Enumerations are sometimes used as standalone sentences; (2) This is a case in which we want to split them of.'
    s = apply_regex_list(s, sentenize.SPLIT_ENUM_REGEX)
    assert s == 'Something quite annoying:\n(1) Enumerations are sometimes used as standalone sentences;\n(2) This is a case in which we want to split them of.'

def test_formtok_split():
    s = 'Strings should be split after a formtok When the next sentence starts with a upper case letter.'
    s = apply_regex_list(s, sentenize.REFINED_SPLIT_REGEX)
    assert s == 'Strings should be split after a formtok\nWhen the next sentence starts with a upper case letter.'

def test_application():
    s = 'Logistic regression analysis was performed with SAS 8. 0. P<0.05 were considered statistically significant.'
    s = sentenize.sentenize(s)
    assert s == 'Logistic regression analysis was performed with SAS 8. 0.\nP<0.05 were considered statistically significant.'

def test_normalize():
    s = 'Stimuli were displayed on a 21 inch CRT monitor (refresh rate  = 120 Hz) using MatLab (7.1 version) software.'
    s, replacements = sentenize.normalize(s)
    assert s == 'Stimuli were displayed on a 21 inch CRT monitor (refresh rate = 120 Hz) using MatLab (7.1 version) software.'
