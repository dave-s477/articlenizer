import re

from pathlib import Path
from functools import partial
from multiprocessing import Pool

from articlenizer.articlenizer import sentenize_text
from articlenizer.util import chunk_list

article_beg_pattern = re.compile(r'<b>(?P<article_name>[a-zA-Z0-9]+?)</b>')
article_end_pattern = re.compile(r'<p><hr><p>')
xml_pattern = re.compile(r'<(?P<name>[a-zA-Z]+?)>')
xml_end_pattern = re.compile(r'<\/(?P<name>[a-zA-Z]+?)>')

class HTML_Parser():
    """Parser for HTML software annotation.
    """
    def __init__(self, text):
        self.text = text
        self.articles = []
        self.in_article = False
        self.in_entity = False
        self.article_offset = 0
        
    def process_text(self):
        """Transform given HTML text to a list of BRAT tag articles
        """
        for line in self.text.split('<br>\n'):
            if not line:
                continue
            match = article_beg_pattern.search(line)
            if match:
                if '<hr>' in line:
                    self.in_article = False
                article_name = match.group('article_name')
                article_name = article_name.rstrip()
                if article_name:
                    print(article_name)
                    self.in_article = True
                    self.articles.append({
                        'name': article_name,
                        'text': '',
                        'annotations': []
                    })
                    self.article_offset = 0
            else:
                if self.in_article:
                    sub_sentence = line
                    while sub_sentence:
                        if not self.in_entity:
                            match = xml_pattern.search(sub_sentence)
                            if match:
                                self.in_entity = True
                                self.articles[-1]['text'] += sub_sentence[:match.span(0)[0]]
                                sub_sentence = sub_sentence[match.span(0)[1]:]
                                self.articles[-1]['annotations'].append({
                                    'type': match.group('name'),
                                    'beg': len(self.articles[-1]['text'])
                                })
                            else:
                                self.articles[-1]['text'] += sub_sentence
                                sub_sentence = ''
                        else:
                            self.in_entity = False
                            match = xml_end_pattern.search(sub_sentence)
                            if not match:
                                raise(RuntimeError("Found a opening XML tag but no closing tag.."))
                            entity_string = sub_sentence[:match.span(0)[0]]
                            sub_sentence = sub_sentence[match.span(0)[-1]:]
                            self.articles[-1]['text'] += entity_string
                            self.articles[-1]['annotations'][-1]['end'] = len(self.articles[-1]['text'])
                            self.articles[-1]['annotations'][-1]['string'] = entity_string
                    self.articles[-1]['text'] += '\n'

    def get_articles(self):
        return self.articles

def parse_file_list(in_list, out_path='.'):   
    """Parse a list of HTML tagged articles to BRAT format

    Args:
        in_list (list of PosixPaths): List of input files
        out_path (str, optional): Directory in which to write the outputs. Defaults to '.'.

    Returns:
        int: Number of articles extracted 
    """
    n_articles = 0
    for path_in in in_list:
        with path_in.open(mode='r') as xml_in:
            parser = HTML_Parser(xml_in.read())
            parser.process_text()
            articles = parser.get_articles()
            n_articles += len(articles)
            for article in articles:
                out_text = Path('{}/{}.txt'.format(out_path, article['name']))
                out_annotation = Path('{}/{}.ann'.format(out_path, article['name']))
                with out_text.open(mode='w') as out_art, out_annotation.open(mode='w') as out_anno:
                    out_art.write(article['text'])
                    anno_count = 1
                    for e in article['annotations']:
                        out_anno.write('T{}\t{} {} {}\t{}\n'.format(anno_count, e['type'], e['beg'], e['end'], e['string']))
                        anno_count += 1
    return n_articles

def parse_file_list_parallel_wrapper(in_list, out_path='.', n_cores=4):
    """Parallel wrapper for parse_file_list

    Args:
        in_list (list of PosixPaths): List of input files
        out_path (str, optional): Directory in which to write the outputs. Defaults to '.'.
        n_cores (int, optional): Number of python threads to use. Defaults to 4. 

    Returns:
        int: Number of articles extracted 
    """
    list_segments = chunk_list(in_list, n_cores)
    fct_to_execute = partial(parse_file_list, out_path=out_path)
    with Pool(n_cores) as p:
        n_articles = p.map(fct_to_execute, list_segments)
    return sum(n_articles)
