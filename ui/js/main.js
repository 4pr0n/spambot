$(document).ready(function() {
	getScoreboard();
	setGraphButtons();
	getGraph();

	createTable('spam', 'removed spam', 'remove', 'col-xs-12 col-lg-6');
	getSpam('spam');

	createTable('filter', 'filter changes', 'filter', 'col-xs-12 col-lg-6');
	getFilterChanges();

	createTable('sourced', 'sourced', 'saved', 'col-xs-12 col-md-3');
	getSources();

	createTable('removed', 'content removals', 'eye-close', 'col-xs-12 col-md-9');
	getContentRemovals();

	setAutoScrolls();
	setAutocomplete();

	var keys = getQueryHashKeys();
	if ('filter' in keys) {
		$('#container').fadeOut(500);
		$('#alt-container').fadeIn(500);
		if ('text' in keys) {
			// Get filter info for specific filter, populate main header
			getFilterInfo(keys['filter'], keys['text']);
			// Get removals for filter, insert below header
			createTable('alt-spam', 'spam removed by filter', 'remove', 'col-xs-12', '#alt-container');
			getSpam('alt-spam', 0, 10, keys['filter'], keys['text'])
		} else if (keys['filter'] == 'all') {
			// Display all filters (user/text/link/tld/thumb)
		} else {
			// Display just one type of filter (user/text/link/tld/thumb)
		}
	}
});

function getFilterInfo(type, text) {
	$('h1#title')
		.empty()
		.append( $('<em/>').html(text) )
		.append( '<p><small>' + type + ' filter</small>');
	var url = 'api.cgi?method=get_filter_info&type=' + type + '&text=' + encodeURIComponent(text);
	$.getJSON(url)
		.fail(function() { /* TODO */ })
		.done(function(json) {
			$('p#description')
				.empty()
				.append( 'created by <strong>' + json.user + '</strong> on ' + (new Date(json.date * 1000)).toLocaleString() )
				.append( $('<p/>') )
				.append( 'filter is <strong>' + (json.active ? '' : 'not ') + 'active</strong>' )
				.append( $('<p/>') )
				.append( 'filter ' + (json.is_spam ? '<strong>will</strong>' : 'will <strong>not</strong>') + ' remove posts and comments as spam' );
		});
}

/* Convert keys in hash to JS object */
function getQueryHashKeys() {
	var a = window.location.hash.substring(1).split('&');
	if (a == "") return {};
	var b = {};
	for (var i = 0; i < a.length; ++i) {
		var p=a[i].split('=');
		if (p.length != 2) continue;
		b[p[0]] = decodeURIComponent(p[1].replace(/\+/g, " "));
	}
	return b;
}

function createTable(name, title, icon, cols, appendto) {
	var $div = $('<div/>')
		.addClass(cols)
		.attr('id', name);
	$('<h2/>')
		.appendTo( $div )
		.append  ( $('<b/>').addClass('glyphicon glyphicon-' + icon) )
		.append  ( $('<span/>').html(' ' + title) );
	$('<p/>').appendTo( $div );
	$('<table/>')
		.appendTo( $div )
		.addClass('table table-striped table-condensed table-hover')
		.attr('id', name + '-table');
	$div.append( getNavButtons(name) );
	if (appendto === undefined) {
		appendto = '#container';
	}
	$(appendto).append( $div );
}

function getNavButtons(name) {
	var $center = $('<center/>');

	var $button = $('<button/>')
		.appendTo($center)
		.addClass('btn btn-default')
		.attr('type', 'button')
		.attr('id', name + '-back');
	$('<span/>').appendTo($button).addClass('glyphicon glyphicon-chevron-left');
	$('<span/>').appendTo($button).html(' back');

	$button = $('<button/>')
		.appendTo($center)
		.addClass('btn btn-default')
		.attr('type', 'button')
		.attr('id', name + '-next');
	$('<span/>').appendTo($button).html('next ');
	$('<span/>').appendTo($button).addClass('glyphicon glyphicon-chevron-right');
	return $center;
}

