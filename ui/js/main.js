$(document).ready(function() {
	// Enable side-bar toggling
  $('[data-toggle=offcanvas]').click(function() {
    $('.row-offcanvas').toggleClass('active');
  });
	getScoreboard();
	getRemovedSpam();
	getFilterChanges();
	setGraphButtons();
	getGraph();
	getContentRemovals();
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
				$('<tr/>')
					.click(function() {
						// TODO Direct to user page
					})
					.appendTo( $('#scoreboard') )
					.append( $('<td class="text-right"/>').html(index + 1 ) )
					.append( $('<td class="text-center"/>').html(item.user ) )
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
				.append( $('<td/>').addClass('text-right').html(totalScore) )
				.append( $('<td/>').addClass('text-right').html(totalFilters) )
				.append( $('<td/>').addClass('text-right').html( (totalScore / totalFilters).toFixed(1) + '%') );
			
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
				.append( $('<th class="text-left">filter text</th>') )
				//.append( $('<th>spam?</th>') )
				.append( $('<th>credit</th>') );
			$.each(json.removed, function(index, item) {
				$('<tr/>')
					.click(function() {
						// TODO Error handling
					})
					.appendTo( $('#removed-spam') )
					.append( $('<td class="text-right"/>').html(new Date(item.date * 1000).toLocaleString() ) )
					.append( $('<td class="text-center"/>').html( $('<a/>').attr('href', item.permalink).html(item.posttype) ) )
					.append( $('<td class="text-center"/>').append( $('<span class="glyphicon glyphicon-' + getIconFromType(item.spamtype) + '"/>').html(' ' + item.spamtype)) )
					.append( $('<td class="text-left"/>').html(item.spamtext) )
					//.append( $('<td/>').html(item.is_spam ? 'yes' : 'no') )
					.append( $('<td/>').html(item.author  ) );
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
function getIconFromType(type) {
	return type.replace('text', 'pencil').replace('tld', 'globe').replace('thumb', 'picture');
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
				.append( $('<th class="text-right">user</th>') )
				.append( $('<th class="text-center">action</th>') )
				.append( $('<th>type</th>') )
				.append( $('<th>filter text</th>') );
			$.each(json.filter_changes, function(index, item) {
				$('<tr/>')
					.click(function() {
						// TODO Redirect to filter page
					})
					.appendTo( $('#filter-changes') )
					.append( $('<td class="text-right"/>').html(new Date(item.date * 1000).toLocaleString() ) )
					.append( $('<td class="text-right"/>').html(item.user    ) )
					.append( $('<td class="text-center"/>').append( $('<span class="glyphicon glyphicon-' + item.action.replace('added', 'plus').replace('removed', 'minus-sign') + '"/>') ) )
					.append( $('<td/>').append( $('<span class="glyphicon glyphicon-' + getIconFromType(item.spamtype) + '"/>').html(' ' + item.spamtype)) )
					.append( $('<td/>')
						.append(deleteFilterIcon(item.spamtype, item.spamtext))
						.append( $('<span/>').html(item.spamtext) ));
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

function deleteFilterIcon(type, text) {
	return $('<button type="button" class="btn btn-danger btn-xs"/>')
		.append( $('<span class="glyphicon glyphicon-remove"/>') )
		.attr('title', 'delete ' + type + ' filter "' + text + '"')
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
					text: '' + json.interval + ' interval',
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
					.append( $('<td class="text-right"/>').html(new Date(item.date * 1000).toLocaleString() ) )
					.append( $('<td class="text-center"/>').append( $('<span class="glyphicon glyphicon-minus-sign"/>') ) )
					.append( $('<td class="text-left"/>').html( $('<a/>').attr('href', item.permalink).html('post') ) )
					.append( $('<td class="text-left"/>').html(item.reason  ) );
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
