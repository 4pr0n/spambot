$(document).ready(function() {
	getScoreboard();
	setGraphButtons();
	getGraph();

	getSpam('spam');
	getFilterChanges();
	getSources();
	getContentRemovals();
	getModeratedSubreddits();

	setAutocomplete();

	setAllRedirects();
	checkForPageChange();

	// Update status of bot
	checkIsBotActive();
	setInterval(checkIsBotActive, 10 * 1000);
});

/**
 * Sets up 'redirects' which "reload" the page with a specific hash.
 */
function setAllRedirects() {
	var redirs = [
		['a#nav-add-filter', 'add'],
		['a#view-filter-all', 'filter=all'],
		['a#view-filter-tld', 'filter=tld'],
		['a#view-filter-link', 'filter=link'],
		['a#view-filter-text', 'filter=text'],
		['a#view-filter-user', 'filter=user'],
		['a#view-filter-thumb', 'filter=thumb'],
		['a#view-about-site', 'about=site'],
		['a#view-about-mods', 'about=mods'],
		['a#view-about-code', 'about=code'],
		['a.navbar-brand', 'home'],
		['a#nav-spam', 'spam'],
		['a#nav-stats', 'stats'],
	];
	$.each(redirs, function(index, item) {
		$(item[0]).click(function() {
			window.location.hash = item[1];
			checkForPageChange();
		});
	});
}

/**
 * Parses the URL's hash and decides what to load.
 */
function checkForPageChange() {
	var keys = getQueryHashKeys();
	// Hash points to something on the main page (requires scrolling to an element)
	if (window.location.hash === '' || window.location.hash === '#' ||
			'home'   in keys ||
			'stats'  in keys || 
			'scores' in keys || 
			'spam'   in keys || 
			'mod'    in keys   ) {
		// Display main page
		$('body .container[id^="container-"]:visible')
			.filter(function() {
				return this.id !== 'container-main';
			})
			.stop()
			.fadeOut(200);
		if (!$('#container-main').is(':visible')) {
			$('#container-main')
				.stop()
				.fadeIn(500);
		}
		// Scroll up
		var $elem = $('#container-main');
		if      ('stats'  in keys) { $elem = $('#stats-div' ); }
		else if ('scores' in keys) { $elem = $('#scores-div'); }
		else if ('spam'   in keys) { $elem = $('#spam-div'  ); }
		else if ('mod'    in keys) { $elem = $('#modded-div'); }
		// If navbar is showing, hide it before scrolling
		var wait = 0;
		if ( $('.navbar-collapse').hasClass('in') ) { 
			$('.navbar-toggle').click();
			wait = 200;
		}
		setTimeout(
			function() {
				$('html,body')
					.stop()
					.animate({
						'scrollTop': $elem.offset().top - $('.navbar').height(),
					}, 500);
			}, wait);
	}

	else if ('about' in keys) {
		showPage('container-about-' + keys['about']);
	}

	else if ('add' in keys) {
		showPage('container-filters-add');
	}

	else if ('filter' in keys) {
		if ('text' in keys) {
			// Display specific filter
			showPage('container-filter-single');
			// Get filter info for specific filter, populate jumbotron
			getFilterInfo(keys.filter, keys.text);
			// Get removals for filter
			getSpam('filter-single-spam', 0, 20, keys.filter, keys.text)
		}
		else {
			// Display one or all filters
			showPage('container-filter-type');
			$('div#container-filter-type h1#filters')
				.html(keys.filter + ' filters');
			$('div#container-filter-type p#filters')
				.html('full list of ' + keys.filter + ' filters used by the bot to detect and remove spam');
			if (keys.filter === 'all') {
				$('div#container-filter-type div[id^="filter-"]')
					.stop()
					.fadeIn(200);
				$.each( $('div#container-filter-type table[id^="filter-"]'),
					function(index, item) {
						getFilters($(item).parent().attr('id'), $(item).parent().attr('name'), 0, 10);
					}
				);
			}
			else {
				$('div#container-filter-type div.row div[id!="filter-' + keys.filter + '"]')
					.stop()
					.fadeOut(200);
				$('div#container-filter-type div.row div#filter-' + keys.filter)
					.stop()
					.fadeIn(200);
				getFilters('filter-' + keys.filter, keys.filter, 0, 20);
			}
		}
	}
	else {
		// Unexpected hash tag. Set the default
		window.location.hash = '';
		checkForPageChange();
	}
}

