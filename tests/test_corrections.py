import pytest

from articlenizer import corrections
from articlenizer.util import apply_regex_list

def test_bracket_correction():
    s = 'Testing errors(performed with brackets)in order to make sure they do not happen'
    s = apply_regex_list(s, corrections.CORRECTION_REGEX)
    assert s == 'Testing errors (performed with brackets) in order to make sure they do not happen'

def test_semi_colon_correction():
    s = 'Errors with semi colons;they can happen;but are easy to correct.'
    s = apply_regex_list(s, corrections.CORRECTION_REGEX)
    assert s == 'Errors with semi colons; they can happen; but are easy to correct.'

def test_formula_replacement():
    s = 'Formulas such as GFP=(∑(v(t)−V(t)2/n)1/2(1) or (h)=∑j=1qSSj should be replaced with the formtok placeholder.'
    s, _ = corrections.remove_math_expr(s)
    assert s == 'Formulas such as formtok or formtok should be replaced with the formtok placeholder.'

def test_citation_correction():
    s = "Endometrial cancer (EC) is the most common gynaecological malignancy. The age standardised incidence in the UK has risen from 13.4 to 19.1 per 100,000 over the period from 1998 to 2009,[1] possibly as a consequence of rise in obesity, a known risk factor. [2] Age standardised mortality from EC has risen from 3.0 to 4.0 per 100,000 over the same period (1999 to 2012).[3] Women with EC usually present with postmenopausal bleeding and are diagnosed with early stage disease. Although five year survival is in excess of 90% in early stage, it declines sharply to 14% for those with Stage IV disease, similar to ovarian cancer cf.[4] treatment is primarily surgical, but varies according to stage with hysterectomy and bilateral salpingo-oophorectomy (BSO) performed in women detected at Stage I, whilst for women with stage III and IV disease, chemotherapy or radiotherapy are recommended. The value of lymphadenectomy in the treatment of EC is not universally established.[5]"
    s, _ = corrections.correct_citations(s)
    assert s ==  "Endometrial cancer (EC) is the most common gynaecological malignancy. The age standardised incidence in the UK has risen from 13.4 to 19.1 per 100,000 over the period from 1998 to 2009[1], possibly as a consequence of rise in obesity, a known risk factor [2]. Age standardised mortality from EC has risen from 3.0 to 4.0 per 100,000 over the same period (1999 to 2012)[3]. Women with EC usually present with postmenopausal bleeding and are diagnosed with early stage disease. Although five year survival is in excess of 90% in early stage, it declines sharply to 14% for those with Stage IV disease, similar to ovarian cancer cf.[4] treatment is primarily surgical, but varies according to stage with hysterectomy and bilateral salpingo-oophorectomy (BSO) performed in women detected at Stage I, whilst for women with stage III and IV disease, chemotherapy or radiotherapy are recommended. The value of lymphadenectomy in the treatment of EC is not universally established[5]."