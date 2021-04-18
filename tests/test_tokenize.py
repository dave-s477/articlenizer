import pytest

from articlenizer import articlenizer

def test_tokenization_with_spaces():
    s = 'Tokenization is tested with a single sentence, which requires an example such as the sentence: "Data processing and statistical analyses were conducted using IBM SPSS 22.0 (IBM Corp., Armonk, NY), MATLAB R2015a (The MathWorks, Natick, MA), R 3.3.2 R2.11.1 (http://www.R-project.org/), and Python libraries for scientific computation (NumPy, and SciPy) [39]."'
    s = articlenizer.tokenize_text(s, representation='spaces')
    assert s == ['Tokenization', ' ', 'is', ' ', 'tested', ' ', 'with', ' ', 'a', ' ', 'single', ' ', 'sentence', ',', ' ', 'which', ' ', 'requires', ' ', 'an', ' ', 'example', ' ', 'such', ' ', 'as', ' ', 'the', ' ', 'sentence', ':', ' ', '"', 'Data', ' ', 'processing', ' ', 'and', ' ', 'statistical', ' ', 'analyses', ' ', 'were', ' ', 'conducted', ' ', 'using', ' ', 'IBM', ' ', 'SPSS', ' ', '22.0', ' ', '(', 'IBM', ' ', 'Corp', '.', ',', ' ', 'Armonk', ',', ' ', 'NY', ')', ',', ' ', 'MATLAB', ' ', 'R', '2015a', ' ', '(', 'The', ' ', 'MathWorks', ',', ' ', 'Natick', ',', ' ', 'MA', ')', ',', ' ', 'R', ' ', '3.3.2', ' ', 'R', '2.11.1', ' ', '(', 'http://www.R-project.org/', ')', ',', ' ', 'and', ' ', 'Python', ' ', 'libraries', ' ', 'for', ' ', 'scientific', ' ', 'computation', ' ', '(', 'NumPy', ',', ' ', 'and', ' ', 'SciPy', ')', ' ', '[39]', '.', '"']

def test_tokenization_without_spaces():
    s = 'Tokenization is tested with a single sentence, which requires an example such as the sentence: "Data processing and statistical analyses were conducted using IBM SPSS 22.0 (IBM Corp., Armonk, NY), MATLAB R2015a (The MathWorks, Natick, MA), R 3.3.2 (http://www.R-project.org/), and Python libraries for scientific computation (NumPy, and SciPy) [39]."'
    s = articlenizer.tokenize_text(s)
    assert s == ['Tokenization', 'is', 'tested', 'with', 'a', 'single', 'sentence', ',', 'which', 'requires', 'an', 'example', 'such', 'as', 'the', 'sentence', ':', '"', 'Data', 'processing', 'and', 'statistical', 'analyses', 'were', 'conducted', 'using', 'IBM', 'SPSS', '22.0', '(', 'IBM', 'Corp', '.', ',', 'Armonk', ',', 'NY', ')', ',', 'MATLAB', 'R', '2015a', '(', 'The', 'MathWorks', ',', 'Natick', ',', 'MA', ')', ',', 'R', '3.3.2', '(', 'http://www.R-project.org/', ')', ',', 'and', 'Python', 'libraries', 'for', 'scientific', 'computation', '(', 'NumPy', ',', 'and', 'SciPy', ')', '[39]', '.', '"'] 

def test_tokenization_without_spaces_application():
    s = "Several softwares and R packages are available for Rasch model analysis such as ConQuest (https://shop.acer.edu.au/group/CON3), RUMM (www.rummlab.com.au), ltm (cran.r-project.org/package=ltm) and eRM (cran.r-project.org/package=eRm)."
    s = articlenizer.tokenize_text(s)
    print(s)
    assert s == ['Several', 'softwares', 'and', 'R', 'packages', 'are', 'available', 'for', 'Rasch', 'model', 'analysis', 'such', 'as', 'ConQuest', '(', 'https://shop.acer.edu.au/group/CON3', ')', ',', 'RUMM', '(', 'www.rummlab.com.au', ')', ',', 'ltm', '(', 'cran.r-project.org/package=ltm', ')', 'and', 'eRM', '(', 'cran.r-project.org/package=eRm', ')', '.']