function getFilterInfo(type, text) {
	$('div#container-filter-single h1#filters')
		.empty()
		.append( $('<small>' + type + ' filter for</small> <em>' + text + '</em>') )
	var url = 'api.cgi?method=get_filter_info&type=' + type + '&text=' + encodeURIComponent(text);
	$.getJSON(url)
		.fail(function() { /* TODO */ })
		.done(function(json) {
			$('div#container-filter-single p#filters')
				.empty()
				.append( '<strong>' + json.count + '</strong> removal' + (json.count == 1 ? '' : 's') )
				.append( $('<p/>') )
				.append( 'created by <strong>' + getUser(json.user).html() + '</strong> on ' + (new Date(json.date * 1000)).toLocaleString() )
				.append( $('<p/>') )
				.append( 'filter is <strong>' + (json.active ? '<b class="text-success">active</b>' : '<b class="text-danger">inactive</b>') + '</strong>' );
			if (json.active) {
				$('div#container-filter-single p#filters')
					.append( $('<p/>') )
					.append( 'filter ' + (json.is_spam ? '<strong>will</strong>' : 'will <strong>not</strong>') + ' remove posts and comments as spam' );
			}
		});
}

/* Convert keys in hash to JS object */
function getQueryHashKeys() {
	var a = window.location.hash.substring(1).split('&');
	if (a == "") return {};
	var b = {};
	for (var i = 0; i < a.length; ++i) {
		var p=a[i].split('=');
		if (p.length != 2) {
			b[p[0]] = '';
			continue;
		}
		b[p[0]] = decodeURIComponent(p[1].replace(/\+/g, " "));
	}
	return b;
}

function getScoreboard() {
	$('#scores-table')
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
			$('#scores-table')
				.empty()
				.stop()
				.animate({opacity : 1.0}, 400);
			$('<tr/>')
				.appendTo( $('#scores-table') )
				.append( $('<th class="text-right">#</th>') )
				.append( $('<th class="text-center">admin</th>') )
				.append( $('<th class="text-right">score</th>') )
				.append( $('<th class="text-right">filters</th>') )
				.append( $('<th class="text-right">ratio</th>') );
			// Build scoreboard
			var totalScore = 0, totalFilters = 0;
			$.each(json.scoreboard, function(index, item) {
				totalScore += item.score;
				totalFilters += item.filters;
				$('<tr/>')
					.click(function() {
						// TODO Direct to user page
					})
					.appendTo( $('#scores-table') )
					.append( $('<td class="text-right"/>').html(index + 1 ) )
					.append( $( getUser(item.user) ) )
					.append( $('<td class="text-right"/>').html(item.score) )
					.append( $('<td class="text-right"/>').html(item.filters) )
					.append( $('<td class="text-right"/>').html( (item.score / item.filters).toFixed(1) + '') );
			});
			$('<tr/>')
				.click(function() {
					// TODO Direct to user page
				})
				.appendTo( $('#scores-table') )
				.append( $('<td/>') )
				.append( $('<td/>').addClass('text-center').html('') )
				.append( $('<td/>').addClass('text-right').html('<strong>' + totalScore + '</strong>') )
				.append( $('<td/>').addClass('text-right').html('<strong>' + totalFilters + '</strong>') )
				.append( $('<td/>').addClass('text-right').html('<strong>' + (totalScore / totalFilters).toFixed(1) + '</strong>'));
			
		});
}

