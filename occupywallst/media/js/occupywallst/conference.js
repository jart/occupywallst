
var conference_init;

(function() {
    "use strict";

    var confio;
    var confs;
    var admin;

    function init(args) {
        confs = args.confs;
        admin = args.admin;
        if (typeof(io) == "undefined")
            return;
        confio = io.connect(args.url);
        confio.on('connect', function() {
            for (var conf in confs) {
                confio.emit("monitor start", conf);
            }
        });
        confio.on('disconnect', function(e) {
            console.log("DISCONNECTED");
        });
        confio.on('error', function(reason) {
            console.log("error", reason);
        });
        confio.on("conference", function(conf) {
            for (var i in conf.members) {
                add_member(conf.members[i]);
            }
        });
        confio.on("member join", function(member) {
            add_member(member);
        });
        confio.on("member leave", function(member) {
            remove_member(member);
        });
        confio.on("member update", function(member) {
            update_member(member, member_row(member));
        });
    }

    function member_count(conf, delta) {
        var count = $(".count", confs[conf].elem);
        var mp3stream = $(".mp3stream", confs[conf].elem);
        var people = $(".people", confs[conf].elem);
        var x = parseInt(count.text());
        x += delta;
        count.text(x);
        if (x >= 2 && !mp3stream.is(":visible")) {
            mp3stream.fadeIn();
        } else if (x < 2 && mp3stream.is(":visible")) {
            mp3stream.fadeOut();
        }
        if (x == 1) {
            people.text("person");
        } else {
            people.text("people");
        }
    }

    function member_row(member) {
        return $(".id-" + member.id, confs[member.conf].elem);
    }

    function remove_member(member) {
        member_count(member.conf, -1);
        member_row(member).slideUp(300, function() {
            $(this).remove();
        });
    }

    function add_member(member) {
        member_count(member.conf, +1);
        function cmd() {
            confio.emit($(this).text(), member.conf, member.id);
            return false;
        }
        var row = $("<div/>").hide()
        .addClass("member")
        .addClass("id-" + member.id);
        if (admin) {
            var links = $("<span/>").addClass("links").append(
                $('<a href="#" class="mute">mute</a>').click(cmd),
                $('<a href="#" class="kick">kick</a>').click(cmd)
            );
            row.append(links);
        }
        row.append($("<span/>").addClass("cid").text(member.cid));
        update_member(member, row);
        confs[member.conf].elem.append(row);
        row.slideDown();
    }

    function update_member(member, row) {
        $(".info", row).remove();
        if (member.muted) {
            row.addClass("muted");
            row.append($("<span/>").addClass("info").text("(muted)"));
            $(".mute", row).text("unmute");
        } else {
            row.removeClass("muted");
            $(".mute", row).text("mute");
        }
        if (member.talking) {
            row.addClass("talking");
            row.append($("<span/>").addClass("info").text("(talking)"));
        } else {
            row.removeClass("talking");
        }
    }

    // export stuff
    conference_init = init;

})();
