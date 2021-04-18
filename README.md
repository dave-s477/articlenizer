# Articlenizer

The python package provides functionality preprocessing and parsing of scientific articles. 
It is specifically designed to capture naming conventions common in scientific literature.

## Installing

The package can be installed by: 
```shell
git clone https://github.com/dave-s477/articlenizer
cd articlenizer
pip install .
```
or for an editable installation
```shell
pip install -e .
```

The only non-standard package included in the install is `pytest`. 
To verify the functionality run: 
```shell 
pytest tests
```
or
```shell 
python -m pytest tests
```

## Preprocessing

The package is offers different functionality centered around parsing and processing scientific articles.
The most important ones are also available as command line tools.

### Sentenization

Sentenization is performed by initially splitting everything where one of `[.!?]` is followed by a whitespace. 
The split is refined by adding splitting potential errors such as `"sentence.Next"`that should have a newline but contain a formatting error. 
False positive line splits are recombined after all potential splits were generated in oder to capture errors, e.g. a newline after `e.g.\n` is likely to be erroneous and is removed. 
At last, enumerations are split, but only if they start with an upper cased word `(1) Like this`.

Looking at an example:
```python
from articlenizer import articlenizer as art

art.sentenize_text('Split this text in sentences. Output depends on the flag: "representation".')

# Out: ['Split this text in sentences.', 'Output depends on the flag: "representation".']
```

### Tokenization

Tokenization is purely regex based and can be best understood by taking a look in `./articlenizer/tokenize.py`. 

It can for instance be run by:
```python
from articlenizer import articlenizer as art

art.tokenize_text('Tokenize a text with articlenizer v.0.1.')

# Out: ['Tokenize', 'a', 'text', 'with', 'articlenizer', 'v.', '0.1', '.']
```

### Corrections

Some "obvious" text errors are correct such as: 1. no space after semi-colons: `this;should;not;happen` and no space before and after brackets: `neither(should)this.`

For instance:
```python
from articlenizer import articlenizer as art

art.correct_text('Some wrong text;needs to be corrected.')

# Out: 'Some wrong text; needs to be corrected'
```

### All in one
```python
from articlenizer import articlenizer as art

art.get_tokenized_sentences('Split this text in sentences with articlenizer v.0.1. Output depends on a couple of flags.')

# Out: [
#   ['Split', 'this', 'text', 'in', 'sentences', 'with', 'articlenizer', 'v.', '0.1', '.'], 
#   ['Output', 'depends', 'on', 'a', 'couple', 'of', 'flags', '.']
# ]
```

## Format conversion

### JATS
Articlenizer includes a [JATS](https://de.wikipedia.org/wiki/Journal_Article_Tag_Suite) XML parser that extracts plain text from JATS articles, omitting meta-data. 

### BRAT and IOB2
Articlenizer includes functionality for transforming [BRAT](https://brat.nlplab.org/) (Stand-off format) to [IOB2](https://en.wikipedia.org/wiki/Inside%E2%80%93outside%E2%80%93beginning_(tagging)) and reverse.

### TEI and HTML
It also offers functionality to transform TEI based annotation and HTML based annotation to BRAT format. However, those were designed specifically to handle two corpora and will not generalize well to other problems: [Softcite](https://github.com/howisonlab/softcite-dataset) (TEI) and [BioNerDs](https://sourceforge.net/projects/bionerds/files/goldstandard/) (HTML)