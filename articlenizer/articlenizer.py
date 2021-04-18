from pathlib import Path
from functools import partial
from multiprocessing import Pool

from articlenizer import sentenize
from articlenizer import tokenize
from articlenizer import corrections
from articlenizer import encode_string
from articlenizer.util import chunk_list

def handle_unicode(text):
    """Wrapper for encode_string.handle_unicode_characters. Handle unicode characters appearing in string.

    Args:
        text (string): string to transform

    Returns:
        string: unicode 'normalized' string
    """
    text, _ = encode_string.handle_unicode_characters(text)
    return text

def correct_text(text):
    """Wrapper for corrections.correct. Correct likely errors in a given text in order to improve downstream processing

    Args:
        text (string): text to correct 

    Returns:
        string: corrected text
    """
    text = corrections.correct(text)
    return text

def sentenize_text(text, representation='list', correct=True):
    """Sentenize a given text

    Args:
        text (string): string to sentenize
        representation (str, optional): return type, 'list' return a list of sentences, otherwise a block of text is returned where newlines indicate individual sentences. Defaults to 'list'.
        correct (bool): correct errors in string

    Returns:
        list or text: sentences in the given text
    """
    if correct:
        text = correct_text(text)
    sentences = sentenize.sentenize(text)
    if representation == 'list':
        sentences = sentences.split('\n')
    return sentences

def tokenize_text(sentence, representation='no_spaces', correct=True):
    """Sentenize a given sentence

    Args:
        text (string): string to tokenize
        representation (str, optional): whether to include spaces in the return string. If no spaces are returned the original string cannot be reconstructed. Defaults to 'no_spaces'.
        correct (bool): correct errors in string

    Returns:
        list: list of tokens
    """
    if correct:
        sentence = correct_text(sentence)
    tokens = tokenize.tokenize(sentence)
    if representation == 'no_spaces':
        tokens = [tok for tok in tokens if tok.rstrip()]
    return tokens

def replace_math_equations(text):
    """Replace math equations by a special token

    Args:
        text (string): text
    
    Returns:
        string: transformed string 
    """
    text, _ = corrections.remove_math_expr(text)
    return text

def switch_citations(text):
    text, _ = corrections.correct_citations(text)
    return text

def get_tokenized_sentences(text, sentence_rep='list', token_rep='no_spaces', process_unicode=True, replace_math=True, correct=True, corr_cite=True):
    """Sent- and Tokenize an text

    Args:
        text (string): text to process
        sentence_rep (str, optional): see 'sentenize_text'. Defaults to 'list'.
        token_rep (str, optional): see 'tokenize_text'. Defaults to 'no_spaces'.
        process_unicode (bool, optional): replace unicodes. Defaults to True.
        replace_math (bool, optional): replace math equations. Defaults to True.
        correct (bool, optional): replace string errors. Defaults to True.
        corr_cite (bool, optional): correct citation errors. Defaults to True.

    Returns:
        list of lists: sentences with individual tokens
    """
    if process_unicode:
        text = handle_unicode(text)
    if replace_math:
        text = replace_math_equations(text)
    if corr_cite:
        text = switch_citations(text)
    text = sentenize_text(text, sentence_rep, correct=correct)
    tokenized_text = []
    for line in text:
        tokenized_text.append(tokenize_text(line, token_rep, correct=False))
    return tokenized_text

def preprocess_articles(file_list, process_unicode=True, replace_math=True, correct=True, corr_cite=True):
    """Preprocess a list of articles and write output to files.

    Args:
        file_list ([input filename, output filename]): pair of file names to read and to write
        process_unicode (bool, optional): replace unicodes. Defaults to True.
        replace_math (bool, optional): replace math equations. Defaults to True.
        correct (bool, optional): replace string errors. Defaults to True.
        corr_cite (bool, optional): correct citation errors. Defaults to True.
    """
    for in_name, out_name in file_list:
        with in_name.open(mode='r') as article:
            text = article.read()
        text = get_tokenized_sentences(text, sentence_rep='list', token_rep='no_spaces', process_unicode=process_unicode, replace_math=replace_math, correct=correct, corr_cite=corr_cite)
        with out_name.open(mode='w') as prepro_article:
            for line in text:
                prepro_article.write(' '.join(line).rstrip() + '\n')

def preprocess_articles_parallel_wrapper(file_list, n_cores, process_unicode=True, replace_math=True, correct=True, corr_cite=True):
    """Parallel wrapper for preprocess_articles

    Args:
        file_list ([input filename, output filename]): pair of file names to read and to write
        n_cores (int): number of python processes to use (multiprocessing package)
        process_unicode (bool, optional): replace unicodes. Defaults to True.
        replace_math (bool, optional): replace math equations. Defaults to True.
        correct (bool, optional): replace string errors. Defaults to True.
        corr_cite (bool, optional): correct citation errors. Defaults to True.
    """
    list_segments = chunk_list(file_list, n_cores)
    fct_to_execute = partial(preprocess_articles, process_unicode=process_unicode, replace_math=replace_math, correct=correct, corr_cite=corr_cite)
    with Pool(n_cores) as p:
        p.map(fct_to_execute, list_segments)