function getFilters(name, type, start, count) {
	if (start === undefined) start =  0;
	if (count === undefined) count = 10;
	$('#' + name + '-table')
		.stop()
		.animate({opacity : 0.1}, 1000);
	var url = 'api.cgi?method=get_filters&start=' + start + '&count=' + count + '&type=' + type;
	console.log(url);
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
				.append( $('<th class="text-center">creator</th>') )
				.append( $('<th class="text-center">#</th>') )
				.append( $('<th class="text-left">filter</th>') );
			$.each(json.filters, function(index, item) {
				$('<tr/>')
					.click(function() {
						// TODO Error handling
					})
					.appendTo( $('#' + name + '-table') )
					.append( getDate(item.date) )
					.append( getUser(item.user) )
					.append( $('<td class="text-center"/>').html( item.count ) )
					.append( getIconFromFilter(item.spamtype, item.spamtext, item.is_spam) );
			});

			$('#' + name + '-title').html(' ' + json.total + ' ' + type + ' filters');
			// Back/next buttons
			if (start >= 10) {
				$('#' + name + '-back')
					.removeAttr('disabled')
					.unbind('click')
					.click(function() {
						getFilters(name, type, json.start - count * 2, json.count);
					});
			} else {
				$('#' + name + '-back')
					.attr('disabled', 'disabled');
			}
			$('#' + name + '-next')
				.unbind('click')
				.click(function() {
					getFilters(name, type, json.start, json.count);
				});
		});
}
/* Queries for removed posts, adds to table. Handles back/next buttons */
function getSpam(name, start, count, type, text) {
	if (start === undefined) start =  0;
	if (count === undefined) count = 10;
	$('#' + name + '-table')
		.stop()
		.animate({opacity : 0.1}, 1000);
	var url = 'api.cgi?method=get_spam&start=' + start + '&count=' + count;
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
				.append( $('<th class="text-center">thx to</th>') )
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
						getSpam(name, json.start - count * 2, json.count, type, text);
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
		.addClass('text-center')
		.html('<small>' + abbr + '</small>' );
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
						type.replace('text',     'pencil')
						    .replace('tld',      'globe')
						    .replace('thumb',    'picture')
						    .replace('tumblr',   'text-width')
								.replace('blogspot', 'bold')
					)
					.attr('title', type)
		)
		.append(
				$('<span/>')
					.addClass('text-warning')
					.attr('title', text)
					.append( $('<a/>')
						.attr('href', '#filter=' + type + '&text=' + text)
						.html('<small> ' + abbr + '</small>')
						.click(function() {
							window.location.hash = $(this).attr('href').replace('#', '');
							checkForPageChange();
						})
					)
			)
		.append(getDeleteIconForFilter(type, text));
}
function getDeleteIconForFilter(type, text) {
	return $('<button/>')
		.attr('type', 'button')
		.addClass('btn btn-danger btn-xs')
		.css('float', 'right')
		.append( $('<span class="glyphicon glyphicon-remove"/>') )
		.attr('title', 'delete ' + type + ' filter "' + text + '" via a PM to /u/rachives on reddit')
		.css('margin-left', '5px')
		.click(function() {
			sendPM('remove ' + type + ': ' + text);
		});
}

function sendPM(body) {
	var params = {
		to      : 'rarchives',
		subject : 'dowhatisay',
		message : body,
	};
	window.open('http://www.reddit.com/message/compose/?' + $.param(params));
}

