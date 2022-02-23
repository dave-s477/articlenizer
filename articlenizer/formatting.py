import re

from pathlib import Path
from functools import partial
from multiprocessing import Pool
from itertools import zip_longest

from articlenizer import articlenizer, encode_string, corrections, sentenize, util
from articlenizer.util import chunk_list

def annotation_to_dict(annotation):
    """Read BRAT annotation line by line and transform it in a dictionary. 
    Events are currently no supported. 

    Args:
        annotation (string): String formatted in BRAT format (content of .ann file)

    Returns:
        dictionary: contains 'entities' and 'relations' as separated nested dictionaries
    """
    annotation_dict = {
        'entities': {},
        'relations': {}
    }
    lines = annotation.split('\n')
    for line in lines: 
        if line.rstrip():
            line_split = line.split('\t')
            if len(line_split) != 3:
                raise(RuntimeError('Line in unsupported format: "{}"'.format(line)))

            if line.startswith('T'):
                ann_label, ann_beg, ann_end = line_split[1].split()
                annotation_dict['entities'][line_split[0]] = {
                    'label': ann_label,
                    'beg': int(ann_beg),
                    'end': int(ann_end),
                    'string': line_split[2].rstrip()
                }

            elif line.startswith('R'):
                rel_type, arg1, arg2 = line_split[1].split()
                annotation_dict['relations'][line_split[0]] = {
                    'label': rel_type,
                    'arg1': arg1.split(':')[-1],
                    'arg2': arg2.split(':')[-1]
                }

            else: 
                raise(RuntimeError('Got unsupported annotation type in line "{}"'.format(line)))

    return annotation_dict

def _adjust_strings(annotation, text):
    """Adjust annotation string of an entity.
    If entity boundaries are readjusted the resulting annotation string is recalculated by this function.
    Dictionary is adjusted in place

    Args:
        annotation (dictionary): annotation dictionary (result of calling annotation_to_dict)
        text (string): plain text corresponding to the annotated entities
    """
    for _, entity in annotation['entities'].items():
        entity['string'] = text[entity['beg']:entity['end']]        

def _remove_characters(annotation, drops):
    """Update annotation boundaries based on given indices where a character was dropped.

    Args:
        annotation (dictionary):  annotation dictionary (result of calling annotation_to_dict)
        drops (list): list of integer indicies
    """
    for _, entity in annotation['entities'].items():
        entity['beg_org'] = entity['beg']
        entity['end_org'] = entity['end']
    for drop in drops:
        drop_position, _ = drop
        for _, entity in annotation['entities'].items():
            if drop_position <= entity['beg_org']:
                entity['beg'] -= 1
                entity['end'] -= 1
            elif drop_position <= entity['end_org']:
                entity['end'] -= 1

def _add_characters(annotation, adds):
    """Update annotation boundaries based on given indices where a character was added.

    Args:
        annotation (dictionary): annotation dictionary (result of calling annotation_to_dict)
        adds (list): list of integer indicies
    """
    for _, entity in annotation['entities'].items():
        entity['beg_org'] = entity['beg']
        entity['end_org'] = entity['end']
    for add in adds:
        for _, entity in annotation['entities'].items():
            if add <= entity['beg_org']:
                entity['beg'] += 1
                entity['end'] += 1
            elif add < entity['end_org']:
                entity['end'] += 1
            
def _replace_segments(annotation, replacements):
    """Update annotation based on string substitution at a specific position (general case)

    Args:
        annotation (dictionary): annotation dictionary (result of calling annotation_to_dict)
        replacements (list): contains lists of [string, replacement, start_ind, end_ind]
    """
    for drop in replacements:
        drop_string, drop_repl, drop_start, drop_end = drop
        drop_diff = len(drop_repl) - len(drop_string)
        for _, entity in annotation['entities'].items():
            if drop_end < entity['beg']:
                entity['beg'] += drop_diff
                entity['end'] += drop_diff
            elif drop_start >= entity['end']:
                pass
            elif drop_start < entity['beg'] and drop_end <= entity['end']:
                entity['beg'] = drop_start + 1
                entity['end'] += drop_diff
            elif drop_start >= entity['beg'] and drop_end > entity['end']:
                entity['end'] = drop_end + drop_diff 
            elif drop_start < entity['beg'] and drop_end > entity['end']:
                entity['beg'] = drop_start 
                entity['end'] = drop_end + drop_diff
            elif drop_start >= entity['beg'] and drop_end <= entity['end']:
                entity['end'] += drop_diff
            else:
                raise(RuntimeError("Unknown case occurred on {} {}-{} with replacement {}".format(drop_string, drop_start, drop_end, drop_repl)))

