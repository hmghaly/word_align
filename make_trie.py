
def make_trie(*words):
    #_end = '_end_'
    root = dict()
    for word in words:
        current_dict = root
        for letter in word:
            current_dict = current_dict.setdefault(letter, {})
        current_dict["_"] = ""
    return root

items=[["IN", "NP"],
       ["NP", "VP"],
       ["DT", "NN"],
       ["PRP"],
       ["DT", "JJ", "NN"],
       ["TO", "VP"],
       ["VBD", "VP"],
       ["VB", "NP"],
       ["MD", "VP"]]
#print(make_trie('foo', 'bar', 'baz', 'barz'))
#print(make_trie(items))
root = dict()
for it in items:
    current_dict = root
    it.reverse()
    for i0 in it:
        current_dict = current_dict.setdefault(i0, {})
    current_dict["_"] = ""

for r in root:
    print(r, root[r])
        
    
    
        
