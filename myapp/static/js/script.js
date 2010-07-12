
var re = /[^a-zA-Z0-9_\-]/;

var loggedin = false;
if ($.cookie('session')) {
    loggedin = true;
} 

$(document).ready(function() {
    
    $('#gsearch_term').focus();
    $('#gsearch_reddits').click(
        function() {
            var reddits = $(this).val();
            if (reddits.length !== 0) {
                if (reddits.charAt(reddits.length - 1) !== '+') {
                    $(this).val(reddits + '+');
                }
            }
        }
    );

    var lastreddit;
    var lasttag;
    var loading = '<div class="loading">loading...</div>';
    
    $('a.subreddit').live('click', function() {
        if ($('#info').length) {
            $('#info').remove();
            if ($(this).parents('#taginfo').length > 0) {
                $('a.subreddit').css('color', 'black !important');
            }
            $('a.subreddit').removeClass('selected');
            if (this == lastreddit) {
                return false;
            }
        }
        if ($(this).parents('#taginfo').length > 0) {
            $('a.subreddit').css('color', '#ccc !important');
            $(this).css('color', 'orangered !important');
        }
        var link = $(this).attr('href');
        var url =  '/api' + link;
        $(this).addClass('selected').after('<div id="info">' + loading + '</div>');
        $('#info').load(url);
        lastreddit = this
        $.scrollTo(this, 800, {axis:'y', offset:{top:-100}});
        return false;
    });
    

    $('a.tag').live('click', function() {
        if ($('#taginfo').length != 0) {
            $('#taginfo').remove();
            $('a.tag').removeClass('selected');
            if (this == lasttag) {
                return false;
            }
        }
        var link = $(this).attr('href'); 
        var url =  '/api' + link;
        $(this).addClass('selected').after('<div id="taginfo">' + loading + '</div>');
        $('#taginfo').load(url);
        lasttag = this;
        $.scrollTo(this, 800, {axis:'y', offset:{top:-100}});
        return false;
    });

 
    $('span[id ^= subs_]').live('click', function() {
        var txt = $(this).html();
        var url = $(this).attr('id').split('_').slice(1).join('_');
        var submissions = $('#submissions_' + url);
        if (submissions.html().length != 0) {
            if (submissions.css('display') == 'none') {
                submissions.css('display', 'block');
                $(this).html(txt.substr(0, txt.length-4) + ' [-]');
                return false;
            }
            $(this).html(txt.substr(0, txt.length-4) + ' [+]');
            submissions.css('display', 'none');
            return false; 
        }
        $(this).html(txt.substr(0, txt.length-4) + ' [-]');
        submissions
            .html(loading)
            .css('display', 'block')
            .load('/api/cachedproxy/' + url, 
                function(data) {
                    $(this).html(data);
                }
            );
    });


    $('#add_tag_name').live('click', function() { 
        $(this).autocomplete('/api/autocomplete/tags');
    });
    

    $('.auto').autocomplete('/api/autocomplete/reddits', {
        minChars: 2,
        multiple: true,
        multipleSeparator: '+',
        scroll: false
    });


    $('#add_tag_submit').live('click', function() {
        var name = $('#add_tag_name').val();
        if (name == '') {
            return false;   
        }
        else if (name.length > 20) {
            var error = '<div class="error">Max 20 characters.</div>';
        }
        else if (name.match(re) != null) {
            var error = '<div class="error">Only letters and numbers allowed.</div>';
        }
        if (error) {
            if ($('.error').length == 0) {
                $(this).after(error);
            } else {
                $('.error').replaceWith(error);
            }
            return false;
        }
        var id = $('#add_tag_id').val();
        if (!loggedin) {
            popup('tag_' + id + '_' + name);
            return false;
        }
        var token = $('#add_tag_token').val();
        var dataString = 'todo=tag_' + id + '_' + name + '&token=' + token;
        $.post(
            '/api/add_tag',
            dataString,
            function(data) {
                if ($('#tag_' + name).length != 0) {
                    $('#tag_' + name).replaceWith(data);
                    $('#add_tag_name').attr('value','');
                    return true;
                }
                $('#add_tag').prev().before(data);
                $('#add_tag_name').attr('value','');
                return true;
            },
            'html'
        );
        return false;
    });


    $('.arrow').live('click', function() {
        if (!loggedin) {
            popup($(this).attr('id'));
            return false;
        }
        var todo = $(this).attr('id');
        var token = $(this).parent('.vote').attr('id');
        var dataString = 'todo=' + todo + '&token=' + token;
        $.post(
            '/api/vote',
            dataString,
            function(data) {
                $('#' + todo).parents('.bigtag').replaceWith(data);
            },
            'html'
        );
        return false;

    });


    $('.bigtag').live('mouseover',
        function() {
            $(this).children('.score').removeClass('hidden');
        }
    );

    $('.bigtag').live('mouseout',
        function() {    
            $(this).children('.score').addClass('hidden');
        }
    );

    $('.loginbutton').click(function() {
        popup('');
        return false;
    });
 
    $('#form_stalk').submit(function() {
        $('#stalkstatus').html('This may take a few seconds.');
    });

    $('#form_monitor').submit(function() {
        var keyword = $('#monitor_keyword').val();
        if (keyword.length < 5) {
            $('#monitorstatus').html('Enter anything from 5 to 20 characters.'); 
            return false; 
        } 
        else if (keyword.length > 20) {
            $('#monitorstatus').html('Enter anything from 5 to 20 characters.'); 
            return false;
        }
    });

    function popup(reason) {
        $('#popup')
            .modal({
                overlayClose: true,
                opacity: 80
            });
        $('#popup')
            .find('[id^=reason_]')
            .attr('value', reason);
        return false;
    }


    $('.page').live('click', 
        function() {
            $.scrollTo('0%');
        }
    );
});


