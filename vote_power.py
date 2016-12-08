import json
from scipy.stats import norm
import math
import csv

major_parties = ('D', 'R')

STDDEV_FOR_MARGIN = 1.282  # norm.cdf(s) = .9

with open('538_data.json') as f:
    data = json.load(f)

with open('states.csv') as f:
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

    # TODO pdf gating
            
    major_share = sum(polls[p]['mid'] for p in major_parties)
    pdfs = {}
    for party in major_parties:
        poll = polls[party]
        stddev = .5 * (poll['hi'] - poll['lo']) / STDDEV_FOR_MARGIN
        useful_range = norm.cdf(major_share, poll['mid'], stddev) - norm.cdf(0, poll['mid'], stddev)
        assert useful_range > .995, (state, useful_range)
        pdfs[party] = norm.pdf(.5*major_share, poll['mid'], stddev) / useful_range
        # old method that doesn't scale the margin of error after eliminating 3rd parties
        #pdfs[party] = norm.pdf(.5, poll['mid'] / major_share, stddev)
    # geometric mean of all parties since they have slightly different margins of error
    pdf = reduce(lambda a, b: a * b, pdfs.values(), 1.)**(1. / len(pdfs))

    vp[state] = pdf / states[state]['pop2010'] * states[state]['ev10'] * 1e6
    
for k, v in sorted(vp.iteritems(), key=lambda e: -e[1]):
    name = states[k]['state']
    strength = v
    vs_strongest = max(vp.values()) / v
    expected = states[k]['ev10']/states[k]['pop2010']*1e6

    print '%s %.2f %.2f' % (name, strength, vs_strongest)
#    print """<tr>
#  <td>%s</td>
#  <td class="data">%.2f</td>
#  <td class="data">%.2f</td>
#  <td class="data"><sup>1/</sup>%.2f</td>
#</tr>""" % (name, expected, strength, vs_strongest)