def _switch_characters(annotation, switches):
    """Adjust annotation boundaries to switching spans in the text

    Args:
        annotation (dictionary): annotation dictionary (result of calling annotation_to_dict)
        switches ([type]): list of replacement span tuples [(b1, e1), (b2, e2)] with e1 <= b2
    """
    for switch in switches:
        for _, entity in annotation['entities'].items():
            if entity['beg'] >= switch[0][0] and entity['end'] <= switch[0][1]: 
                entity['beg'] += (switch[1][1] - switch[1][0])
                entity['end'] += (switch[1][1] - switch[1][0])
            elif entity['beg'] >= switch[1][0] and entity['end'] <= switch[1][1]: 
                entity['beg'] -= (switch[0][1] - switch[0][0])
                entity['end'] -= (switch[0][1] - switch[0][0])
            elif ( entity['beg'] < switch[0][0] and entity['end'] > switch[0][0] ) or ( entity['beg'] < switch[0][1] and entity['end'] > switch[0][1] ) or ( entity['beg'] < switch[1][0] and entity['end'] > switch[1][0] ) or ( entity['beg'] < switch[1][1] and entity['end'] > switch[1][1] ):
                print(RuntimeWarning("For {} switch and {} entity there is an overlap that cannot be handled.".format(switch, entity)))

def get_sentence_entities(beg, end, annotations):
    """Get annotation for each individual sentence and adjust indices to start from 0 for each sentence.

    Args:
        beg (int): begin index of sentence in text
        end (int): end index of sentence in text
        annotation (dictionary): annotation dictionary (result of calling annotation_to_dict)

    Returns:
        dictionary: entities 
    """
    entities = {}
    for k, v in annotations['entities'].items():
        if v['beg'] >= beg and v['end'] <= end + 1:
            entities[k] = {
                'label': v['label'],
                'beg': v['beg'] - beg,
                'end': v['end'] - beg,
                'string': v['string']
            }
        elif v['beg'] <= end and v['end'] > end:
            print(RuntimeWarning("Annotation span stretches over more than one sentence according to the sentence split: {} and {}".format(k, v)))
            entities[k] = {
                'label': v['label'],
                'beg': v['beg'] - beg,
                'end': end - 1 - beg,
                'string': v['string'][:v['end']-end-1]
            }
        elif v['beg'] <= beg and v['end'] >= beg:
            print(RuntimeWarning("Annotation span stretches over more than one sentence, ingoring the second part!"))
            #print(annotations)
    entities = {k: v for k, v in sorted(entities.items(), key=lambda item: item[1]['beg'])}
    for idx, (k, v) in enumerate(entities.items()):
       v['idx'] = idx

    return entities

def get_sentence_relations(annotations, entities):
    """Get relations from annotation dictonary and combine it with information from the corresponding entities

    Args:
        annotations (dictionary): annotation dictionary (result of calling annotation_to_dict)
        entities (dictionary): entity annotation (result of get_sentence_entities)

    Returns:
        dictionary: extracted and enhanced relations 
    """
    ann_keys = list(entities.keys())
    relations = {}
    for k, v in annotations['relations'].items():
        if v['arg1'] in ann_keys and v['arg2'] in ann_keys:
            relations[k] = {
                'label': v['label'],
                'arg1_old': v['arg1'],
                'arg2_old': v['arg2'],
                'arg1': entities[v['arg1']]['string'],
                'arg2': entities[v['arg2']]['string'],
                'pos1': entities[v['arg1']]['new_beg'] if 'new_beg' in entities[v['arg1']] else entities[v['arg1']]['beg'],
                'pos2': entities[v['arg2']]['new_beg'] if 'new_beg' in entities[v['arg2']] else entities[v['arg2']]['beg'],
                'ent1': entities[v['arg1']]['idx'],
                'ent2': entities[v['arg2']]['idx']
            }
        elif (v['arg1'] in ann_keys and not v['arg2'] in ann_keys) or (v['arg2'] in ann_keys and not v['arg1'] in ann_keys):
            pass
            #print(RuntimeWarning("Relation {}: {} spans over two sentences".format(k, v)))
    return relations

