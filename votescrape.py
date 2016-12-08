import requests
from BeautifulSoup import BeautifulSoup
import collections
import itertools

r = requests.get('http://www.politico.com/2016-election/results/map/president')
soup = BeautifulSoup(r.text)

state_results = soup.findAll('article', {'class': 'results-group'})
assert len(state_results) == 51

totals = collections.defaultdict(dict)
evs = {}

for a in state_results:
    state = a.findAll('div', {'class': 'results-data pos-omega contains-mix'})[0]['data-stateabb'][-2:]
    ev = int(a.find('p', {'class': 'reporting'}).text.split('Electoral Votes: ')[-1])
    evs[state] = ev
    
    try:
      table = a.findAll('table', {'class': 'results-table'})[0]
    except IndexError:
        import pdb;pdb.set_trace()
    for row in table.findAll('tr'):
        title = row.findAll('th', {'class': 'results-name'})[0].span
        candidate = title.contents[-1].strip()
        party = title.find('span', {'class': 'token token-party'}).abbr['title']
        votes = row.findAll('td', {'class': 'results-popular'})[0].text
        votes = int(''.join(votes.split(',')))

        totals[state][candidate] = votes

assert sum(evs.values()) == 538

from pprint import pprint

def pct(x, ttl):
    return '%0.2f%%' % (100. * x / ttl)

total_popular = sum(itertools.chain(*(v.values() for v in totals.values())))
cand_popular = collections.defaultdict(lambda: 0)
for vv in totals.values():
    for k, v in vv.iteritems():
        cand_popular[k] += v

for cand, vote in sorted(cand_popular.iteritems(), key=lambda e: -e[1]):
    print cand, pct(vote, total_popular)
print
    
cand_evs = collections.defaultdict(lambda: 0)
cand_evs_int = collections.defaultdict(lambda: 0)
for state, results in totals.iteritems():
    state_total = sum(results.values())
    for cand, vote in results.iteritems():
        cand_evs[cand] += float(evs[state]) * vote / state_total

    _evs = evs[state]
    _total = state_total
    while _evs > 0:
        _cand, _ev = sorted(((cand, float(_evs) * vote / _total) for cand, vote in results.iteritems()), key=lambda (c, ev): abs(ev - round(ev)))[0]
        cand_evs_int[_cand] += int(round(_ev))
        _evs -= round(_ev)
        _total -= results[_cand]
        del results[_cand]
 
for cand, evs in sorted(cand_evs.iteritems(), key=lambda e: -e[1]):
    print cand, round(evs, 2), pct(evs, 538)
print
for cand, evs in sorted(cand_evs_int.iteritems(), key=lambda e: -e[1]):
    if evs > 0:
        print cand, evs, pct(evs, 538)
print
        
#pprint(dict(totals))
