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

	createTable('modded', 'modded subs', 'tower', 'col-xs-12');
	getModeratedSubreddits();

	setAutoScrolls();
	setAutocomplete();
	checkIsBotActive();
	setInterval(checkIsBotActive, 10 * 1000);

	// Set click-handlers for nav bar buttons
	$('a#add-spam-filter'  ).click(function() { window.location.hash = 'add';           checkForPageChange(); });
	$('a#view-filter-link' ).click(function() { window.location.hash = '#filter=link' ; checkForPageChange(); });
	$('a#view-filter-text' ).click(function() { window.location.hash = '#filter=text' ; checkForPageChange(); });
	$('a#view-filter-user' ).click(function() { window.location.hash = '#filter=user' ; checkForPageChange(); });
	$('a#view-filter-tld'  ).click(function() { window.location.hash = '#filter=tld'  ; checkForPageChange(); });
	$('a#view-filter-thumb').click(function() { window.location.hash = '#filter=thumb'; checkForPageChange(); });
	$('a#view-filter-all'  ).click(function() { window.location.hash = '#filter=all'  ; checkForPageChange(); });
	$('a#view-about-site'  ).click(function() { window.location.hash = '#about=site'  ; checkForPageChange(); });
	$('a#view-about-mods'  ).click(function() { window.location.hash = '#about=mods'  ; checkForPageChange(); });
	$('a#view-about-code'  ).click(function() { window.location.hash = '#about=code'  ; checkForPageChange(); });

	checkForPageChange();
});

function checkForPageChange() {
	var keys = getQueryHashKeys();
	if ('stats' in keys) {
		$('html,body')
			.stop()
			.animate({
				'scrollTop': $('#stats-anchor').offset().top - $('.navbar').height(),
			}, 500);
	}
	else if ('scores' in keys) {
		$('html,body')
			.stop()
			.animate({
				'scrollTop': $('#scores-anchor').offset().top - $('.navbar').height(),
			}, 500);
	}
	else if ('spam' in keys) {
		$('html,body')
			.stop()
			.animate({
				'scrollTop': $('#spam').offset().top - $('.navbar').height(),
			}, 500);
	}
	else if ('mod' in keys) {
		if ( !$('#container').is(':visible') ) {
			// Main page is not visible, make it visible
			$('#alt-container').stop().hide(200);
			$('#container').stop().fadeIn(200);
		}
		$('html,body')
			.stop()
			.animate({
				'scrollTop': $('#modded').offset().top - $('.navbar').height(),
			}, 500);
	}
	else if ('about' in keys) {
		if (keys['about'] === 'site') {
			// Info about the site
			createAboutSitePage();
		}
		else if (keys['about'] === 'mods') {
			// Info for mods
			createAboutModsPage();
		}
		else if (keys['about'] === 'code') {
			// Info about source code
			createAboutCodePage();
		}
	}
	else if ('add' in keys) {
		createAddSpamFilterPage();
	}
	else if ('filter' in keys) {
		// Mark toolbars as inactive
		$('a[id^="nav-"]').parent().removeClass('active');
		// Hide main page
		$('#container').stop().fadeOut(200);
		// Show minipage
		// Scroll up
		$('html,body')
			.stop()
			.animate({
				'scrollTop': 0,
			}, 500);
		if ('text' in keys) {
			$('div#alt-container')
				.empty()
				.append(
					$('<div class="jumbotron"/>')
						.append( $('<h1/>').attr('id', 'title').html('reddit spam bot') )
						.append( $('<p/>').attr('id', 'description').html('info and statistics for the anti-spam bot <a href="http://reddit.com/u/rarchives">/u/rarchives</a>') )
				);
			$('#alt-container').stop().hide().fadeIn(500);
			// Get filter info for specific filter, populate main header
			getFilterInfo(keys['filter'], keys['text']);
			// Get removals for filter, insert below header
			createTable('alt-spam', 'spam removed by filter', 'remove', 'col-xs-12', '#alt-container');
			getSpam('alt-spam', 0, 10, keys['filter'], keys['text'])
		} else if (keys['filter'] == 'all') {
			// Display all filters (user/text/link/tld/thumb)
			$('div#alt-container')
				.empty()
				.append(
					$('<div class="jumbotron"/>')
						.append( $('<h1/>').attr('id', 'title').html('all spam filters') )
						.append( $('<p/>').attr('id', 'description').html('below are all spam filters used by the bot to detect and remove spam') )
				);
			$('#alt-container').stop().hide().fadeIn(500);
			createTable('alt-filter-link',  'link filters',  'link',    'col-xs-12 col-lg-6', '#alt-container');
			createTable('alt-filter-text',  'text filters',  'pencil',  'col-xs-12 col-lg-6', '#alt-container');
			createTable('alt-filter-user',  'user filters',  'user',    'col-xs-12 col-lg-6', '#alt-container');
			createTable('alt-filter-tld',   'tld filters',   'globe',   'col-xs-12 col-lg-6', '#alt-container');
			createTable('alt-filter-thumb', 'thumb filters', 'picture', 'col-xs-12 col-lg-6', '#alt-container');
			getFilters('alt-filter-link',  'link');
			getFilters('alt-filter-text',  'text');
			getFilters('alt-filter-user',  'user');
			getFilters('alt-filter-tld',   'tld');
			getFilters('alt-filter-thumb', 'thumb');
		} else {
			// Display just one type of filter (user/text/link/tld/thumb)
			$('div#alt-container')
				.empty()
				.append(
					$('<div class="jumbotron"/>')
						.append( $('<h1/>').attr('id', 'title').html(keys['filter'] + ' spam filters') )
						.append( $('<p/>').attr('id', 'description').html('below are all "' + keys['filter'] + '" filters used to detect and remove spam') )
				);
			$('#alt-container').stop().hide().fadeIn(500);
			createTable('alt-filter-' + keys['filter'], keys['filter'] + ' filters', 'filter', 'col-xs-12', '#alt-container');
			getFilters('alt-filter-' + keys['filter'],  keys['filter']);
		}
	}
	else if (window.location.hash !== '' && window.location.hash !== '#') {
	// Unexpected hash tag. Set the default
		window.location.hash = '';
		checkForPageChange();
	}
}

