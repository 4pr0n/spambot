$(document).ready(function() {
	// Enable side-bar toggling
  $('[data-toggle=offcanvas]').click(function() {
    $('.row-offcanvas').toggleClass('active');
  });
	getScoreboard();
	getRemovedSpam();
	getFilterChanges();
	setGraphButtons();
	getContentRemovals();
	getSources();
	getGraph();
	setAutoScrolls();
	setAutocomplete();
});

function getScoreboard() {
	$('#scoreboard')
		.stop()
		.animate({opacity : 0.1}, 1000);
	$.getJSON('api.cgi?method=get_scoreboard')
		.fail(function() {
			// TODO handle failure
		})
		.done(function(json) {
			if (json.error !== undefined) {
				// TODO Error handler
				return;
			}
			$('#scoreboard')
				.empty()
				.stop()
				.animate({opacity : 1.0}, 400);
			$('<tr/>')
				.appendTo( $('#scoreboard') )
				.append( $('<th class="text-right">#</th>') )
				.append( $('<th class="text-center">admin</th>') )
				.append( $('<th class="text-right">score</th>') )
				.append( $('<th class="text-right">filters</th>') )
				.append( $('<th class="text-right">%</th>') );
			// Build scoreboard
			var totalScore = 0, totalFilters = 0;
			$.each(json.scoreboard, function(index, item) {
				totalScore += item.score;
				totalFilters += item.filters;
				if (item.user == '') item.user = '[internal filters]';
				$('<tr/>')
					.click(function() {
						// TODO Direct to user page
					})
					.appendTo( $('#scoreboard') )
					.append( $('<td class="text-right"/>').html(index + 1 ) )
					.append( $('<td class="text-center text-info"/>').html('<strong>' + item.user + '</strong>') )
					.append( $('<td class="text-right"/>').html(item.score) )
					.append( $('<td class="text-right"/>').html(item.filters) )
					.append( $('<td class="text-right"/>').html( (item.score / item.filters).toFixed(1) + '%') );
			});
			$('<tr/>')
				.click(function() {
					// TODO Direct to user page
				})
				.appendTo( $('#scoreboard') )
				.append( $('<td/>') )
				.append( $('<td/>').addClass('text-center').html('') )
				.append( $('<td/>').addClass('text-right').html('<strong>' + totalScore + '</strong>') )
				.append( $('<td/>').addClass('text-right').html('<strong>' + totalFilters + '</strong>') )
				.append( $('<td/>').addClass('text-right').html('<strong>' + (totalScore / totalFilters).toFixed(1) + '%</strong>'));
			
		});
}

