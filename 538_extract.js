
/** 
 * run in dev console on http://projects.fivethirtyeight.com/2016-election-forecast/
 * to extract per-state poll predictions and error bars
 */

var results = {};
for (var i in race.summary) {
    var state = race.summary[i];
    var id = state.state;
    if (id == "US" || id.length > 2) {
	// skip nationwide and states that break out by congressional district
	continue;
    }

    results[id] = {};
    for (var party in state.latest) {
	results[id][party] = {};
	var polls = state.latest[party].models.polls;

	results[id][party].mid = .01*polls.forecast;
	results[id][party].lo = .01*polls.lo;  // 10th pctile
	results[id][party].hi = .01*polls.hi;  // 90th pctile
    }
}
console.log(JSON.stringify(results));

