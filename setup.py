from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='articlenizer',
      version='0.1',
      description='Sentenization and Tokenization of scientific articles.',
      long_description=readme(),
      classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Topic :: Text Processing :: NLP',
      ],
      keywords='scientific sentenization tokenization paper article parsing normalization',
      url='https://github.com/dave-s477/articlenizer',
      author='David Schindler',
      author_email='david.schindler@uni-rostock.de',
      license='MIT',
      packages=['articlenizer'],
      scripts=[
        'bin/brat_to_bio',
        'bin/bio_to_brat',
        'bin/parse_JATS',
        'bin/parse_TEI',
        'bin/parse_HTML',
        'bin/articlenize_prepro',
        'bin/analyze_corpus'
      ],
      install_requires=[
        'pytest'
      ],
      include_package_data=True,
      zip_safe=False)