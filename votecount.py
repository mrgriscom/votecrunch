import csv
import itertools
import collections
import sys

ELECTION = int(sys.argv[1])

with open('states.csv') as f:
    states = {}
    for row in csv.DictReader(f):
        for k, v in row.iteritems():
            try:
                row[k] = float(v)
            except:
                pass
        states[row['abbr']] = row

states_by_name = dict((v['state'], k) for k, v in states.iteritems())

def get_evs(state):
    field = 'ev%02d' % ((10*((ELECTION-1)//10))%100)
    return states[state][field]
TOTAL_EVS = sum(get_evs(state) for state in states.keys())

totals = {}
with open('%s_results.csv' % ELECTION) as f:
    r = csv.reader(f)
    for i, row in enumerate(r):
        if i == 0:
            def get_can(s):
                can = s.split()[1]
                return {
                    'W.': 'Bush',
                    'H.W.': 'Bush',
                }.get(can, can)
            candidates = [get_can(k) for k in row[1:row.index('Others')]]
            candidates.append('_other')
        elif i == 1:
            pass
        else:
            state = row[0]
            if any(c in state for c in '123456789'):
                continue
            if 'total' in state.lower():
                continue
            if '(' in state:
                state = state[:state.index('(')].strip()
            state = {
                'D.C.': 'District of Columbia',
            }.get(state, state)
                
            state = ''.join(c for c in state if c.lower() in 'abcdefghijklmnopqrstuvwxyz ')
            state = states_by_name[state]
                
            totals[state] = {}
            for c, cand in enumerate(candidates):
                val = row[2 + 3*c]
                try:
                    val = float(''.join(val.split(',')))
                except:
                    val = 0
                totals[state][cand] = val

assert len(totals) == 51
                
def pct(x, ttl, digits=2):
    return '%0.*f%%' % (digits, 100. * x / ttl)

def tally_state_evs(method):
    tally = collections.defaultdict(dict)
    for state, results in totals.iteritems():
        state_total = sum(results.values())
        cands = sorted(results.keys())
        pct_pop = [results[cand] / state_total for cand in cands]
        tally[state] = dict((cand, ev) for cand, ev in zip(cands, method(get_evs(state), pct_pop)))
    tally['_total'] = dict((cand, sum(v[cand] for v in tally.values())) for cand in candidates)
    for cand, total in list(tally['_total'].iteritems()):
        if total == 0 or cand == '_other':
            for v in tally.values():
                del v[cand]
    return dict(tally)
            
def proportional(ev, pcts):
    return [ev * k for k in pcts]

def proportional_rounded(ev, pcts):
    pcts = dict(enumerate(pcts))
    rounded = [None] * len(pcts)
    while pcts:
        total = sum(pcts.values())
        i, val = sorted(((i, ev * pct / total) for i, pct in pcts.iteritems()), key=lambda (i, val): abs(val - round(val)))[0]
        rounded[i] = round(val)
        ev -= rounded[i]
        del pcts[i]
    assert ev == 0
    return rounded

def top_two(ev, pcts):
    second_place = sorted(pcts)[-2]
    pcts = [0 if x < second_place else x for x in pcts]
    return proportional_rounded(ev, pcts)

def format(tally):
    cands = [c for c in candidates if c in tally['_total']]
    
    print """<table class="ev-tally">
<tr>
  <th></th>
  <th></th>"""
    for c in cands:
        print '  <th class="datahdr" colspan="2">%s</th>' % c
    print '</tr>'

    def print_row(state, tally):
        if state == '_total':
            name = 'Total'
        else:
            name = states[state]['state']
            name = {
                'District of Columbia': 'D.C.',
            }.get(name, name)

        print '<tr%s>' % (' class="total"' if state == '_total' else '')
        print '  <td>%s</td>' % name
        print '  <td class="data">%d</td>' % (TOTAL_EVS if state == '_total' else get_evs(state))
        for c in cands:
            val = tally[c]
            p = pct(val, TOTAL_EVS if state == '_total' else get_evs(state), 2 if state == '_total' else 0)
            if val == 0:
                print '  <td class="data" colspan="2">&mdash;</td>'
            elif state != '_total':
                print '  <td class="data evs">%.2f</td><td class="data pct">(%s)</td>' % (val, p)
            else:
                print '  <td class="data" colspan="2">%.1f<div class="total-pct">(%s)</div></td>' % (val, p)
        print '</tr>'

    for state, results in sorted(tally.iteritems(), key=lambda e: states.get(e[0], {}).get('state')):
        if state != '_total':
            print_row(state, results)
    print_row('_total', tally['_total'])
            
    print '</table>'
    print
    
def format_simple(tally):
    cands = [c for c in candidates if c in tally['_total']]
    
    print """<table class="ev-tally rounded">
<tr>
  <th></th>"""
    for c in cands:
        print '  <th class="datahdr">%s</th>' % c
    print '</tr>'

    def print_row(state, tally):
        if state == '_total':
            name = 'Total'
        else:
            name = states[state]['state']
            name = {
                'District of Columbia': 'D.C.',
            }.get(name, name)

        print '<tr%s>' % (' class="total"' if state == '_total' else '')
        print '  <td>%s</td>' % name
        for c in cands:
            val = tally[c]
            if val == 0:
                print '  <td class="data">&mdash;</td>'
            elif state != '_total':
                print '  <td class="data">%d</td>' % val
            else:
                print '  <td class="data">%d<div class="total-pct">(%s)</div></td>' % (val, pct(val, TOTAL_EVS))
        print '</tr>'

    for state, results in sorted(tally.iteritems(), key=lambda e: states.get(e[0], {}).get('state')):
        if state != '_total':
            print_row(state, results)
    print_row('_total', tally['_total'])
            
    print '</table>'
    print
    

def summarize(total_pop, pop, real_evs, prop, prop_int, top2):
    ordered_candidates = sorted(candidates, key=lambda c: -pop[c])
    assert sum(real_evs) == TOTAL_EVS
    real_evs = dict(zip(ordered_candidates, real_evs))
    pop = dict((k, v / total_pop) for k, v in pop.iteritems())
    
    print """<table class="summary">
<tr>
  <th></th>
  <th class="datahdr">Popular Vote</th>
  <th class="datahdr">Actual EVs&dagger;</th>
  <th class="datahdr">Proportional EVs</th>
  <th class="datahdr">Proportional EVs, rounded</th>
  <th class="datahdr">Top-2 EVs</th>
</tr>"""
    for i, cand in enumerate(ordered_candidates):
        if cand == '_other':
            continue

        def fmt_ev(evs, digits=0):
            ev = evs.get(cand, 0)
            mode = ''
            if ev == max(evs.values()):
                mode = 'tie' if len([x for x in evs.values() if x == max(evs.values())]) > 1 else 'winner'
            not_majority = (mode == 'winner' and ev <= .5*TOTAL_EVS)
            if ev == 0:
                return '<td class="data empty">&mdash;</td>'
            else:
                return '<td class="data%s">%.*f%s<div class="total-pct">(%s)</div></td>' % ((' ' + mode) if mode else '', digits, ev, '<sup style="color: red;">*</sup>' if not_majority else '', pct(ev, TOTAL_EVS))

        def fmt_pop(pop_pct):
            p = pop_pct[cand]
            mode = 'winner' if p == max(pop_pct.values()) else ''
            not_majority = (mode == 'winner' and p <= .5)
            return '<td class="data%s">%s%s</td>' % ((' ' + mode) if mode else '', pct(p, 1.), '<sup style="color: red;">*</sup>' if not_majority else '')

        print """<tr>
  <td>%s</td>
  %s
  %s
  %s
  %s
  %s
</tr>""" % (cand,
            fmt_pop(pop),
            fmt_ev(real_evs),
            fmt_ev(prop['_total'], 1),
            fmt_ev(prop_int['_total']),
            fmt_ev(top2['_total']),
)
    print '</table>'

    

# national popular vote
total_popular = sum(itertools.chain(*(v.values() for v in totals.values())))
cand_popular = collections.defaultdict(lambda: 0)
for vv in totals.values():
    for k, v in vv.iteritems():
        cand_popular[k] += v
for cand, vote in sorted(cand_popular.iteritems(), key=lambda e: -e[1]):
    print cand, pct(vote, total_popular)
print

prop = tally_state_evs(proportional)
prop_int = tally_state_evs(proportional_rounded)
top2 = tally_state_evs(top_two)

format(prop)
format_simple(prop_int)
format_simple(top2)

# ordered by popular vote
real_evs = {
    2016: [232, 306],
    2012: [332, 206],
    2008: [365, 173],
    2004: [286, 252],
    2000: [267, 271],
    1996: [379, 159],
    1992: [370, 168],
}

summarize(total_popular, cand_popular, real_evs[ELECTION], prop, prop_int, top2)