function getRemovedSpam(start, count) {
	if (start === undefined) start =  0;
	if (count === undefined) count = 10;
	$('#removed-spam')
		.stop()
		.animate({opacity : 0.1}, 1000);
	$.getJSON('api.cgi?method=get_removed&start=' + start + '&count=' + count)
		.fail(function() {
			// TODO handle failure
		})
		.done(function(json) {
			if (json.error !== undefined) {
				// TODO Error handler
				return;
			}
			$('#removed-spam')
				.empty()
				.stop()
				.animate({opacity : 1.0}, 400);
			$('<tr/>')
				.appendTo( $('#removed-spam') )
				.append( $('<th class="text-right">date</th>') )
				.append( $('<th class="text-center">reddit</th>') )
				.append( $('<th class="text-center">type</th>') )
				.append( $('<th>thx to</th>') )
				.append( $('<th class="text-left">filter text</th>') );
			$.each(json.removed, function(index, item) {
				$('<tr/>')
					.click(function() {
						// TODO Error handling
					})
					.appendTo( $('#removed-spam') )
					.append( getDate(item.date) )
					.append( getRedditLink(item.permalink, item.posttype) )
					.append( getIconFromSpamType(item.spamtype) )
					.append( getUser(item.author) )
					.append( getIconFromFilter(item.spamtype, item.spamtext, item.is_spam) );
			});

			// Back/next buttons
			if (start >= 10) {
				$('#removed-spam-back')
					.removeAttr('disabled')
					.unbind('click')
					.click(function() {
						getRemovedSpam(json.start - 20, json.count);
					});
			} else {
				$('#removed-spam-back')
					.attr('disabled', 'disabled');
			}
			$('#removed-spam-next')
				.unbind('click')
				.click(function() {
					getRemovedSpam(json.start, json.count);
				});
		});
}
function getUser(user) {
	var abbr = user
		.toLowerCase()
		.replace('pervertedbylanguage', 'pervertedby&hellip;')
		.replace('storm_troopers', 'stormtroopers');
	return $('<td/>')
		.addClass('text-left')
		.html('<small>' + abbr + '</small>' )
		.attr('title', user + ' is credited for creating this filter');
}
function getIconFromSpamType(type) {
	return $('<td/>')
		.addClass('text-center')
		.append(
				$('<span/>')
					.addClass('glyphicon')
					.addClass('glyphicon-' + 
							type.replace('text',  'pencil')
									.replace('tld',   'globe')
									.replace('thumb', 'picture'))
					.attr('title', type)
			);
}
function getIconFromFilter(type, text) {
	var abbr = text;
	if (abbr.length > 16) {
		abbr = abbr.substring(0, 15) + '&hellip;';
	}
	return $('<td/>')
		.append(getDeleteIconForFilter(type, text))
		.append(
				$('<span/>')
					.addClass('text-warning')
					.attr('title', text)
					.html('<small>' + abbr + '</small>') );
}
function getRedditLink(permalink, posttype) {
	return $('<td/>')
		.addClass('text-center')
		.append(
			$('<a/>')
			.attr('href', permalink)
			.html( posttype.substring(0, 4) )
			.attr('title', 'link to the post on reddit: ' + permalink)
		);
}
function getIconFromAction(action) {
	return $('<td/>')
		.addClass('text-center')
		.append(
			$('<span/>')
				.addClass('glyphicon')
				.addClass('glyphicon-' + 
						action.replace('added',   'plus')
									.replace('removed', 'minus-sign'))
				.attr('title', action)
		);
}
function getDate(date) {
	return $('<td/>')
		.addClass('text-right')
		.html('<small>' + (new Date(date * 1000).toLocaleString()) + '</small>');
}

function getFilterChanges(start, count) {
	if (start === undefined) start =  0;
	if (count === undefined) count = 10;
	$('#filter-changes')
		.stop()
		.animate({opacity : 0.1}, 1000);
	$.getJSON('api.cgi?method=get_filter&start=' + start + '&count=' + count)
		.fail(function() {
			// TODO handle failure
		})
		.done(function(json) {
			if (json.error !== undefined) {
				// TODO Error handler
				return;
			}
			$('#filter-changes')
				.empty()
				.stop()
				.animate({opacity : 1.0}, 400);
			$('<tr/>')
				.appendTo( $('#filter-changes') )
				.append( $('<th class="text-right">date</th>') )
				.append( $('<th class="text-center">user</th>') )
				.append( $('<th class="text-center">action</th>') )
				.append( $('<th class="text-center">type</th>') )
				.append( $('<th class="text-left">filter text</th>') );
			$.each(json.filter_changes, function(index, item) {
				$('<tr/>')
					.click(function() {
						// TODO Redirect to filter page
					})
					.appendTo( $('#filter-changes') )
					.append( getDate(item.date) )
					.append( getUser(item.user) )
					.append( getIconFromAction(item.action) )
					.append( getIconFromSpamType(item.spamtype) )
					.append( getIconFromFilter(item.spamtype, item.spamtext) );
			});

			// Back/next buttons
			if (start >= 10) {
				$('#filter-changes-back')
					.removeAttr('disabled')
					.unbind('click')
					.click(function() {
						getFilterChanges(json.start - 20, json.count);
					});
			} else {
				$('#filter-changes-back')
					.attr('disabled', 'disabled');
			}
			$('#filter-changes-next')
				.unbind('click')
				.click(function() {
					getFilterChanges(json.start, json.count);
				});
		});
}

