
var chat_init;

(function() {
    "use strict";

    var me;
    var chat;
    var is_connected = false;

    function init(args) {
        $("#msgtext").focus();
        $("#postform").submit(on_postform);
        $("#privateroom").submit(function() {
            window.location.href = $(".room", this).val() + '/';
            return false;
        });
        connect(args.url, args.room);
    }

    function connect(url, room) {
        var pinger, ponged;
        if (typeof(io) == "undefined") {
            display({text: "error: chat server is down"});
            return;
        }
        chat = io.connect(url);
        chat.on('connect', function () {
            is_connected = true;
            chat.emit("join", {room: room});
            ponged = true;
            pinger = setInterval(function() {
                if (ponged) {
                    ponged = false;
                    chat.emit('ping');
                } else {
                    chat.socket.disconnect();
                }
            }, 5000);
        });
        chat.on('connecting', function () {
            display({text: "Connecting..."});
        });
        chat.on('error', function (reason) {
            display({text: "Error: " + reason});
        });
        chat.on('disconnect', function(reason) {
            chat = null;
            is_connected = false;
            clearInterval(pinger);
            $("#users > div").remove();
            display({text: "disconnected from server :'("});
        });
        chat.on("pong", function () {
            ponged = true;
        });
        chat.on("msg", display);
        chat.on("join_ack", function (msg) {
            me = msg.user;
            display({text: "Welcome " + me.name + "!"});
            display({text: "Joined: " + msg.room});
            for (var k in msg.users) {
                add_user(msg.users[k]);
            }
        });
        chat.on("leave", function (msg) {
            display({text: msg.user.name + " has left"});
            remove_user(msg.user);
        });
        chat.on("leave_ack", function (msg) {
            display({text: "you have left " + msg.room});
            $("#users").empty();
        });
        chat.on("kicked", function (msg) {
            display({text: "you were kicked from " + msg.room});
        });
        chat.on("join", function (msg) {
            add_user(msg.user);
            display({text: msg.user.name + " has joined"});
        });
    }

    function on_postform() {
        if (!me)
            return false;
        if (!is_connected) {
            display({text: "not connected"});
            return false;
        }
        var text = $("#msgtext").val();
        $("#msgtext").val("");
        if (text.length < 2)
            return false;
        if (text[0] == "/") {
            var command, args;
            if (text.indexOf(" ") != -1) {
                command = text.slice(1, text.indexOf(' '));
                args = text.slice(text.indexOf(' ') + 1);
            } else {
                command = text.slice(1);
                args = '';
            }
            if (command == "kick") {
                chat.emit("kick", {room: "pub", user: {name: args}});
            } else if (command == "me") {
                var msg = {
                    room: "pub",
                    user: me,
                    text: args,
                    emo: true
                };
                chat.emit("msg", msg);
            } else {
                display({text: "unknown command"});
            }
        } else {
            var msg = {
                room: "pub",
                user: me,
                text: text,
                emo: false
            };
            chat.emit("msg", msg);
        }
        return false;
    }

    function display(msg) {
        var line = $("<div/>");
        if (msg.user) {
            if (msg.emo) {
                line
                .append($("<span/>").text(curtime() + " * "))
                .append(fun_username(msg.user.name))
                .append($("<span/>").text(" " + msg.text));
            } else {
                line
                .append($("<span/>").text(curtime() + " "))
                .append($("<span/>").text("<"))
                .append(fun_username(msg.user.name))
                .append($("<span/>").text(">"))
                .append($("<span/>").text(" " + msg.text));
            }
        } else {
            line.text(curtime() + " -!- " + msg.text);
        }
        $("#messages").append(line);
        $("#messages").prop({scrollTop: $("#messages").prop("scrollHeight")});
    }

    function add_user(user) {
        $("#users").append($("<div/>").append(fun_username(user.name)));
    }

    function fun_username(name) {
        if (name.match(/^anon[0-9]+$/)) {
            return $("<span/>").text(name);
        } else {
            return $("<a/>").attr("href", "/users/" + name + '/').text(name);
        }
    }

    function remove_user(user) {
        $("#users > div").each(function () {
            if ($(this).text() == user.name) {
                $(this).remove();
            }
        });
    }

    function curtime() {
        var now = new Date();
        var hours = now.getHours();
        var minutes = now.getMinutes();
        if (hours < 10) hours = "0" + hours;
        if (minutes < 10) minutes = "0" + minutes;
        return "" + hours + ":" + minutes;
    }

    // export stuff
    chat_init = init;

})();
