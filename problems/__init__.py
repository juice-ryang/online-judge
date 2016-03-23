# pdict: pdict['problem set name'] = sorted list of problems
pdict = dict()
# psetlist: sorted list of problem sets
psetlist = list()


def __search__():
    from glob import glob
    from os.path import isdir, isfile

    for s in glob('problems/*'):
        if not isdir(s) or isfile(s+'/.jrojignore'):
            continue
        s = s.split('/')[-1]
        if s == '__pycache__':
            continue
        psetlist.append(s) 
        pdict[s] = list()
        for p in glob('problems/' + s + '/*'):
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
            return ''.join(f.readlines())
    return '##No description.'


def get_testcase_for_judging(problemset, problem):
    from glob import glob
    d = dict()
    l = list(glob('problems/'+problemset+'/'+problem+'/*'))
    d['testcases'] = list()
    i = 0
    while True:
        t = [e for e in l if e.split('/')[-1][0:2] == '{0:0=2d}'.format(i)]
        if not t:
            break
        d['testcases'].append({e.split('.')[-1]:e for e in t})
        i += 1
    d['N'] = i

    return d


__search__()