function getRedditLink(permalink, posttype) {
	var txt = posttype.substring(0, 4);
	if (permalink.indexOf('/r/') >= 0) {
		txt = permalink.substring(permalink.indexOf('/r/') + 3);
		txt = txt.substring(0, txt.indexOf('/'));
		txt = '<small>' + txt + '</small>';
	}
	return $('<td/>')
		.addClass('text-center')
		.append(
			$('<a/>')
			.attr('href', permalink)
			.attr('target', '_BLANK_' + permalink)
			.html( txt )
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
				.append( $('<th class="text-center">link</th>') )
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

function getModeratedSubreddits(start, count) {
	var columns = 3;
	if (start === undefined) start =  0;
	if (count === undefined) count = columns * 10;
	$('#modded-table')
		.stop()
		.animate({opacity : 0.1}, 1000);
	var url = 'api.cgi?method=get_modded_subs&start=' + start + '&count=' + count;
	$.getJSON(url)
		.fail(function() {
			// TODO handle failure
		})
		.done(function(json) {
			if (json.error !== undefined) {
				// TODO Error handler
				return;
			}
			$('#modded-table')
				.empty()
				.stop()
				.animate({opacity : 1.0}, 400);
			$('<tr/>')
				.appendTo( $('#modded-table') )
				.append( $('<th class="text-center" colspan="' + columns + '">moderated subreddits</th>') );
			var $tr = $('<tr/>')
				.appendTo( $('#modded-table') );
			for (var i = 0; i < json.subreddits.length; i++) {
				if (i % columns == 0 && i != 0) {
					$tr = $('<tr/>').appendTo( $('#modded-table') );
				}
				var item = json.subreddits[i];
				$('<td class="text-center"/>')
					.append(
						$('<a/>')
							.attr('href', 'http://reddit.com/r/' + item)
							.attr('target', '_BLANK_' + item)
							.html('/r/' + item)
					)
					.appendTo( $tr );
			}

			$('#modded-title').html(' ' + json.total + ' modded subs');
			// Back/next buttons
			if (start >= 10) {
				$('#modded-back')
					.removeAttr('disabled')
					.unbind('click')
					.click(function() {
						getModeratedSubreddits(json.start - 20, json.count);
					});
			} else {
				$('#modded-back')
					.attr('disabled', 'disabled');
			}
			$('#modded-next')
				.unbind('click')
				.click(function() {
					getModeratedSubreddits(json.start, json.count);
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
				},
			
				credits: {
					enabled: true,
					text: '' + json.interval.replace(/s$/, '') + ' intervals',
					align: 'left',
					href: null,
					position: {
						align: 'left',
						x: 10,
						verticalAlign: 'bottom'
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

/**
 * Sets up autocomplete for search and add-filter textboxes
 */
function setAutocomplete() {
	var url = 'api.cgi?method=search_filters&q=%QUERY&limit=10';
	var temp = '<table><tr><td>';
	temp += '<span class="glyphicon glyphicon-{{icon}}" title="{{type}} filter"></span>';
	temp += '</td><td style="padding-left: 10px">';
	temp += '<a href="#filter={{type}}&text={{text}}">{{text}}</a>';
	temp += '</td></tr></table>';
	$('#search-filters,#add-spam-filter').typeahead([
			{
				name: 'spam-filters',
				remote: url,
				template: temp,
				valueKey: 'text',
				limit: 10,
				engine: Hogan
			}
		])
		.on('typeahead:selected', function($e, datum) {
			$('#search-filters,#add-spam-filter').blur().val('');
			window.location.hash = 'filter=' + datum.type + '&text=' + datum.text;
			checkForPageChange();
		})
		.focusin(function() {
			$(this).stop().animate( {
				'width': ($(window).width() - $(this).offset().left - 50) + 'px'
			}, 200);
		})
		.focusout(function() {
			$(this).stop().animate( {
				'width': ($(window).width() - $('#search-filters').offset().left - 60) + 'px'
			}, 200);
		})
		.css('width', '150px');
}

function checkIsBotActive() {
	$.getJSON('api.cgi?method=get_last_update')
		.fail(function() { /* TODO */ })
		.done(function(json) {
			var stat = '', color = '';
			if (json.diff < 30) {
				stat = 'active';
				color = 'success';
			} else if (json.diff < 120) {
				stat = 'at risk (' + json.hr_time + ')';
				color = 'warning';
			} else {
				stat = 'inactive (' + json.hr_time + ')';
				color = 'danger';
			}
			$('#status-button')
				.removeClass()
				.addClass('label label-' + color)
				.html(stat);
		});
}


/**
 * Display new "page". Hides current pages, scrolls up, shows new page
 */
function showPage(id) {
	// Hide existing pages
	$('body .container[id^="container-"]:visible').stop().fadeOut(200);
	// Deselect nav-bar
	$('a[id^="nav-"]').parent().removeClass('active');
	// Hide drop-down navbar on xs
	if ( $('.navbar-collapse').hasClass('in') ) {
		$('.navbar-toggle').click();
	}
	// Scroll up
	$('html,body').stop().animate({ 'scrollTop': 0 }, 500);
	// Show the page
	$('#' + id).stop().hide().fadeIn(500);
}