function getScoreboard() {
	$('#scoreboard')
		.stop()
		.animate({opacity : 0.1}, 1000);
	var url = window.location.pathname.replace(/\/filters/, '') + 'api.cgi?method=get_scoreboard';
	$.getJSON(url)
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
					.append( $( getUser(item.user) ) )
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

function getSpam(name, start, count, type, text) {
	if (start === undefined) start =  0;
	if (count === undefined) count = 10;
	$('#' + name + '-table')
		.stop()
		.animate({opacity : 0.1}, 1000);
	var url = window.location.pathname.replace(/\/filters/, '') + 'api.cgi?method=get_spam&start=' + start + '&count=' + count;
	if (type !== undefined && text !== undefined) {
		url += '&type=' + type + '&text=' + encodeURIComponent(text);
	}
	$.getJSON(url)
		.fail(function() {
			// TODO handle failure
		})
		.done(function(json) {
			if (json.error !== undefined) {
				// TODO Error handler
				return;
			}
			$('#' + name + '-table')
				.empty()
				.stop()
				.animate({opacity : 1.0}, 400);
			$('<tr/>')
				.appendTo( $('#' + name + '-table') )
				.append( $('<th class="text-right">date</th>') )
				.append( $('<th class="text-center">reddit</th>') )
				.append( $('<th>thx to</th>') )
				.append( $('<th class="text-left">filter</th>') );
			$.each(json.removed, function(index, item) {
				$('<tr/>')
					.click(function() {
						// TODO Error handling
					})
					.appendTo( $('#' + name + '-table') )
					.append( getDate(item.date) )
					.append( getRedditLink(item.permalink, item.posttype) )
					.append( getUser(item.user) )
					.append( getIconFromFilter(item.spamtype, item.spamtext, item.is_spam) );
			});

			// Back/next buttons
			if (start >= 10) {
				$('#' + name + '-back')
					.removeAttr('disabled')
					.unbind('click')
					.click(function() {
						getSpam(name, json.start - 20, json.count, type, text);
					});
			} else {
				$('#' + name + '-back')
					.attr('disabled', 'disabled');
			}
			$('#' + name + '-next')
				.unbind('click')
				.click(function() {
					getSpam(name, json.start, json.count, type, text);
				});
		});
}
function getUser(user) {
	if (user === '') user = '[internal]';
	var abbr = user
		.toLowerCase()
		.replace('pervertedbylanguage', 'pervertedby&hellip;')
		.replace('storm_troopers', 'stormtroopers');
	return $('<td/>')
		.addClass('text-left')
		.html('<small>' + abbr + '</small>' )
		.attr('title', user + ' is credited for creating this filter');
}
function getIconFromFilter(type, text) {
	var abbr = text;
	if (abbr.length > 16) {
		abbr = abbr.substring(0, 15) + '&hellip;';
	}
	return $('<td/>')
		.append(
				$('<span/>')
					.addClass('glyphicon')
					.addClass('glyphicon-' + 
							type.replace('text',  'pencil')
									.replace('tld',   'globe')
									.replace('thumb', 'picture'))
					.attr('title', type)
		)
		.append(
				$('<span/>')
					.addClass('text-warning')
					.attr('title', text)
					.html(' <small>' + abbr + '</small>') )
		.append(getDeleteIconForFilter(type, text));
}
function getDeleteIconForFilter(type, text) {
	return $('<button/>')
		.attr('type', 'button')
		.addClass('btn btn-danger btn-xs')
		.append( $('<span class="glyphicon glyphicon-remove"/>') )
		.attr('title', 'delete ' + type + ' filter "' + text + '" via a PM to /u/rachives on reddit')
		.css('margin-left', '5px')
		.click(function() {
			var params = {
				to      : 'rarchives',
				subject : 'dowhatisay',
				message : 'remove ' + type + ': ' + text,
			};
			window.open('http://www.reddit.com/message/compose/?' + $.param(params));
		});
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
	var d = new Date(date * 1000);
	var sd = [d.getFullYear(), d.getMonth(), d.getDate()].join('/');
	sd += ' ';
	if (d.getHours() < 10) sd += '0';
	sd += d.getHours() + ':';
	if (d.getMinutes() < 10) sd += '0';
	sd += d.getMinutes();
	return $('<td/>')
		.addClass('text-right')
		.html('<small>' + sd + '</small>');
}

function getFilterChanges(start, count) {
	if (start === undefined) start =  0;
	if (count === undefined) count = 10;
	$('#filter-table')
		.stop()
		.animate({opacity : 0.1}, 1000);
	var url = window.location.pathname.replace(/\/filters/, '') + 'api.cgi?method=get_filter_changes&start=' + start + '&count=' + count;
	$.getJSON(url)
		.fail(function() {
			// TODO handle failure
		})
		.done(function(json) {
			if (json.error !== undefined) {
				// TODO Error handler
				return;
			}
			$('#filter-table')
				.empty()
				.stop()
				.animate({opacity : 1.0}, 400);
			$('<tr/>')
				.appendTo( $('#filter-table') )
				.append( $('<th class="text-right">date</th>') )
				.append( $('<th class="text-center">user</th>') )
				.append( $('<th class="text-center">action</th>') )
				.append( $('<th class="text-left">filter</th>') );
			$.each(json.filter_changes, function(index, item) {
				$('<tr/>')
					.click(function() {
						// TODO Redirect to filter page
					})
					.appendTo( $('#filter-table') )
					.append( getDate(item.date) )
					.append( getUser(item.user) )
					.append( getIconFromAction(item.action) )
					.append( getIconFromFilter(item.spamtype, item.spamtext) );
			});

			// Back/next buttons
			if (start >= 10) {
				$('#filter-back')
					.removeAttr('disabled')
					.unbind('click')
					.click(function() {
						getFilterChanges(json.start - 20, json.count);
					});
			} else {
				$('#filter-back')
					.attr('disabled', 'disabled');
			}
			$('#filter-next')
				.unbind('click')
				.click(function() {
					getFilterChanges(json.start, json.count);
				});
		});
}

function getContentRemovals(start, count) {
	if (start === undefined) start =  0;
	if (count === undefined) count = 10;
	$('#removed-table')
		.stop()
		.animate({opacity : 0.1}, 1000);
	var url = window.location.pathname.replace(/\/filters/, '') + 'api.cgi?method=get_removals&start=' + start + '&count=' + count;
	$.getJSON(url)
		.fail(function() {
			// TODO handle failure
		})
		.done(function(json) {
			if (json.error !== undefined) {
				// TODO Error handler
				return;
			}
			$('#removed-table')
				.empty()
				.stop()
				.animate({opacity : 1.0}, 400);
			$('<tr/>')
				.appendTo( $('#removed-table') )
				.append( $('<th class="text-right">date</th>') )
				.append( $('<th class="text-left">link</th>') )
				.append( $('<th class="text-left">reason</th>') );
			$.each(json.content_removals, function(index, item) {
				$('<tr/>')
					.appendTo( $('#removed-table') )
					.append( getDate(item.date) )
					.append( getRedditLink(item.permalink, 'post') )
					.append( $('<td class="text-left text-info" title="' + item.reason.replace(/"/g, '&quot;') + '"/>').html(item.reason.substring(0, 25)  ) );
			});

			// Back/next buttons
			if (start >= 10) {
				$('#removed-back')
					.removeAttr('disabled')
					.unbind('click')
					.click(function() {
						getContentRemovals(json.start - 20, json.count);
					});
			} else {
				$('#removed-back')
					.attr('disabled', 'disabled');
			}
			$('#removed-next')
				.unbind('click')
				.click(function() {
					getContentRemovals(json.start, json.count);
				});
		});
}

function getSources(start, count) {
	if (start === undefined) start =  0;
	if (count === undefined) count = 10;
	$('#sourced-table')
		.stop()
		.animate({opacity : 0.1}, 1000);
	var url = 'api.cgi?method=get_sources&start=' + start + '&count=' + count;
	$.getJSON(url)
		.fail(function() {
			// TODO handle failure
		})
		.done(function(json) {
			if (json.error !== undefined) {
				// TODO Error handler
				return;
			}
			$('#sourced-table')
				.empty()
				.stop()
				.animate({opacity : 1.0}, 400);
			$('<tr/>')
				.appendTo( $('#sourced-table') )
				.append( $('<th class="text-right">date</th>') )
				.append( $('<th class="text-center">link</th>') )
				//.append( $('<th class="text-left">album</th>') )
			$.each(json.sources, function(index, item) {
				$('<tr/>')
					.appendTo( $('#sourced-table') )
					.append( getDate(item.date) )
					.append( getRedditLink(item.permalink, 'post') )
					//.append( $('<td class="text-left"/>  ').html( $('<a/>').attr('href', item.album).html(item.album) ) );
			});

			// Back/next buttons
			if (start >= 10) {
				$('#sourced-back')
					.removeAttr('disabled')
					.unbind('click')
					.click(function() {
						getSources(json.start - 20, json.count);
					});
			} else {
				$('#sourced-back')
					.attr('disabled', 'disabled');
			}
			$('#sourced-next')
				.unbind('click')
				.click(function() {
					getSources(json.start, json.count);
				});
		});
}

function getGraph(span, interval) {
	if (span     === undefined) span = 48;
	if (interval === undefined) interval = 3600;
	$('div#graph')
		.stop()
		.animate({opacity : 0.1}, 1000);
	var url = window.location.pathname.replace(/\/filters/, '') + 'api.cgi?method=get_graph&span=' + span + '&interval=' + interval;
	$.getJSON(url)
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
		['#nav-spam',     '#spam'],
		['#nav-graphs',   '#stats-anchor']
	];
	$.each(navids, function(index, item) {
		$(item[0]).mouseup(function() { this.blur() });
		$(item[0]).click(function() {
			$('a[id^="nav-"]').parent().removeClass('active');
			$(this).parent().addClass('active').blur();
			if ( $('.navbar-collapse').hasClass('in') ) {
				// If navbar is showing, hide it before scrolling
				$('.navbar-toggle').click();
				setTimeout(function() {
					$('html,body')
						.stop()
						.animate({
							'scrollTop': $(item[1]).offset().top - $('.navbar').height(),
						}, 500);
				}, 250);
			} else {
				$('html,body')
					.stop()
					.animate({
						'scrollTop': $(item[1]).offset().top - $('.navbar').height(),
					}, 500);
			}
		});
	});
}

function setAutocomplete() {
	var url = window.location.pathname.replace(/\/filters/, '') + 'api.cgi?method=search_filters&q=%QUERY&limit=10';
	$('#search-filters').typeahead([
		{
			name: 'spam-filters',
			remote: url,
			template: '<table><tr><td><span class="glyphicon glyphicon-{{icon}}" title="{{type}} filter"></span></td><td style="padding-left: 10px">{{text}}</td></tr></table>',
			valueKey: 'text',
			limit: 10,
			engine: Hogan
		}
	])
	.focusin(function() {
		$(this).stop().animate( {
			'width': ($(window).width() - $(this).offset().left - 50) + 'px'
		}, 200);
	})
	.focusout(function() {
		$(this).stop().animate( {
			'width': '150px'
		}, 200);
	})
	.css('width', '150px');
}