def bio_annotate(tokens, entities):
    """Create BIO annotation for tokens and entities. 

    Args:
        tokens (list): sentence split in token strings 
        entities (dictionary): entity annotation for a given sentence

    Returns:
        list, list, list: adjusted tokens, token names, bio labels
    """
    out_tokens = []
    out_names = []
    out_labels = []
    offset = 0
    new_offset = 0
    space_before = True
    for token in tokens:
        if token.rstrip() and not space_before:
            new_offset += 1
        current_end = offset + len(token)
        current_label = 'O'
        token_name = 'O'
        if token.rstrip():
            for ann_key, ann in entities.items():
                if offset == ann['beg']:
                    if current_label != 'O':
                        raise(RuntimeError("Multiple annotations for a span."))
                    current_label = 'B-{}'.format(ann['label'])
                    token_name = ann_key
                    ann['new_beg'] = new_offset
                    ann['new_end'] = new_offset + len(token)
                elif offset > ann['beg'] and current_end <= ann['end']:
                    if current_label != 'O':
                        raise(RuntimeError("Multiple annotations for a span."))
                    current_label = 'I-{}'.format(ann['label'])
                    token_name = ann_key
                    ann['new_end'] = new_offset + len(token)
                elif offset < ann['beg'] and current_end > ann['beg'] or offset < ann['end'] and current_end > ann['end']:
                    print(RuntimeWarning("Annotation does not match the token split, token: {}, entities: {}".format(token, entities)))
                    if out_labels[-1].startswith('B-') and out_labels[-1].split('-', maxsplit=1)[-1] == ann['label']: 
                        print("Treating as I..")
                        current_label = 'I-{}'.format(ann['label'])
                        token_name = ann_key
                        ann['new_end'] = new_offset + len(token)
                    else:
                        print("Treating as B..")
                        current_label = 'B-{}'.format(ann['label'])
                        token_name = ann_key
                        ann['new_beg'] = new_offset
                        ann['new_end'] = new_offset + len(token)
                    
                else:
                    pass

            out_names.append(token_name)
            out_labels.append(current_label)
            out_tokens.append(token)
        
        offset = current_end 
        new_offset += len(token)
        if not token.rstrip():
            space_before = True
        else:
            space_before = False
    return out_tokens, out_names, out_labels

def brat_to_bio(text, annotation, process_unicode=True, replace_math=True, correct=True, corr_cite=True, keep_paragraphs=False):
    """Transform a document annotated in BRAT format into a sentence based BIO format that also considers relations. 

    Args:
        text (string): plain text of the BRAT annotation (content of .txt file)
        annotation (string): BRAT annotation (content of .ann file)
        process_unicode (bool, optional): replace unicodes. Defaults to True.
        replace_math (bool, optional): replace math equations. Defaults to True.
        correct (bool, optional): replace string errors. Defaults to True.
        corr_cite (bool, optional): correct citation errors. Defaults to True.

    Returns:
        list of dictionaries: sentences information for each sentence in text 
    """
    annotation_dict = annotation_to_dict(annotation)
    if process_unicode:
        text, replacements = encode_string.handle_unicode_characters(text)
        _remove_characters(annotation_dict, replacements)
        _adjust_strings(annotation_dict, text)
    if replace_math:
        text, replacements = corrections.remove_math_expr(text)
        _replace_segments(annotation_dict, replacements)
        _adjust_strings(annotation_dict, text)
    if correct:
        text, replacements = corrections.correct_with_index(text)
        _add_characters(annotation_dict, replacements)
        _adjust_strings(annotation_dict, text)
    if corr_cite:
        text, switched_segments = corrections.correct_citations(text)
        _switch_characters(annotation_dict, switched_segments)
        _adjust_strings(annotation_dict, text)

    text, replacements = sentenize.normalize(text)
    _replace_segments(annotation_dict, replacements)
    _adjust_strings(annotation_dict, text)
    text, replacements = sentenize.sentenize_with_index(text)
    _add_characters(annotation_dict, replacements)
    _adjust_strings(annotation_dict, text)

    sentences = []
    if keep_paragraphs:
        sentence_match_objects = re.finditer(r'([^\n]+|\n{2,})', text)
    else:
        sentence_match_objects = re.finditer(r'([^\n]+)', text)
    for sentence in sentence_match_objects:
        sentence_string = sentence.group(0)
        if not sentence_string.strip():
            sentence_entities = {}
        else:
            sentence_entities = get_sentence_entities(sentence.span(0)[0], sentence.span(0)[1], annotation_dict)
        tokens = articlenizer.tokenize_text(sentence_string, 'spaces', False)
        tokens, names, labels = bio_annotate(tokens, sentence_entities)
        sentence_relations = get_sentence_relations(annotation_dict, sentence_entities)
        sentences.append({
            'string': sentence_string,
            'tokens': tokens,
            'names': names,
            'labels': labels,
            'entities': sentence_entities,
            'relations': sentence_relations
        })
    
    return sentences

