# pdict: pdict['problem set name'] = sorted list of problems
pdict = dict()
# psetlist: sorted list of problem sets
psetlist = list()


def __search__():
    from glob import glob
    for s in glob('problems/*'):
        s = s.split('/')[-1]
        # QUICK FIX
        if s == '__init__.py' or s == '__pycache__':
            continue
        psetlist.append(s) 
        pdict[s] = list()
        for p in glob('problems/'+s+'/*'):
            pdict[s].append(p.split('/')[-1])
        pdict[s].sort()
    psetlist.sort()


def get_problems(problemset):
    if problemset in psetlist:
        return pdict[problemset]


def get_all_sets():
    return psetlist


def get_problem_description(problemset, problem):
    if problemset in psetlist:
        if problem in pdict[problemset]:
            f = open('problems/'+problemset+'/'+problem+'/description.md')
            return "".join(f.readlines())
    return None


__search__()
