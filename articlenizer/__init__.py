""" Articlenizer offers easy functions for sentenization and tokenization of scientific articles.
"""

CUSTOM_STOPWORDS = ['had', 'hereupon', 'upon', 'does', 'be', 'toward', 'under', 'put', 'from', 'then', 'always', 'more', 'sometimes', 'least', 'has', 'made', 'have', 'down', 'those', 'could', 'latterly', 'wherein', 'most', 'did', 'even', 'both', 'were', 'whither', 'becoming', 'many', 'seeming', 'else', 'must', 'who', 're', 'within', 'show', 'no', 'now', 'something', 'amount', 'thence', 'once', 'him', 'at', 'a', 'our', 'indeed', 'there', 'll', 'everywhere', 'nothing', 'below', 'whereafter', 'however', 've', 'you', 'three', 'whose', 'them', 'should', 'six', 'or', 'keep', 'everyone', 'will', 'herself', 'alone', 'never', 'still', 'ours', 'this', 'last', 'he', 'out', "d", 'some', 'around', 'several', 'anyhow', 'onto', 'only', 'without', 'whoever', 'fifteen', 'that', 'become', 'and', 'anywhere', 'between', 'would', 'm', 'one', 'whereupon', 'nevertheless', 'doing', 'top', 'up', 'so', 'mostly', 'everything', 'been', 'my', 'if', 'get', 'cannot', 'regarding', 's', 'nine', 'every', 'enough', 'few', 'any', 'thereafter', 'another', 'just', 'd', 'since', 'they', 'nor', 'us', 'five', 'less', 'himself', 'beyond', 'anything', 'beside', 'seem', 'the', 'his', 'on', 'perhaps', 'here', 'how', 'often', 'but', 'name', 'well', 'someone', 'give', 'meanwhile', 'namely', 'whereby', 'ever', 'make', 'itself', 'call', 'much', 'various', 'against', 'except', 'myself', 'through', 'your', 'done', 'therefore', 'are', 'very', 'amongst', 'moreover', 'afterwards', 'besides', 'back', 'along', 'seems', 'formerly', 'i', 'yet', 'over', 'front', 'eight', 'empty', 'to', 'sometime', 'yourselves', 'nobody', 'which', 'twelve', 'further', 'really', 'as', 'neither', 'otherwise', 'sixty', 'such', 'fifty', 'being', 'her', 'across', 'off', 'whole', 'with', 'hundred', 'because', 'she', 'part', 'am', 'not', '’ve', 'somehow', 'therein', 'per', 'thru', 'we', 'for', 'after', 'became', 'becomes', 'due', 'say', 'rather', 'seemed', 'into', 'all', 'bottom', 'used', 'see', 'its', 'until', 'what', 'hereafter', 'towards', 'these', 'eleven', 'full', 'either', 'yourself', 'herein', 'too', 'ca', 'me', 'although', 'also', 'first', 'quite', 'ourselves', 'beforehand', 'elsewhere', 'before', 'why', 'whereas', 'hence', 'two', 'above', 'again', 'unless', 'thereby', 'thus', 'was', 'whom', 'same', 'throughout', 'thereupon', 'next', 'whenever', 'yours', 'behind', 'ten', 'anyway', 'noone' 'via', 'can', 'go', 'may', 'take', 'an', 'by', 'others', 'hers', "ve", 'almost', 'other', 'twenty', 'side', 'might', 'whence', 'former', 'though', 'anyone', 'third', 'somewhere', 'in', 'forty', 'together', 'already', 'about', 'own', 'it', 'each', 'is', 'where', 'during', 'four', 'wherever', 'among', 'their', 'while', 'of', 'hereby', 'when', 'do', 'than', 'serious', 'nowhere', 'whether', 'whatever', 'move', 'none', 'latter', 'themselves', 'please', 'mine']

ABBREVIATIONS = [r'e\. ?g\.\,?', r'i\. ?e\.\,?', r'i\. ?v\.\,?', r'vs\.', r'cf\.', r'c\. ?f\.\,?.', r'Dr\.', r'Mrs?\.', r'Ms\.', r'Ltd\.\,?', r'Inc\.\,?', r'Corp\.\,?', r'wt\.', r'et ?al\.', r'sq\.', r'[Vv]\.', r'[Vv]er\.', r'[Ee]xp\.', r'pp\.', r'St\.', r'[Vv]ers\.', r'spp?\.', r'ca\.', r'refs?\.']