def sentence_based_info(text, annotation, process_unicode=True, replace_math=True, correct=True, corr_cite=True, is_preprocessed=False):
    """Transform a document annotated in BRAT format into a sentence based BIO format that also considers relations. 

    Args:
        text (string): plain text of the BRAT annotation (content of .txt file)
        annotation (string): BRAT annotation (content of .ann file)
        process_unicode (bool, optional): replace unicodes. Defaults to True.
        replace_math (bool, optional): replace math equations. Defaults to True.
        correct (bool, optional): replace string errors. Defaults to True.
        corr_cite (bool, optional): correct citation errors. Defaults to True.

    Returns:
        list of dictionaries: Brat based information for each sentence in text 
    """

    annotation_dict = annotation_to_dict(annotation)
    return sentence_based_info_annotation_dict(text, annotation_dict, process_unicode, replace_math, correct, corr_cite, is_preprocessed) 

def sentence_based_info_annotation_dict(text, annotation_dict, process_unicode=True, replace_math=True, correct=True, corr_cite=True, is_preprocessed=False):
    """Transform a document annotated in BRAT format into a sentence based BIO format that also considers relations. 

    Args:
        text (string): plain text of the BRAT annotation (content of .txt file)
        annotation_dict (dict): Result of annotation_to_dict based on BRAT annotation
        process_unicode (bool, optional): replace unicodes. Defaults to True.
        replace_math (bool, optional): replace math equations. Defaults to True.
        correct (bool, optional): replace string errors. Defaults to True.
        corr_cite (bool, optional): correct citation errors. Defaults to True.

    Returns:
        list of dictionaries: Brat based information for each sentence in text 
    """
    
    if process_unicode:
        text, replacements = encode_string.handle_unicode_characters(text)
        _remove_characters(annotation_dict, replacements)
        _adjust_strings(annotation_dict, text)
    if replace_math:
        text, replacements = corrections.remove_math_expr(text)
        _replace_segments(annotation_dict, replacements)
        _adjust_strings(annotation_dict, text)
    if correct:
        text, replacements = corrections.correct_with_index(text)
        _add_characters(annotation_dict, replacements)
        _adjust_strings(annotation_dict, text)
    if corr_cite:
        text, switched_segments = corrections.correct_citations(text)
        _switch_characters(annotation_dict, switched_segments)
        _adjust_strings(annotation_dict, text)

    if not is_preprocessed:
        text, replacements = sentenize.normalize(text)
        _replace_segments(annotation_dict, replacements)
        _adjust_strings(annotation_dict, text)
        text, replacements = sentenize.sentenize_with_index(text)
        _add_characters(annotation_dict, replacements)
        _adjust_strings(annotation_dict, text)

    sentences = []
    sentence_match_objects = re.finditer(r'[^\n]+', text)
    for sentence in sentence_match_objects:
        sentence_string = sentence.group(0)
        sentence_entities = get_sentence_entities(sentence.span(0)[0], sentence.span(0)[1], annotation_dict)
        sentence_relations = get_sentence_relations(annotation_dict, sentence_entities)
        sentences.append({
            'string': sentence_string,
            'entities': sentence_entities,
            'relations': sentence_relations
        })
    
    return sentences