function addFilterTable(type) {
	
}

function getFilterInfo(type, text) {
	$('h1#title')
		.empty()
		.append( $('<small>' + type + ' filter for</small> <em>' + text + '</em>') )
	var url = 'api.cgi?method=get_filter_info&type=' + type + '&text=' + encodeURIComponent(text);
	$.getJSON(url)
		.fail(function() { /* TODO */ })
		.done(function(json) {
			$('p#description')
				.empty()
				.append( '<strong>' + json.count + '</strong> removal' + (json.count == 1 ? '' : 's') )
				.append( $('<p/>') )
				.append( 'created by <strong>' + getUser(json.user).html() + '</strong> on ' + (new Date(json.date * 1000)).toLocaleString() )
				.append( $('<p/>') )
				.append( 'filter is <strong>' + (json.active ? '<b class="text-success">active</b>' : '<b class="text-danger">inactive</b>') + '</strong>' )
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
		if (p.length != 2) {
			b[p[0]] = '';
			continue;
		}
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
		.append  ( $('<span id="' + name + '-title"/>').html(' ' + title) );
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
					.appendTo( $('#scoreboard') )
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
				.appendTo( $('#scoreboard') )
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
						getFilters(name, type, json.start - 20, json.count);
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
			console.log('failure!');
		})
		.done(function(json) {
			if (json.error !== undefined) {
				// TODO Error handler
				console.log('error: ', json.error);
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
				console.log('item', item);
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
		['#nav-spam',     '#spam'],
		['#nav-graphs',   '#stats-anchor']
	];
	$.each(navids, function(index, item) {
		$(item[0]).click(function(e) {
			//window.location.hash = '';
			if ( !$('#container').is(':visible') ) {
				// Main page is not visible, make it visible
				$('#alt-container').stop().hide(200);
				$('#container').stop().fadeIn(200);
			}
			$('a[id^="nav-"]').parent().removeClass('active');
			$(this).parent().addClass('active').blur();
			$(this).blur();
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
			return true;
		});
	});
}

function setAutocomplete() {
	var url = 'api.cgi?method=search_filters&q=%QUERY&limit=10';
	var temp = '<table><tr><td>';
	temp += '<span class="glyphicon glyphicon-{{icon}}" title="{{type}} filter"></span>';
	temp += '</td><td style="padding-left: 10px">';
	temp += '<a href="#filter={{type}}&text={{text}}">{{text}}</a>';
	temp += '</td></tr></table>';
	$('#search-filters').typeahead([
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

function createAddSpamFilterPage() {
	$('a[id^="nav-"]').parent().removeClass('active');
	// Hide main page
	$('#container').stop().fadeOut(200);
	// Show minipage
	// Scroll up
	$('html,body')
		.stop()
		.animate({
			'scrollTop': 0,
		}, 500);
	$('#alt-container div').filter(function() { return !$(this).hasClass('jumbotron') }).remove();
	$('#alt-container').stop().hide().fadeIn(500);
	$('h1#title')
		.empty()
		.append( 'add spam filter' );
	var $p = $('p#description')
		.empty()
		.append( $('<div class="text-danger text-right"/>').html('<strong>only admins can add filters</strong>') )
		.append( $('<div class="text-warning text-right"/>').html('if you are not an admin, you can submit<p>a filter to <a href="http://reddit.com/r/reportthespammersNSFW" target="_BLANK_NSFW">/r/ReportTheSpammersNSFW</a>') );
	var $g = $('<div/>')
		.addClass('input-group')
		.appendTo($p);

	var $input = $('<input/>')
		.attr('id', 'add-spam-filter')
		.attr('type', 'text')
		.attr('placeholder', 'type or paste filter here')
		.addClass('form-control')
		.appendTo($g);
	$input.typeahead({
				name: 'spam-filters',
				remote: 'api.cgi?method=search_filters&q=%QUERY&limit=10',
				template: '<table><tr><td><span class="glyphicon glyphicon-{{icon}}" title="{{type}} filter"></span></td><td style="padding-left: 10px"><a href="#filter={{type}}&text={{text}}">{{text}}</a></td></tr></table>',
				valueKey: 'text',
				limit: 10,
				engine: Hogan,
				width: '100%'
		})
		.addClass('typeahead-lg')
		.on('typeahead:selected', function($e, datum) {
			window.location.hash = 'filter=' + datum.type + '&text=' + datum.text;
			checkForPageChange();
		});

	var $gb = $('<div/>')
		.addClass('input-group-btn')
		.appendTo($g);
	var $btn = $('<button/>')
		.attr('type', 'button')
		.addClass('btn btn-default dropdown-toggle')
		.attr('data-toggle', 'dropdown')
		.html('add as...')
		.appendTo($gb);
	$('<span/>')
		.addClass('caret')
		.appendTo($btn);
	var $ul = $('<ul/>')
		.addClass('dropdown-menu pull-right')
		.appendTo($gb);
	$('<a/>')
		.addClass('pull-right')
		.attr('id', 'filter-add-link')
		.html('link filter <span class="glyphicon glyphicon-link"></span>')
		.click(function() {
			sendPM('add link: ' + $('input#add-spam-filter').val());
			$('input#add-spam-filter').val('');
		})
		.appendTo( $('<li/>').appendTo($ul) );
	$('<a/>')
		.addClass('pull-right')
		.attr('id', 'filter-add-text')
		.html('text filter <span class="glyphicon glyphicon-pencil"></span>')
		.click(function() {
			sendPM('add text: ' + $('input#add-spam-filter').val());
			$('input#add-spam-filter').val('');
		})
		.appendTo( $('<li/>').appendTo($ul) );
	$('<a/>')
		.addClass('pull-right')
		.attr('id', 'filter-add-user')
		.html('user filter <span class="glyphicon glyphicon-user"></span>')
		.click(function() {
			sendPM('add user: ' + $('input#add-spam-filter').val());
			$('input#add-spam-filter').val('');
		})
		.appendTo( $('<li/>').appendTo($ul) );
	$('<a/>')
		.addClass('pull-right')
		.attr('id', 'filter-add-tld')
		.html('tld filter <span class="glyphicon glyphicon-globe"></span>')
		.click(function() {
			sendPM('add tld: ' + $('input#add-spam-filter').val());
			$('input#add-spam-filter').val('');
		})
		.appendTo( $('<li/>').appendTo($ul) );
	$('<a/>')
		.addClass('pull-right')
		.attr('id', 'filter-add-thumb')
		.html('thumb filter <span class="glyphicon glyphicon-picture"></span>')
		.click(function() {
			sendPM('add thumb: ' + $('input#add-spam-filter').val());
			$('input#add-spam-filter').val('');
		})
		.appendTo( $('<li/>').appendTo($ul) );
	$('#alt-container')
		.append( $('<div class="col-xs-12">')
				.append($('<h1/>').html('link filter'))
				.append($('<p/>').html('link filters apply to any text within a link.') )
				.append($('<p/>').html('only searches through links that contain <code>http://</code>') )
				.append($('<p/>').html('example:') ) 
				.append($('<p/>').addClass('lead').html('link filter <code>site.com</code> will detect and remove links to <code>http://site.com/page.jpg</code>, <code>http://website.com</code>, etc.') )
		);
	$('#alt-container')
		.append( 
			$('<div class="col-xs-12">')
				.append($('<h1/>').html('text filter'))
				.append(
					$('<p/>').html('searches')
						.append( $('<ul/>')
							.append( $('<li/>').html('post titles') )
							.append( $('<li/>').html('post urls') )
							.append( $('<li/>').html('post selftext') )
							.append( $('<li/>').html('comment text') )
						)
					)
				.append($('<p/>').html('example:') ) 
				.append($('<p/>').addClass('lead').html('text filter <code>click here</code> will detect and remove comments that contain <code>click here to see the video!</code>, or <code>if you want a click here\'s your chance</code>, etc; regardless of if the <code>click here</code> is within a link or not.') )
			);
						
	$('#alt-container')
		.append( $('<div class="col-xs-12">')
				.append($('<h1/>').html('user filter'))
				.append($('<p/>').html('matches to a full username, not case sensitive.') )
				.append($('<p/>').html('example:') ) 
				.append($('<p/>').addClass('lead').html('<code>ViolentAcrez</code> would detect and remove posts/comments from <code>/u/violentacrez</code> but not <code>/u/violentacrez2</code>') )
		);
	$('#alt-container')
		.append( $('<div class="col-xs-12">')
				.append($('<h1/>').html('tld filter'))
				.append($('<p/>').html('TLD (top-level domain) filters match a link\'s TLD.') )
				.append($('<p/>').html('example:') ) 
				.append($('<p/>').addClass('lead').html('the site <code>www.site.ru/index.php</code> has the TLD <code>ru</code>') )
		);
	$('#alt-container')
		.append( $('<div class="col-xs-12">')
				.append($('<h1/>').html('thumb filter'))
				.append($('<p/>').html('targets a specific type of spam: "thumb spam", aka imgur albums that contain links to spam sites. the bot will look inside of each imgur album and detect spammy links within.<p>called <code>thumb spam</code> because initially many spammers had albums with a tiny image and a link that said "click here for a larger image".') )
				.append($('<p/>').html('example:') ) 
				.append($('<p/>').addClass('lead').html('an imgur album that contains the text <code>click here!</code> would be removed because (so far) only spammers include this text in their albums') )
		);
}

function createAboutSitePage() {
	$('a[id^="nav-"]').parent().removeClass('active');
	// Hide main page
	$('#container').stop().fadeOut(200);
	// Show minipage
	// Scroll up
	$('html,body')
		.stop()
		.animate({
			'scrollTop': 0,
		}, 500);
	$('#alt-container div').filter(function() { return !$(this).hasClass('jumbotron') }).remove();
	$('#alt-container').stop().hide().fadeIn(500);
	$('h1#title')
		.empty()
		.append( 'about this site' );
	var desc = 'this site shows what the automated robot /u/rarchives is doing on reddit';
	desc += '<p><small>the bot is designed to remove spam and provide links to more images in NSFW subreddits.</small>';
	var $p = $('p#description')
		.empty()
		.html(desc)
	$('#alt-container')
		.append( $('<div class="col-xs-12 col-md-6">')
				.append($('<h1/>').html('how does it work?'))
				.append($('<p class="lead"/>').html('the bot is a moderator on <a href="#mod" onclick="window.location.hash = \'mod\'; checkForPageChange();">numerous subreddits</a>') )
				.append($('<p class="lead"/>').html('the bot looks at the posts and comments in these subreddits and removes any posts that are considered "spam"') )
		);
	$('#alt-container')
		.append( $('<div class="col-xs-12 col-md-6">')
				.append($('<h1/>').html('what is "spam"?'))
				.append($('<p class="lead"/>').html('spam is defined by filters which are added by a select-few users') )
				.append($('<p class="lead"/>').html('these filters can be added at any time and are immediately applied to all subreddits in which the bot moderates') )
		);
	$('#alt-container')
		.append( $('<div class="col-xs-12 col-md-6">')
				.append($('<h1/>').html('is this like AutoModerator?'))
				.append($('<p class="lead"/>').html('the bot is not affiliated with /u/AutoModerator') )
				.append($('<p class="lead"/>').html('AutoModerator is great for what it does, but spam moves fast. keeping up with spam across hundreds of subreddits via a wiki config is painful, so this bot was created to alleviate the pain') )
		);
	$('#alt-container')
		.append( $('<div class="col-xs-12 col-md-6">')
				.append($('<h1/>').html('how can I add a filter?'))
				.append($('<p class="lead"/>').html('submit a post to <a href="http://reddit.com/r/reportthespammersNSFW" target="_BLANK_NSFW">/r/ReportTheSpammersNSFW</a>') )
		);
	$('#alt-container')
		.append( $('<div class="col-xs-12 col-md-6">')
				.append($('<h1/>').html('why the website?'))
				.append($('<p class="lead"/>').html('the bot takes many actions. the site helps visualize everything that is happening behind the scenes') )
		);
	$('#alt-container')
		.append( $('<div class="col-xs-12">')
				.append($('<h1/>').html('questions? comments?'))
				.append($('<p class="lead"/>').html('you can reach the site administators on reddit by sending a message to <a href="http://www.reddit.com/message/compose?to=%2Fr%2FreportthespammersNSFW">/r/ReportTheSpammersNSFW</a>') )
		);
}

function createAboutModsPage() {
	$('a[id^="nav-"]').parent().removeClass('active');
	// Hide main page
	$('#container').stop().fadeOut(200);
	// Show minipage
	// Scroll up
	$('html,body')
		.stop()
		.animate({
			'scrollTop': 0,
		}, 500);
	$('#alt-container div').filter(function() { return !$(this).hasClass('jumbotron') }).remove();
	$('#alt-container').stop().hide().fadeIn(500);
	$('h1#title')
		.empty()
		.append( 'information for moderators' );
	var desc = 'you can employ this bot in your own subreddit by adding reddit user <code>rarchives</code> as a moderator of your subreddit';
	desc += '<p><small>the bot requires <em>at least</em> <code>post</code> permissions. other features require more privileges</small>';
	var $p = $('p#description')
		.empty()
		.html(desc)
	$('#alt-container')
		.append( $('<div class="col-xs-12">')
				.append($('<h1/>').html('features'))
				.append(
					$('<p class="lead"/>').append(
						$('<ul/>')
							.append( $('<li/>').html('removes spam using a dynamically-updated filter. catches new spam as it\'s rising') )
							.append( $('<li/>').html('removes reposts from /r/gonewild') )
							.append( $('<li/>').html('removes "illicit" content known to violate reddit\'s rules on underage or illicit content') )
					)
				)
		);
}

function createAboutCodePage() {
	$('a[id^="nav-"]').parent().removeClass('active');
	$('#container').stop().fadeOut(200);
	$('html,body')
		.stop()
		.animate({
			'scrollTop': 0,
		}, 500);
	$('#alt-container div').filter(function() { return !$(this).hasClass('jumbotron') }).remove();
	$('#alt-container').stop().hide().fadeIn(500);
	$('h1#title')
		.empty()
		.append( 'source code' );
	var desc = 'the bot\'s source code and this website are available <strong><a href="https://github.com/4pr0n/spambot" target="_BLANK_GITHUB">on github</a></strong>';
	var $p = $('p#description')
		.empty()
		.html(desc)
	$('#alt-container')
		.append( $('<div class="col-xs-12">')
				.append($('<h1/>').html('languages'))
				.append(
					$('<p class="lead"/>').append(
						$('<ul/>')
							.append( $('<li/>').html('bot is written in <a href="http://python.org/">Python</a> (2.7.x flavor)') )
							.append( $('<li/>').html('website is built on <a href="http://getbootstrap.com/">Bootstrap</a> (3.0), <a href="http://jquery.com/">JQuery</a> (2.x), and <a href="http://www.highcharts.com/">Highcharts</a>') )
					)
				)
		);
}
