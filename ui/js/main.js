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
				.append( $('<th class="text-left">filter text</th>') )
				//.append( $('<th>spam?</th>') )
				.append( $('<th>admin</th>') );
			$.each(json.removed, function(index, item) {
				$('<tr/>')
					.click(function() {
						// TODO Error handling
					})
					.appendTo( $('#removed-spam') )
					.append( $('<td class="text-center"/>').html('<small>' + new Date(item.date * 1000).toLocaleString()  + '</small>') )
					.append( $('<td class="text-center"/>').html( $('<a/>').attr('href', item.permalink).html(item.posttype.substring(0, 4)) ) )
					.append( $('<td class="text-center"/>').append( $('<span class="glyphicon glyphicon-' + getIconFromType(item.spamtype) + '"/>').attr('title', item.spamtype).html('')) )
					.append( $('<td/>')
						.append(deleteFilterIcon(item.spamtype, item.spamtext))
						.append( $('<span class="text-warning"/>').html('<small>' + item.spamtext + '</small>') ))
					//.append( $('<td/>').html(item.is_spam ? 'yes' : 'no') )
					.append( $('<td/>').html('<small>' + item.author.replace('pervertedbylanguage', 'pervertedby&hellip;') + '</small>' ) );
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
					.append( $('<td class="text-right"/>').html('<small>' + new Date(item.date * 1000).toLocaleString()  + '</small>') )
					.append( $('<td class="text-right"/>').html(item.user    ) )
					.append( $('<td class="text-center"/>').append( $('<span class="glyphicon glyphicon-' + item.action.replace('added', 'plus').replace('removed', 'minus-sign') + '"/>') ) )
					.append( $('<td/>').append( $('<span class="glyphicon glyphicon-' + getIconFromType(item.spamtype) + '"/>').attr('title', item.spamtype).html('')) )
					.append( $('<td/>')
						.append(deleteFilterIcon(item.spamtype, item.spamtext))
						.append( $('<span class="text-warning"/>').html('<small>' + item.spamtext + '</small>') ));
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
					.append( $('<td class="text-center"/>').append( $('<span class="glyphicon glyphicon-minus-sign"/>') ) )
					.append( $('<td class="text-left"/>').html( $('<a/>').attr('href', item.permalink).html('post') ) )
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
				.append( $('<th class="text-center">date</th>') )
				.append( $('<th class="text-center">post</th>') )
				//.append( $('<th class="text-left">album</th>') )
			$.each(json.sources, function(index, item) {
				$('<tr/>')
					.appendTo( $('#sources') )
					.append( $('<td class="text-center"/>').html('<small>' + new Date(item.date * 1000).toLocaleString()  + '</small>') )
					.append( $('<td class="text-center"/>').html( $('<a/>').attr('href', item.permalink).html('post') ) )
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