def write_brat_to_bio(file_names, process_unicode=True, replace_math=True, correct=True, corr_cite=True, keep_paragraphs=False):
    """Read a BRAT input file, transform it to BIO format and write separate outputs for text, labels and relations.

    Args:
        file_names ([PosixPath, PosixPath, PosixPath]): paths to text, annotation and output base path
        process_unicode (bool, optional): replace unicodes. Defaults to True.
        replace_math (bool, optional): replace math equations. Defaults to True.
        correct (bool, optional): replace string errors. Defaults to True.
        corr_cite (bool, optional): correct citation errors. Defaults to True.
    """
    with file_names['txt'].open(mode='r') as t_file, file_names['ann'].open(mode='r') as a_file:
        article_text = t_file.read()
        article_annotation = a_file.read()
        article_sentences = brat_to_bio(article_text, article_annotation, process_unicode=process_unicode, replace_math=replace_math, correct=correct, corr_cite=corr_cite, keep_paragraphs=keep_paragraphs)

        out_text_loc = Path(str(file_names['out']) + '.data.txt') 
        out_label_loc = Path(str(file_names['out']) + '.labels.txt') 
        out_relation_loc = Path(str(file_names['out']) + '.relations.txt') 

        with out_text_loc.open(mode='w') as out_text, out_label_loc.open(mode='w') as out_labels, out_relation_loc.open(mode='w') as out_relations:
            for sent in article_sentences:
                out_text.write(' '.join(sent['tokens']).rstrip() + '\n')
                out_labels.write(' '.join(sent['labels']).rstrip() + '\n')
                relation_string = ''
                for _, rel in sent['relations'].items():
                    relation_string += '{}\t{}\t{}\t{}\t{}\t{}\t{};;'.format(rel['label'], rel['arg1'], rel['pos1'], rel['ent1'], rel['arg2'], rel['pos2'], rel['ent2'])
                out_relations.write(relation_string + '\n')

def article_list_brat_to_bio(file_names, process_unicode=True, replace_math=True, correct=True, corr_cite=True, keep_paragraphs=False):
    """Read a list of BRAT input files, transform them to BIO format and write separate outputs for text, labels and relations for each file

    Args:
        file_names (list of lists): elements: [PosixPath, PosixPath, PosixPath] paths to text, annotation and output base path
        process_unicode (bool, optional): replace unicodes. Defaults to True.
        replace_math (bool, optional): replace math equations. Defaults to True.
        correct (bool, optional): replace string errors. Defaults to True.
        corr_cite (bool, optional): correct citation errors. Defaults to True.
    """
    for f_names in file_names:
        write_brat_to_bio(f_names, process_unicode=process_unicode, replace_math=replace_math, correct=correct, corr_cite=corr_cite, keep_paragraphs=keep_paragraphs) 

def brat_to_bio_parallel_wrapper(file_names, n_cores, process_unicode=True, replace_math=True, correct=True, corr_cite=True, keep_paragraphs=False):
    """Parallel wrapper for article_list_brat_to_bio

    Args:
        file_names (list of lists): elements: [PosixPath, PosixPath, PosixPath] paths to text, annotation and output base path
        n_cores (int): number of python processes to use (multiprocessing package)
        process_unicode (bool, optional): replace unicodes. Defaults to True.
        replace_math (bool, optional): replace math equations. Defaults to True.
        correct (bool, optional): replace string errors. Defaults to True.
        corr_cite (bool, optional): correct citation errors. Defaults to True.
    """
    list_segments = chunk_list(file_names, n_cores)
    fct_to_execute = partial(article_list_brat_to_bio, process_unicode=process_unicode, replace_math=replace_math, correct=correct, corr_cite=corr_cite, keep_paragraphs=keep_paragraphs)
    with Pool(n_cores) as p:
        p.map(fct_to_execute, list_segments)