function send_post(form, type) {
    var show_status = $('#status_' + type);
    var user = $('#user_' + type).val(); 
    var pw = $('#passwd_' + type).val();
    if (user == '' || pw == '') {
        return false;
    } 
    if (type == 'reg') {    
        var pw2 = $('#passwd2_' + type).val();
        var error = '';
        if (pw != pw2) {
            error = 'Passwords don\'t match.';
        }
        if (user.match(re) != null) {
            error = 'Invalid username.';
        }
        $.get('/api/user', 'name='+user, function(data) {
            if (data.length != 0) {
                error = 'Username taken.';
            }
        });
        if (error.length != 0) {
            alert(error);
            show_status.html(error);
            return false;
        }
    }
    var rem = $('#rem_' + type + ':checked').val(); 
    var reason = $('#reason_' + type).val(); 
    var token = $('#token_' + type).val();
    var dataString = 'do=' + type + '&user=' + user + '&pw=' + pw + '&rem=' + rem + '&reason=' + reason + '&token=' + token;
    $.ajax({
        type: 'POST',
        url : '/api/login',
        data: dataString,
        success: function(data) {
            if (data.length == 0) {
                show_status.html('Login failed.');
                return false;
            }
            if (window.location == 'http://metareddit.memtropy.com/login') {
                window.location = 'http://metareddit.memtropy.com';
            }
            loggedin = true;
            $.modal.close();
            $('#header-bottom-right').html('<a href="/user/'+user+'">'+user+'</a> | <a href="/logout">log out</a>');
            if (reason.length != 0) {
                var r = reason.split('_')[0];
                if (r == 'vote') {
                    $('#' + reason).parents('.bigtag').replaceWith(data);
                }
                else if (r == 'tag') {
                    if ($('#tag_' + name).length != 0) {
                        $('#tag_' + name).replaceWith(data);
                    } else {
                        $('#add_tag').prev().before(data);
                    }
                    $('#add_tag_name').attr('value','');
                }
            }
            return false;
        },
        dataType: 'html'
    });
    return false;
}



function clear_input(e) {
    if(e.value == e.defaultValue) {
        e.value = '';
        e.style.color = '#000';
    }
}

function submit(e) {
    e.submit();   
}

function remove_monitoring(hash) {
    jQuery.get('/api/remove_monitoring/' + hash)
    $('#monitoring_' + hash).remove()
    return false;
}