function getContentRemovals(start, count) {
	if (start === undefined) start =  0;
	if (count === undefined) count = 10;
	$('#content-removals')
		.stop()
		.animate({opacity : 0.1}, 1000);
	$.getJSON('api.cgi?method=get_content_removals&start=' + start + '&count=' + count)
		.fail(function() {
			// TODO handle failure
		})
		.done(function(json) {
			if (json.error !== undefined) {
				// TODO Error handler
				return;
			}
			$('#content-removals')
				.empty()
				.stop()
				.animate({opacity : 1.0}, 400);
			$('<tr/>')
				.appendTo( $('#content-removals') )
				.append( $('<th class="text-right">date</th>') )
				.append( $('<th class="text-center">action</th>') )
				.append( $('<th class="text-left">link</th>') )
				.append( $('<th class="text-left">reason</th>') );
			$.each(json.content_removals, function(index, item) {
				$('<tr/>')
					.appendTo( $('#content-removals') )
					.append( $('<td class="text-right"/>').html('<small>' + new Date(item.date * 1000).toLocaleString()  + '</small>') )
					.append( getIconFromAction(item.action) )
					.append( getRedditLink(item.permalink, 'post') )
					.append( $('<td class="text-left text-info"/>').html(item.reason  ) );
			});

			// Back/next buttons
			if (start >= 10) {
				$('#content-removals-back')
					.removeAttr('disabled')
					.unbind('click')
					.click(function() {
						getContentRemovals(json.start - 20, json.count);
					});
			} else {
				$('#content-removals-back')
					.attr('disabled', 'disabled');
			}
			$('#content-removals-next')
				.unbind('click')
				.click(function() {
					getContentRemovals(json.start, json.count);
				});
		});
}

function getSources(start, count) {
	if (start === undefined) start =  0;
	if (count === undefined) count = 10;
	$('#sources')
		.stop()
		.animate({opacity : 0.1}, 1000);
	$.getJSON('api.cgi?method=get_sources&start=' + start + '&count=' + count)
		.fail(function() {
			// TODO handle failure
		})
		.done(function(json) {
			if (json.error !== undefined) {
				// TODO Error handler
				return;
			}
			$('#sources')
				.empty()
				.stop()
				.animate({opacity : 1.0}, 400);
			$('<tr/>')
				.appendTo( $('#sources') )
				.append( $('<th class="text-right">date</th>') )
				.append( $('<th class="text-center">link</th>') )
				//.append( $('<th class="text-left">album</th>') )
			$.each(json.sources, function(index, item) {
				$('<tr/>')
					.appendTo( $('#sources') )
					.append( getDate(item.date) )
					.append( getRedditLink(item.permalink, 'post') )
					//.append( $('<td class="text-left"/>  ').html( $('<a/>').attr('href', item.album).html(item.album) ) );
			});

			// Back/next buttons
			if (start >= 10) {
				$('#sources-back')
					.removeAttr('disabled')
					.unbind('click')
					.click(function() {
						getSources(json.start - 20, json.count);
					});
			} else {
				$('#sources-back')
					.attr('disabled', 'disabled');
			}
			$('#sources-next')
				.unbind('click')
				.click(function() {
					getSources(json.start, json.count);
				});
		});
}

function getDeleteIconForFilter(type, text) {
	return $('<button/>')
		.attr('type', 'button')
		.addClass('btn btn-danger btn-xs')
		.append( $('<span class="glyphicon glyphicon-remove"/>') )
		.attr('title', 'delete ' + type + ' filter "' + text + '" via a PM to /u/rachives on reddit')
		.css('margin-right', '5px')
		.click(function() {
			var params = {
				to      : 'rarchives',
				subject : 'dowhatisay',
				message : 'remove ' + type + ': ' + text,
			};
			window.open('http://www.reddit.com/message/compose/?' + $.param(params));
		});
}