def bio_to_brat(text, label, relation='', split_sent=True, split_words=True):
    """Transform bio annotated tex to BRAT annotation format

    Args:
        text (string or list of sentences): text coded in sentences
        label (string or list of sentences): labels coded in bio-formatted sentences
        split_sent (bool, optional): Split sentences on newline. Defaults to True.
        split_words (bool, optional): Split sentences on spaces. Defaults to True.

    Returns:
        dictionary: annotation 
        string: modified input text
    """
    art_entities = []
    offset = 0
    in_entity = False
    text_out = ''
    relations = []
    if split_sent:
        text = text.split('\n')
        label = label.split('\n')
        relation = relation.split('\n')
    for sentence, sentence_bio, rel in zip_longest(text, label, relation, fillvalue=''):
        entities = []
        if split_words:
            sentence = sentence.rstrip().split()
            sentence_bio = sentence_bio.rstrip().split()
        if len(sentence) > len(sentence_bio):
            print("Warning: a sentence was cut of..")
        elif len(sentence_bio) > len(sentence):
            raise(RuntimeError("Inconsistent input for bio_to_brat"))
        for word, tag in zip(sentence, sentence_bio):
            text_out += word + ' '
            if not tag.startswith('O'):
                tag_prefix = tag[:1]
                ent_type = tag[2:]
                if not in_entity or tag_prefix in ['B', 'S'] or ( entities and entities[-1]['type'] != ent_type ):
                    ent_id = 'T{}'.format(len(entities) + len(art_entities) + 1)
                    entities.append({
                        'id': ent_id,
                        'type': ent_type,
                        'beg': offset,
                        'end': offset + len(word),
                        'string': word
                    })
                else:
                    entities[-1]['end'] += 1 + len(word)
                    entities[-1]['string'] += ' ' + word
                in_entity = True
            else:
                in_entity = False
            offset += len(word) + 1
        text_out = text_out.rstrip() + '\n'
        art_entities.extend(entities)
        for r in rel.split(';;'):
            if r.rstrip():
                rel_id = 'R{}'.format(len(relations) + 1)
                rel_info = r.split('\t')
                relations.append({
                    'id': rel_id,
                    'type': rel_info[0],
                    'Arg1': entities[int(rel_info[3])]['id'],
                    'Arg2': entities[int(rel_info[6])]['id']
                })
        
    return art_entities, relations, text_out

def write_bio_to_brat(file_names):
    """Read a BIO input file, transform it to BRAT format and write separate outputs for text, and BRAT annotation

    Args:
        file_names ([PosixPath, PosixPath, PosixPath]): paths to text, annotation and output base path
    """
    with file_names['data'].open(mode='r') as t_file, file_names['label'].open(mode='r') as l_file:
        article_text = t_file.read()
        article_label = l_file.read()
        if 'relation' in file_names:
            with file_names['relation'].open(mode='r') as r_file:
                article_relation = r_file.read()
            annotations, relations, text = bio_to_brat(article_text, article_label, relation=article_relation)
        else:
            annotations, relations, text = bio_to_brat(article_text, article_label)

    with file_names['txt'].open(mode='w') as out_txt, file_names['ann'].open(mode='w') as out_ann:
        out_txt.write(text)
        for anno in annotations:
            out_ann.write('{}\t{} {} {}\t{}\n'.format(anno['id'], anno['type'], anno['beg'], anno['end'], anno['string']))
        for rel in relations:
            out_ann.write('{}\t{} Arg1:{} Arg2:{}\t\n'.format(rel['id'], rel['type'], rel['Arg1'], rel['Arg2']))

def article_list_bio_to_brat(file_names):
    """Read a list of BIO input files, transform them to BRAT format and write separate outputs for text, and BRAT annotation

    Args:
        file_names (list of lists): elements: [PosixPath, PosixPath, PosixPath] paths to text, annotation and output base path
        process_unicode (bool, optional): replace unicodes. Defaults to True.
        replace_math (bool, optional): replace math equations. Defaults to True.
        correct (bool, optional): replace string errors. Defaults to True.
        corr_cite (bool, optional): correct citation errors. Defaults to True.
    """
    for f_names in file_names:
        write_bio_to_brat(f_names) 

def bio_to_brat_parallel_wrapper(file_names, n_cores):
    """Parallel wrapper for article_list_bio_to_brat

    Args:
        file_names (list of lists): elements: [PosixPath, PosixPath, PosixPath, PosixPath] paths to text, labels and output text and output annotation
        n_cores (int): number of python processes to use (multiprocessing package)
    """
    list_segments = chunk_list(file_names, n_cores)
    with Pool(n_cores) as p:
        p.map(article_list_bio_to_brat, list_segments)
