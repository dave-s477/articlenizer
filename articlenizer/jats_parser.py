import xml.sax

from pathlib import Path
from multiprocessing import Pool
from functools import partial
from collections import deque

from articlenizer import articlenizer
from articlenizer.util import chunk_list

PARAGRAPH_TAGS = ['title', 'p', 'sec', 'abstract']
LINEBREAK_TAGS = ['list-item']
LINK_TAGS = ['ext-link']
IGNORE_TAGS = ['table', 'fig', 'back', 'fn', 'kwd-group', 'contrib-group', 'license']
MAIN_TAGS = ['sec', 'title', 'p', 'bold', 'italic', 'list', 'list-item', 'disp-formula','inline-formula', 'abstract', 'uri', 'monospace']
REFERENCE_TAGS = ['xref']
REPLACE_TAGS = ['disp-formula', 'inline-formula']
START_TAG = ['abstract']
IDS = ['article-id']
TITLE = ['title']
AVAILABILITY_TITLE = 'availability and requirements'

class ArticleNotEnglishError(Exception):
    """Exception to indicate XML articles in a language other than Englisch. """
    def __init__(self, msg='Found non English article.'):
        self.msg = msg
        
    def __str__(self):
        return "[ERROR] %s\n" % str(self.msg)

class JATS_Parser(xml.sax.handler.ContentHandler):
    """Parser for scientific articles given in JATS (Journal Article Tag Suite) format.
    """
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Allows to reset a parser in case it is used for multiple documents. 
        """
        self.in_body = True
        self.content = ''
        self.catch_text = False
        self.sections = deque()
        self.started = False
        self.catch_id = ''
        self.title = ''
        self.catch_title = False
        self.catch_link = False
        self.link_tag_candidate = ''
        self.link_content_candidate = ''
        self.ids = {}

    def startElement(self, name, attrs):
        if name == 'article':
            if 'xml:lang' in attrs.keys() and attrs['xml:lang'] != 'en':
                raise(ArticleNotEnglishError())

        self.catch_id = ''
        if name in IDS:
            if attrs['pub-id-type']:
                self.catch_id = attrs['pub-id-type']
            else:
                print("Found ID without pub-id-type")
                print(name)
                print(attrs.items())
                print()

        if name in START_TAG:
            self.started = True
        
        # ignore all subnodes of ignored tags
        if not self.in_body:
            return
        
        # add node to stack, even ignored nodes
        # remember the latest section we entered
        self.sections.append(name)
        
        # ignore tag?
        if name in IGNORE_TAGS:
            self.in_body = False
            return

        if name in LINK_TAGS:
            self.catch_link = True
            if self.started and self.in_body and 'xlink:href' in attrs:
                self.link_tag_candidate = attrs['xlink:href']
            self.catch_text = False

        # tag with text of interest?
        if name in MAIN_TAGS:
            # start catching text
            self.catch_text = True
            # interesting but no text, so just replace by tag name
            if name in REPLACE_TAGS:
                self.content += " " +  name + " "
        elif name in REFERENCE_TAGS:
            self.catch_text = True
            self.content += "<handle-bib>"
        else: 
            # not interesting stop catching text
            self.catch_text = False

        if name in TITLE:
            if self.title.lower() == AVAILABILITY_TITLE:
                self.content = self.content.rstrip() + '"\n\n'
            self.catch_title = True
                
    def endElement(self, name):
        if name != self.sections[-1]:
            # node was not interesting enough to explore
            return
        self.in_body = True

        if name in IDS:
            self.catch_id = ''

        if name in LINK_TAGS:
            # Links are handled quite weird.. in the text they are often shorted 
            # but full links are often provided in the attributes.. 
            # but sometimes the tags are empty
            # we go with the simple solution for now and take the one that is longer 
            if len(self.link_tag_candidate) > len(self.link_content_candidate):
                self.content += self.link_tag_candidate
            else:
                self.content += self.link_content_candidate
            self.catch_link = False
            

        if name in REFERENCE_TAGS:
            self.content += "</handle-bib>"

        if name in PARAGRAPH_TAGS:
            if name in TITLE or not self.title.lower() == AVAILABILITY_TITLE:
                self.content += '\n'
            else:
                self.content += ' '
        elif name in LINEBREAK_TAGS:
            if name in TITLE or not self.title.lower() == AVAILABILITY_TITLE:
                self.content += '\n'
            else:
                self.content += ' '
        remove = self.sections.pop()

        if name in TITLE:
            self.catch_title = False
            if self.title.lower() == AVAILABILITY_TITLE:
                self.content += '"'
        
        self.catch_text = False
        
        if len(self.sections) > 0 and ( self.sections[-1] in MAIN_TAGS or self.sections[-1] in REFERENCE_TAGS ):
            self.catch_text = True
 
    def characters(self, content):
        if not self.in_body:
            return
        if self.catch_text:
            if self.title.lower() == AVAILABILITY_TITLE:
                self.content += content.replace('\n', '')
            else:
                self.content += content
        if self.catch_id:
            self.ids[self.catch_id] = content

        if self.catch_title:
            self.title = content

        if self.catch_link:
            self.link_content_candidate = content

    def get_text(self):
        if self.title.lower() == AVAILABILITY_TITLE:
            self.content = self.content.rstrip() + '"'
        return self.content

    def get_ids(self):
        return self.ids

def handle_xrefs(text):
    """JATS xref elements are not consistent between journals. 
    For NLP applications it is desirable to have a similar citation style between all documents.
    This function summarizes and moves citations in order to place different styles at the same positions. 

    Args:
        text (string): text string

    Returns:
        string: text with updated citations
    """
    text = articlenizer.handle_unicode(text)
    out_text = ''
    chunks = text.split('<handle-bib>', 1)
    while len(chunks) > 1:
        txt = chunks[0]
        next_bib, text = chunks[1].split('</handle-bib>', 1)

        if next_bib.isdigit() and len(next_bib) <= 3 and (not txt or txt[-1] != '[') and ( not text or text[0] != ']'):
            out_text += txt.rstrip()

            bracket_is_open = False
            if out_text:
                idx = 1
                last_char = out_text[-idx]
                while len(out_text) > idx and not last_char.isalpha():
                    if last_char == ']':
                        break
                    if last_char == '[':
                        bracket_is_open = True
                        break
                    idx += 1
                    last_char = out_text[-idx]

            if not bracket_is_open:
                if out_text.endswith('.'):
                    if out_text[-2] == ']' and out_text[-3].isdigit():
                        out_text = out_text.rstrip('].') + ',' + next_bib+ '].'
                    else:
                        out_text = out_text.rstrip('.') + ' [' + next_bib + '].' 
                elif out_text.endswith(','):
                    add_dot = False
                    out_text = out_text.rstrip(',')
                    if out_text[-1] == '.':
                        out_text = out_text.rstrip('.')
                        add_dot = True
                    if out_text[-1] == ']':
                        out_text = out_text.rstrip(']') + ',' + next_bib+ ']'
                    else:
                        out_text += ' [' + next_bib + '],'
                    if add_dot:
                        out_text += '.'
                elif out_text.endswith('-'):
                    add_dot = False
                    out_text = out_text.rstrip('-')
                    if out_text[-1] == '.':
                        out_text = out_text.rstrip('.')
                        add_dot = True
                    if out_text[-1] == ']':
                        out_text = out_text.rstrip(']') + '-' + next_bib+ ']'
                    else:
                        out_text = out_text + '-[' + next_bib + ']'
                    if add_dot:
                        out_text += '.'
                elif out_text.endswith(']'):
                    out_text = out_text.rstrip(']') + ',' + next_bib + ']'
            
                else:
                    out_text = out_text + ' [' + next_bib + ']' 
            else:
                out_text += next_bib
        else:
            out_text += txt + next_bib

        chunks = text.split('<handle-bib>', 1)
    out_text += chunks[0]
    return out_text

def parse_jats_article(xml_content, parser=None, jats_parser=None):
    """Parse article text from a given JATS xml file.

    Args:
        xml_content (filename or stream): filename or open file handle for file to parse
        parser (xml.sax parser, optional): SAX parser, if None is provided one will be generated. Defaults to None.
        jats_parser (JATS_Parser, optional): JATS_Parser object, will be generated if not provided. Defaults to None.

    Returns:
        string: article plain text
    """
    if parser is None or jats_parser is None:
        parser = xml.sax.make_parser()
        jats_parser = JATS_Parser()
        parser.setContentHandler(jats_parser)
    try:
        jats_parser.reset()
        parser.parse(xml_content)
        text = jats_parser.get_text()
        ids = jats_parser.get_ids()
    except ArticleNotEnglishError:
        return None
    else:
        text = handle_xrefs(text)
        return text

def parse_article_list(in_list):
    """Parse and write JATS articles to plain text files.

    Args:
        in_list ([in_path, out_path]): path to input JATS, location for output plain txt

    Returns:
        int: count of erroneous files
    """
    parser = xml.sax.make_parser()
    jats_parser = JATS_Parser()
    parser.setContentHandler(jats_parser)
    
    error_count = 0
    for path_in, path_out in in_list:
        with path_in.open(mode='r') as xml_in:
            text = parse_jats_article(xml_in, parser=parser, jats_parser=jats_parser)
            if text is None:
                error_count += 1
            else:
                with path_out.open('w') as txt_out:
                    txt_out.write(text)

    return error_count

def parse_article_list_parallel_wrapper(in_list, n_cores=4):
    """Parallel wrapper around parse_article_list

    Args:
        in_list ([in_path, out_path]): path to input JATS, location for output plain txt
        n_cores (int, optional): number parallel python processes to spawn (multiprocessing package). Defaults to 4.
    """
    list_segments = chunk_list(in_list, n_cores)
    with Pool(n_cores) as p:
        error_counts = p.map(parse_article_list, list_segments)
    return sum(error_counts)
