from glob import glob

# pdict: pdict['problem set name'] = sorted list of problems
pdict = dict()
# psetlist: sorted list of problem sets
psetlist = list()

for s in glob('problems/*'):
    s = s.split('/')[-1]
    psetlist.append(s)
    
    pdict[s] = list()
    for p in glob('problems/'+s+'/*'):
        pdict[s].append(p.split('/')[-1])
    pdict[s].sort()

psetlist.sort()
print(pdict)
