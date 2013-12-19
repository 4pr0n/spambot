$(document).ready(function() {
	// Enable side-bar toggling
  $('[data-toggle=offcanvas]').click(function() {
    $('.row-offcanvas').toggleClass('active');
  });
	getScoreboard();
	getRemovedSpam();
	getFilterChanges();
});

function getScoreboard() {
	$.getJSON('api.cgi?method=get_scoreboard')
		.fail(function() {
			// TODO handle failure
		})
		.done(function(json) {
			if (json.error !== undefined) {
				// TODO Error handler
				return;
			}
			$('<tr/>')
				.appendTo( $('#scoreboard') )
				.append( $('<th>#</th>') )
				.append( $('<th>admin</th>') )
				.append( $('<th>score</th>') )
				.append( $('<th>filters</th>') );
			// Build scoreboard
			$.each(json.scoreboard, function(index, item) {
				$('<tr/>')
					.click(function() {
						// TODO Direct to user page
					})
					.appendTo( $('#scoreboard') )
					.append( $('<td/>').html(index + 1 ) )
					.append( $('<td/>').html(item.user ) )
					.append( $('<td/>').html(item.score) )
					.append( $('<td/>').html(item.filters) );
			});
		});
}

function getRemovedSpam(start, count) {
	if (start === undefined) start =  0;
	if (count === undefined) count = 10;
	$.getJSON('api.cgi?method=get_removed&start=' + start + '&count=' + count)
		.fail(function() {
			// TODO handle failure
		})
		.done(function(json) {
			if (json.error !== undefined) {
				// TODO Error handler
				return;
			}
			$('#removed-spam').empty();
			$('<tr/>')
				.appendTo( $('#removed-spam') )
				.append( $('<th>date</th>') )
				.append( $('<th>reddit</th>') )
				.append( $('<th>type</th>') )
				.append( $('<th>filter text</th>') )
				//.append( $('<th>spam?</th>') )
				.append( $('<th>credit</th>') );
			// Build scoreboard
			$.each(json.removed, function(index, item) {
				$('<tr/>')
					.click(function() {
						// TODO Error handling
					})
					.appendTo( $('#removed-spam') )
					.append( $('<td/>').html(new Date(item.date * 1000).toLocaleString() ) )
					.append( $('<td/>').html( $('<a/>').attr('href', item.permalink).html(item.posttype) ) )
					.append( $('<td/>').html(item.spamtype) )
					.append( $('<td/>').html(item.spamtext) )
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

function getFilterChanges(start, count) {
	if (start === undefined) start =  0;
	if (count === undefined) count = 10;
	$.getJSON('api.cgi?method=get_filter&start=' + start + '&count=' + count)
		.fail(function() {
			// TODO handle failure
		})
		.done(function(json) {
			if (json.error !== undefined) {
				// TODO Error handler
				return;
			}
			$('#filter-changes').empty();
			$('<tr/>')
				.appendTo( $('#filter-changes') )
				.append( $('<th>date</th>') )
				.append( $('<th>user</th>') )
				.append( $('<th>action</th>') )
				.append( $('<th>type</th>') )
				.append( $('<th>filter text</th>') );
			$.each(json.filter_changes, function(index, item) {
				$('<tr/>')
					.click(function() {
						// TODO Error handling
					})
					.appendTo( $('#filter-changes') )
					.append( $('<td/>').html(new Date(item.date * 1000).toLocaleString() ) )
					.append( $('<td/>').html(item.user    ) )
					.append( $('<td/>').html(item.action  ) )
					.append( $('<td/>').html(item.spamtype) )
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
				method   : 'delete_filter',
				spamtype : type,
				spamtext : text
			};
			$.getJSON('api.cgi?' + $.param(params))
				.fail(function() {
					// TODO error handler
				})
				.done(function(json) {
					// TODO display filter is removed
				});
		});
}
