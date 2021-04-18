import os
import xml.sax
import unicodedata


dashes = ['֊', '-', '‐', '‑', '‒', '–', '—', '﹘', '﹣', '－']
correction_regex = r'publisher">[^<]+(Co|Inc|Corp|LP|Crop|corp|Ltd|s\.r\.l|B\.V)</rs>\.'

article_entry = ['TEI']
header_entry = ['teiHeader']
body_entry = ['text']
title_entry = ['title']


def fix_relations(article):
    """Adjust relations to a simple numbering scheme for BRAT annotation

    Args:
        article (dictionary): article information coded in a dictionary
    """
    for rel in article['relations']:
        rel['Arg2'] = article['softcite_id_mapping'][rel['Arg2']]

def repair_citation(text, citation):
    """Adjust article citations to match the "usual" pattern ... [3].

    Args:
        text (string): article text
        citation (string): citation text

    Returns:
        string: adjusted text
    """
    text = text.rsplit(citation, 1)[0]
    add_space = False
    if text.endswith(' '):
        text = text.rstrip()
        add_space = True
    
    if not text.endswith(' al.') and not text.endswith(' ref.') and text.endswith('.') or text.endswith(',') or text.endswith(';'):
        cut_off = text[-1]
        text = text[:-1]
        text += ' ' + '[' + citation + ']' + cut_off
        if add_space:
            text += ' '
    else:
        if add_space:
            text += ' '
        text += '[' + citation + ']'
    return text

def is_multi_ref(ref):
    """Test if a citation candidate consist of multiple citations

    Args:
        ref (string): citation string

    Returns:
        bool: test result
    """
    comma_count = 0
    dash_count = 0
    digit_count = 0
    for c in ref:
        if c.isdigit():
            digit_count += 1
        elif unicodedata.category(c) == 'Pd':
            dash_count += 1
        elif c == ',':
            comma_count += 1
        else:
            return False
    if ( comma_count > 0 or dash_count > 0 ) and digit_count > 1:
        return True
    else:
        return False

