import requests
from BeautifulSoup import BeautifulSoup
import collections
import itertools

# download 2016 vote results from politico. wikipedia is easier but this contains all minor candidates

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

print evs
print totals
