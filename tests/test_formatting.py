import pytest

from articlenizer import formatting

def test_replacement():
    text = '  Statistical analyses were conducted applying Statistical Program for the Social Sciences (SPS௵௵S);version   24 (f)=∇∑ (IBM;Inc. Chicago, IL, USA).  '
    annotation = '''T1	software_usage 47 90	Statistical Program for the Social Sciences
T2	abbreviation 92 98	SPS௵௵S
R1	abbreviation_of Arg1:T2 Arg2:T1	
T3	version 110 112	24
T4	developer 121 129	IBM;Inc.
R2	version_of Arg1:T3 Arg2:T1	
R3	developer_of Arg1:T4 Arg2:T1	
'''

    sentences = formatting.brat_to_bio(text, annotation)
    target_tokens = ['Statistical', 'analyses', 'were', 'conducted', 'applying', 'Statistical', 'Program', 'for', 'the', 'Social', 'Sciences', '(', 'SPSS', ')', ';', 'version', '24', 'formtok', '(', 'IBM', ';', 'Inc', '.', 'Chicago', ',', 'IL', ',', 'USA', ')', '.']
    target_labels = ['O', 'O', 'O', 'O', 'O', 'B-software_usage', 'I-software_usage', 'I-software_usage', 'I-software_usage', 'I-software_usage', 'I-software_usage', 'O', 'B-abbreviation', 'O', 'O', 'O', 'B-version', 'O', 'O', 'B-developer', 'I-developer', 'I-developer', 'I-developer', 'O', 'O', 'O', 'O', 'O', 'O', 'O']
    assert len(sentences) == 1 and sentences[0]['tokens'] == target_tokens and sentences[0]['labels'] == target_labels

def test_bio_to_brat():
    text = 'Choroidal segmentation and thickness analyses were performed automatically with custom MATLAB ( MATLAB 2017b , The MathWorks , Inc . , Natick , MA , USA ) software for choroid segmentation [21] .'
    labels = 'O O O O O O O O O O B-pl_usage O B-pl_usage B-release O B-developer I-developer I-developer I-developer I-developer O O O O O O O O O O O O O'
    entities, _, _ = formatting.bio_to_brat(text, labels, split_sent=True)
    assert len(entities) == 4 and entities[0]['beg'] == 87 and entities[0]['end'] == 93 and entities[1]['beg'] == 96 and entities[1]['end'] == 102

def test_relations():
    text = '  Statistical analyses were conducted applying Statistical Program for the Social Sciences (SPS௵௵S);version   24 (f)=∇∑ (IBM;Inc. Chicago, IL, USA).  '
    annotation = '''T1	software_usage 47 90	Statistical Program for the Social Sciences
T2	abbreviation 92 98	SPS௵௵S
R1	abbreviation_of Arg1:T2 Arg2:T1	
T3	version 110 112	24
T4	developer 121 129	IBM;Inc.
R2	version_of Arg1:T3 Arg2:T1	
R3	developer_of Arg1:T4 Arg2:T1	
'''

    sentences = formatting.brat_to_bio(text, annotation)
    assert sentences[0]['relations']['R1']['pos2'] == 45 and sentences[0]['relations']['R1']['pos1'] == 91

def test_sentence_based_info():
    text = 'This is some text with software. That will be split into more than one line. Just to debug it.'
    annotation = '''T1\tsoftware 0 4\tThis
T2\tdeveloper 8 12\tsome
T3\tsoftware 38 42\tsplit
R1\tdeveloper_of Arg1:T2 Arg2:T1\t
'''
    sentences = formatting.sentence_based_info(text, annotation)
    expected_result = [{'string': 'This is some text with software.', 'entities': {'T1': {'label': 'software', 'beg': 0, 'end': 4, 'string': 'This', 'idx': 0}, 'T2': {'label': 'developer', 'beg': 8, 'end': 12, 'string': 'some', 'idx': 1}}, 'relations': {'R1': {'label': 'developer_of', 'arg1_old': 'T2', 'arg2_old': 'T1', 'arg1': 'some', 'arg2': 'This', 'pos1': 8, 'pos2': 0, 'ent1': 1, 'ent2': 0}}}, {'string': 'That will be split into more than one line.', 'entities': {'T3': {'label': 'software', 'beg': 5, 'end': 9, 'string': 'will', 'idx': 0}}, 'relations': {}}, {'string': 'Just to debug it.', 'entities': {}, 'relations': {}}]
    assert sentences == expected_result

def test_sentence_based_info_real_sample():
    text = 'The maps were drawn from free-access shapefiles obtained from DIVA-GIS (http://www.diva-gis.org/)with QGIS 1.8.0 and ArcView 3.2 software.'
    annotation = 'T1\treference 72 96\thttp://www.diva-gis.org/'
    sentences = formatting.sentence_based_info(text, annotation)
    expected_result = [{'string': 'The maps were drawn from free-access shapefiles obtained from DIVA-GIS (http://www.diva-gis.org/) with QGIS 1.8.0 and ArcView 3.2 software.', 'entities': {'T1': {'label': 'reference', 'beg': 72, 'end': 96, 'string': 'http://www.diva-gis.org/', 'idx': 0}}, 'relations': {}}]
    assert sentences == expected_result