class TEI_Parser(xml.sax.handler.ContentHandler):
    """Parser for TEI XML software annotation.
    """
    def __init__(self):
        # self.entity_type_list = set()
        self.article_count = 0
        self.running_id = 0
        self.running_rel_id = 0
        self.in_article = False
        self.in_header = False
        self.in_body = False
        self.in_title = False
        self.in_id = False
        self.in_origin = False
        self.read_text = False
        self.ref = False
        self.rs = False
        self.current_ref = ''
        self.articles = [] 

    def add_article(self):
        self.articles.append({
            'text': '',
            'entities': [],
            'relations': [],
            'softcite_id_mapping': {}
        })

    def startElement(self, name, attrs):
        # Recognize when we are dealing with articles or meta-data
        if name in article_entry:
            if attrs['type'] != 'article':
                raise(RuntimeError("Found type {} -- different from articles".format(attrs['type'])))
            self.add_article()
            self.running_id = 0
            self.running_rel_id = 0
            self.article_count += 1
            self.in_article = True
            self.articles[-1]['subtype'] = attrs['subtype']

        # Recognize when we are dealing with the meta-data of a single article
        if self.in_article and name in header_entry:
            self.in_header = True

        if self.in_header:
            if name in title_entry:
                self.in_title = True

        if self.in_header:
            if name == 'idno' and attrs['type'] == 'PMC':
                self.in_id = True

        if self.in_header:
            if name == 'idno' and attrs['type'] == 'origin':
                self.in_origin = True
            
        # Recognize when we are inside the text of one specific article
        if self.in_article and not self.in_header and name in body_entry:
            self.in_body = True
            if attrs['xml:lang'] != 'en':
                raise(RuntimeError("Non English article in the set."))

        if self.in_body:
            if name not in ['p', 'ref', 'rs', 'text', 'body']:
                raise(RuntimeError("Found unhandled tag: {}".format(name)))
            if name == 'p':
                self.read_text = True
            if name == 'ref' and 'type' in attrs.keys() and attrs['type'] == 'bibr':
                self.ref = True
            if name == 'rs':
                if self.articles[-1]['text'] and not self.articles[-1]['text'].endswith((' ', '(', '[', '{')):
                    self.articles[-1]['text'] += ' '
                self.articles[-1]['entities'].append({
                    'id': self.running_id,
                    'type': attrs['type'],
                    'beg': len(self.articles[-1]['text']),
                    'end': -1,
                    'string': '', 
                    'softcite_id': attrs['xml:id'] if 'xml:id' in attrs.keys() else ''
                })
                if 'xml:id' in attrs.keys():
                    self.articles[-1]['softcite_id_mapping'][attrs['xml:id']] = self.running_id
                if 'corresp' in attrs.keys():
                    self.articles[-1]['relations'].append({
                        'id': self.running_rel_id,
                        'type': '{}_of'.format(attrs['type']),
                        'Arg1': self.running_id,
                        'Arg2': attrs['corresp'].lstrip('#')
                    })
                    self.running_rel_id += 1
                # self.entity_type_list.update([attrs['type']])
                self.rs = True
                self.running_id += 1
                
    def endElement(self, name):
        if name in article_entry:
            self.in_article = False
            if self.articles[-1]['text']:
                if self.articles[-1]['relations']:
                    fix_relations(self.articles[-1])
        if name in header_entry:
            self.in_header = False
        if name in body_entry:
            self.in_body = False
        if name in title_entry:
            self.in_title = False
        if name == 'idno':
            self.in_id = False
            self.in_origin = False
        if name == 'p' and self.read_text:
            self.articles[-1]['text'] += '\n\n'
            self.read_text = False
        if name == 'ref':
            if self.current_ref and ((self.current_ref.isdigit() and len(self.current_ref) < 4 ) or is_multi_ref(self.current_ref) ):
                self.articles[-1]['text'] = repair_citation(self.articles[-1]['text'], self.current_ref)
            self.current_ref = ''
            self.ref = False
        if name == 'rs':
            self.articles[-1]['entities'][-1]['end'] = len(self.articles[-1]['text'])
            self.rs = False

    def characters(self, content):
        if self.in_title:
            self.articles[-1]['title'] = content
        if self.in_id:
            self.articles[-1]['PMC'] = content
        if self.in_origin:
            self.articles[-1]['origin'] = content
        if self.read_text:
            self.articles[-1]['text'] += content
        if self.rs:
            self.articles[-1]['entities'][-1]['string'] = content
        if self.ref:
            self.current_ref += content

def parse(in_file, out_path, write_empty=True):
    """Parse a TEI XML to extract annotate articles and annotation from it.

    Args:
        in_file (PosixPath): file name
        out_path (PosixPath): output path
        write_empty (bool, optional): whether to write empty outputs. Defaults to True.
    """
    parser = xml.sax.make_parser()
    tei_parser = TEI_Parser()
    parser.setContentHandler(tei_parser)

    with in_file.open() as xml_in:
        parser.parse(xml_in)
        print("Parsed {} articles".format(tei_parser.article_count))

    skipped_articles = 0
    for article in tei_parser.articles:
        article_name = article['PMC'] if 'PMC' in article.keys() else article['origin']
        if not write_empty and not article['text'].strip():
            skipped_articles += 1
        else:
            out_text = out_path / '{}.txt'.format(article_name)
            out_annotation = out_path / '{}.ann'.format(article_name)
            with out_text.open(mode='w') as out_art, out_annotation.open(mode='w') as out_anno:
                out_art.write(article['text'])
                for e in article['entities']:
                    out_anno.write('T{}\t{} {} {}\t{}\n'.format(e['id'], e['type'], e['beg'], e['end'], e['string']))
                for r in article['relations']:
                    out_anno.write('R{}\t{} Arg1:T{} Arg2:T{}\t\n'.format(r['id'], r['type'], r['Arg1'], r['Arg2']))
    print("Skipped {} empty articles.".format(skipped_articles))