function getGraph(span, interval) {
	if (span     === undefined) span = 48;
	if (interval === undefined) interval = 3600;
	$('div#graph')
		.stop()
		.animate({opacity : 0.1}, 1000);
	$.getJSON('api.cgi?method=get_graph&span=' + span + '&interval=' + interval)
		.fail(function() {
			// TODO error handler
		})
		.done(function(json) {
			// Show graph
			$('div#graph')
				.empty()
				.stop()
				.animate({opacity : 1.0}, 400);
			$('#recent-range').html('past ' + json.window);
			Highcharts.setOptions({
				global: { useUTC: false }
			});
			var chart = new Highcharts.Chart({
				chart: {
					renderTo: $('div#graph')[0],
					type: 'line',
					borderRadius: '20px',
				},
				title: {
					text: null,
				},
				xAxis: {
					type: 'datetime',
				},
				yAxis: {
					type: 'linear',
					title: 'removals',
					min: 0,
				},
				plotOptions: {
					series: {
						pointStart: json.pointStart,
						pointInterval: json.pointInterval,
					},
				},
				legend: {
					align: 'bottom',
					layout: 'horizontal',
					verticalAlign: 'bottom',
					align: 'center',
					itemMarginTop: 10,
					itemMarginBottom: 10,
				},
			
				credits: {
					enabled: true,
					text: '' + json.interval.replace(/s$/, '') + ' intervals',
					align: 'left',
					href: null,
					position: {
						align: 'left',
						x: 10,
						verticalAlign: 'bottom',
						y: -15,
					},
				},
				series: json.series,
			}); // End of Highcharts
			$('button[id^="graph-"]').removeClass('active').removeAttr('disabled');
			$('button#graph-' + json.window.replace(' ', '-')).addClass('active').attr('disabled', 'disabled');
		}); // End of getJSON.done()
}

function setGraphButtons() {
	var d = [
		['6-hours',   36,       600], // 21600    @ 10m
		['day',       48,      1800], // 86400    @ 30m
		['2-days',    48,      3600], // 172800   @  1h
		['7-days',    56,     10800], // 604800   @  3h
		['month',     60,   3600*12], // 2592000  @ 12h
		['6-months',  60, 3600*24*3], // 15552000 @  3d
		['year',      52, 3600*24*7], // 31449600 @  7d
	];
	$.each(d, function(index, item) {
		$('button#graph-' + item[0]).click(function() {
			$(this).addClass('active').attr('disabled', 'disabled');
			getGraph(item[1], item[2]);
		});
	});
}

function setAutoScrolls() {
	var navids = [
		['#nav-home',     'div.jumbotron'],
		['.navbar-brand', 'div.jumbotron'],
		['#nav-scores',   '#scores-anchor'],
		['#nav-removed',  '#removed-anchor'],
		['#nav-graphs',   '#graph-anchor']
	];
	$.each(navids, function(index, item) {
		$(item[0]).click(function() {
			$('a[id^="nav-"]').parent().removeClass('active');
			$(this).parent().addClass('active').blur();
			$('html,body')
				.animate({
					'scrollTop': $(item[1]).offset().top - $('.navbar').height() - 10,
				}, 500);
		});
	});
}

function setAutocomplete() {
	$('#search-filters').typeahead([
		{
			name: 'spam-filters',
			remote: 'api.cgi?method=search_filters&q=%QUERY&limit=10',
			template: '<table><tr><td><span class="glyphicon glyphicon-{{icon}}" title="{{type}} filter"></span></td><td style="padding-left: 10px">{{text}}</td></tr></table>',
			valueKey: 'text',
			limit: 10,
			engine: Hogan
		}
	]);
}
