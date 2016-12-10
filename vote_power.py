import json
from scipy.stats import norm
from scipy.stats import beta
import math
import csv

# compute the relative 'voting power' in each state factoring in swing state dynamics

major_parties = ('D', 'R')

# to convert 538 upper bound (90th pctile) into std-dev
STDDEV_FOR_MARGIN = norm.ppf(.9)

with open('data/538_data.json') as f:
    data = json.load(f)

with open('data/states.csv') as f:
    states = {}
    for row in csv.DictReader(f):
        for k, v in row.iteritems():
            try:
                row[k] = float(v)
            except:
                pass
        states[row['abbr']] = row
    
vp = {}
for state, polls in sorted(data.iteritems()):
    for party, poll in polls.iteritems():
        skew = abs(poll['mid'] - .5*(poll['lo']+poll['hi']))
        assert skew < .5, (state, party)

    if state == 'UT':
        # merge mcmullin and trump votes
        for k in polls['R']:
            polls['R'][k] += polls['I']['mid']

    major_share = sum(polls[p]['mid'] for p in major_parties)
    pdfs = {}

    # we fit the lower and upper bounds into a normal distribution. it's actually a beta distribution
    # which we could fit directly

    # we calculate the likelihood that the two major candidates will meet right in the middle
    # this is essentially equivalent to ignoring all third party candidates entirely
    # i think this is a valid assumption because the third party votes would likely be distributed to
    # the major candidates in the ratio of their polls, and the uncertainty therein would also proportionally
    # increase the major candidates' margins of error.
    # this seems to work fine so long as no third party has a chance of winning the state, otherwise
    # it gets into math that is too complex for me. i think that would require integrating over a dirichlet
    # distribution but it's unclear how to map the 538 per-candidate beta distributions into that (they all
    # have a different alpha+beta).
    
    for party in major_parties:
        poll = polls[party]
        stddev = .5 * (poll['hi'] - poll['lo']) / STDDEV_FOR_MARGIN
        useful_range = norm.cdf(major_share, poll['mid'], stddev) - norm.cdf(0, poll['mid'], stddev)
        assert useful_range > .995, (state, useful_range)
        pdfs[party] = norm.pdf(.5*major_share, poll['mid'], stddev) / useful_range
    # geometric mean of all parties since they have slightly different margins of error
    pdf = reduce(lambda a, b: a * b, pdfs.values(), 1.)**(1. / len(pdfs))

    vp[state] = pdf / states[state]['pop2010'] * states[state]['ev10'] * 1e6

# print per-vote power in each state
for k, v in sorted(vp.iteritems(), key=lambda e: -e[1]):
    name = states[k]['state']
    strength = v
    vs_strongest = max(vp.values()) / v
    expected = states[k]['ev10']/states[k]['pop2010']*1e6
    print '%s %.2f %.2f %.2f' % (name, strength, vs_strongest, expected)    
#    print """<tr>
#  <td>%s</td>
#  <td class="data">%.2f</td>
#  <td class="data">%.2f</td>
#  <td class="data"><sup>1/</sup>%.2f</td>
#</tr>""" % (name, expected, strength, vs_strongest)
print

sp = dict((k, v * states[k]['pop2010'] / 1e6) for k, v in vp.iteritems())

# print aggregate per-state power
for k, v in sorted(sp.iteritems(), key=lambda e: -e[1]):
    name = states[k]['state']
    pop = states[k]['pop2010']
    _evs = states[k]['ev10']
    strength = v
    popfrac = pop / sum(v['pop2010'] for v in states.values())
    evfrac = _evs / sum(v['ev10'] for v in states.values())
    sfrac = strength / sum(sp.values())
    cumsfrac = sum(v for v in sp.values() if v >= strength) / sum(sp.values())
    #print '%s %.1f %.1f %.2f %.2f' % (name, 100*popfrac, 100*evfrac, 100*sfrac, 100*cumsfrac)
    print """<tr>
  <td>%s</td>
  <td class="data">%.1f%%</td>
  <td class="data">%.1f%%</td>
  <td class="data">%.*f%%</td>
  <td class="data">%.*f%%</td>
</tr>""" % (name, 100*popfrac, 100*evfrac, 3 if sfrac < .001 else 1, 100*sfrac, 3 if cumsfrac > .999 else 1, 100*cumsfrac)
