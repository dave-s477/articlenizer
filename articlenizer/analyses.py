# count relation for each 'main' entity

# num of all relations

from articlenizer import articlenizer, formatting

def analyze_text(text_files):
    """Analyze files regarding: average number of sentences, tokens and token length

    Args:
        text_files (list): list of input text files
    """
    print("Analyzing text")
    token_lengths = {}
    num_sentences = 0
    num_words = 0
    for f in text_files:
        with f.open() as in_text:
            article_text = in_text.read()
            tokenized_text = articlenizer.get_tokenized_sentences(article_text)
            for sent in tokenized_text:
                num_sentences += 1
                num_words += len(sent)
                for token in sent:
                    length = len(token)
                    if length not in token_lengths.keys():
                        token_lengths[length] = 0
                    token_lengths[length] += 1
    out_s = """
Token length distribution of the given corpus (length, n): {}
Average number of sentences: {}
Average number of tokens: {}
    """.format(
            sorted(token_lengths.items()), 
            round(num_sentences / len(text_files), 2),
            round(num_words / len(text_files), 2) 
        )
    print(out_s)

def show_most_common_entities(entity_dict, n=5):
    """Format information on entity count in a string

    Args:
        entity_dict (dictionary): entities and their attributes
        n (int, optional): only the n most common occurrences are used. Defaults to 5.

    Return:
        string: formatted output string
    """
    out_s = ''
    for ent_type, ents in entity_dict.items():
        out_s += '\t{}:\n'.format(ent_type)
        n_ents = {k: v for k, v in sorted(ents.items(), key=lambda item: item[1], reverse=True)}
        for idx, (ent, count) in enumerate(n_ents.items()):
            out_s += '\t\t{}:\t{} ({})\n'.format(idx+1, ent, count)
            if idx >= n:
                break
        out_s += '\n'
    return out_s

def show_counts(input_dict):
    """Format dictionary count information into a string

    Args:
        input_dict (dictionary): input keys and their counts
    
    Return:
        string: formatted output string
    """
    out_s = ''
    in_dict_sorted =  {k: v for k, v in sorted(input_dict.items(), key=lambda item: item[1], reverse=True)}
    for idx, (k, v) in enumerate(in_dict_sorted.items()):
        out_s += '\t{}:\t{} ({})\n'.format(idx, k, v)
    out_s += '\n'
    return out_s

def add_to_dictionary(entity_counts, entity, overall_entity_counts=None):
    """Update a dictonary summary of given entities with a new entity

    Args:
        entity_counts (dictionary): dictionary with counts
        entity (dictionary): information of a single entity annotation
        overall_entity_count (dictionary, optional): dictionary with overall summary counts. Defaults to None.
    """
    anno_parts = entity['label'].split('_')
    for idx, part in enumerate(anno_parts):
        if part not in entity_counts.keys():
            entity_counts[part] = {}
        if entity['string'] not in entity_counts[part].keys():
            entity_counts[part][entity['string']] = 0
        entity_counts[part][entity['string']] += 1
        if overall_entity_counts is not None:
            if idx not in overall_entity_counts.keys():
                overall_entity_counts[idx] = {}
            if part not in overall_entity_counts[idx].keys():
                overall_entity_counts[idx][part] = 0
            overall_entity_counts[idx][part] += 1

def analyze_annotation(annotation_files, threshold=6):
    """Analyze list of BRAT annotation files with respect to the annotated entities and relations.

    Args:
        annotation_files (list): list of input annotation files
        threshold (int, optional): print annotations longer than threshold tokens. Defaults to 6.
    """
    entity_count = 0
    relation_count = 0
    max_entity_count = 0
    max_relation_count = 0
    overall_entity_counts = {}
    entity_counts = {}
    # entity_counts_lower = {}
    token_number = {}
    relation_counts = {}

    for f in annotation_files:
        with f.open() as in_anno:
            anno_text = in_anno.read()
            annotation_dict = formatting.annotation_to_dict(anno_text)
            entity_count += len(annotation_dict['entities'])
            relation_count += len(annotation_dict['relations'])
            if len(annotation_dict['entities']) > max_entity_count:
                max_entity_count = len(annotation_dict['entities'])
            if len(annotation_dict['relations']) > max_relation_count:
                max_relation_count = len(annotation_dict['relations'])

            for _, entity in annotation_dict['entities'].items():
                add_to_dictionary(entity_counts, entity, overall_entity_counts)
                # add_to_dictionary(entity_counts_lower, entity)

                entity_tokens = articlenizer.tokenize_text(entity['string'])
                if len(entity_tokens) not in token_number.keys():
                    token_number[len(entity_tokens)] = 0
                token_number[len(entity_tokens)] += 1
                if len(entity_tokens) > threshold:
                    print("Annotation of length {}: {}".format(len(entity_tokens), entity_tokens))
                    print(f)

            for _, relation in annotation_dict['relations'].items():
                if relation['label'] not in relation_counts.keys():
                    relation_counts[relation['label']] = 0
                relation_counts[relation['label']] += 1 

    average_entities = entity_count / len(annotation_files)
    average_relations = relation_count / len(annotation_files)

    out_s = """
Base Statistics:
\tTotal number of entities/relations: {}/{}
\tAverage entities/relations:         {}/{}
\tMax entities/relations:             {}/{}
\tDistribution of token length: {}

Occurrences of Entities: 

{} 
Occurrences of Mention Types:

{}
Occurrences of Relation:

{}
Most Common Software:

{}
    """.format(
        entity_count, relation_count,
        round(average_entities, 2), round(average_relations, 2),
        max_entity_count, max_relation_count,
        sorted(token_number.items()),
        show_counts(overall_entity_counts[0]),
        show_counts(overall_entity_counts[1]),
        show_counts(relation_counts),
        show_most_common_entities(entity_counts)
    )
    print(out_s)

def analyze_corpus(text_files=None, annotation_files=None, threshold=6):
    """Analyze a BRAT annotated corpus with respect to text and annotation.

    Args:
        text_files (list, optional): PosixPaths to plain text files. Defaults to None.
        annotation_files (list, optional): PosixPaths to BRAT annotation files. Defaults to None.
        threshold (int, optional): print annotations longer than threshold tokens. Defaults to 6.
    """
    if text_files is not None:
        analyze_text(text_files)
    if annotation_files is not None:
        analyze_annotation(annotation_files, threshold)