
var results = {};
for (var i in race.summary) {
    var state = race.summary[i];
    var id = state.state;
    if (id == "US" || id.length > 2) {
	continue;
    }

    results[id] = {};
    for (var party in state.latest) {
	results[id][party] = {};
	var polls = state.latest[party].models.polls;

	results[id][party].mid = .01*polls.forecast;
	results[id][party].lo = .01*polls.lo;
	results[id][party].hi = .01*polls.hi;
    }
}
console.log(JSON.stringify(results));

