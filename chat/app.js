/// occupywallst node.js realtime http stuff
///
/// This program does the following:
///
/// 1. Chat server
/// 2. Publish user notifications as soon as they're created
/// 3. Publish realtime information about what FreeSWITCH is doing
///

var fs = require("fs");
var net = require("net");
var dgram = require("dgram");
var express = require('express');
var memcached = require('memcached');
var cache = new memcached("127.0.0.1:11211");
var pg = require('pg').native;
var freeswitch = require('./freeswitch');
var throttler = require('./throttler');

var settings = (function(){
    var f = fs.readFileSync("settings.json");
    var set = eval('(' + f.toString() + ')');
    try {
        f = fs.readFileSync("settings_local.json");
    } catch (e) {
        return set;
    }
    var locset = eval('(' + f.toString() + ')');
    for (var key in locset) {
        set[key] = locset[key];
    }
    return set;
})();

var app;
if (settings.http.ssl_enable) {
    app = express.createServer({
        key: fs.readFileSync(settings.http.ssl_key),
        cert: fs.readFileSync(settings.http.ssl_cert)
    });
} else {
    app = express.createServer();
}

var io = require('socket.io').listen(app);

app.configure(function() {
    app.set('views', __dirname + '/views');
    app.set('view engine', 'jade');
    // app.use(express.logger());
    app.use(express.bodyParser());
    app.use(express.methodOverride());
    app.use(express.cookieParser());
    app.use(app.router);
    app.use(express.static(__dirname + '/public'));
});
app.configure('development', function() {
    app.use(express.errorHandler({dumpExceptions: true, showStack: true}));
});
app.configure('production', function() {
    app.use(express.errorHandler()); 
});

io.configure(function() {
    io.set('close timeout', 99999999999);
    io.set('transports', ['websocket', 'flashsocket', 'xhr-polling']);
});
io.configure('development', function() {
    console.log("SOCKET.IO DEVELOPMENT MODE");
    io.set('log level', 3);
});
io.configure('production', function() {
    console.log("SOCKET.IO PRODUCTION MODE");
    io.set('log level', 1);
    io.enable('browser client etag');
    io.enable('browser client minification');
});

//////////////////////////////////////////////////////////////////////
// web application

app.get('/', function(req, res) {
    res.render('index', {});
});

app.listen(settings.http.port, settings.http.host);
console.log("webserver listening on %s:%d",
            settings.http.host, settings.http.port);

//////////////////////////////////////////////////////////////////////
// chatroom code

var all_users = {};
var all_rooms = {};
var user_internal = {};
var guest_counter = 1;
var throttle = throttler.throttler(settings.throttler);

function authorization(handshake, callback) {
    handshake.user = {};
    var sessionid = null;
    var cookies = handshake.headers.cookie;
    if (cookies) {
        var res = cookies.match(/sessionid=([0-9a-f]+)/);
        if (res)
            sessionid = res[1];
    }
    get_session(sessionid, function(err, session) {
        if (err) { callback(null, true); return; }
        get_user(session._auth_user_id, function(err, user) {
            if (err) { callback(null, true); return; }
            handshake.user.name = user.username;
            handshake.user.is_staff = user.is_staff;
            callback(null, true);
        });
    });
}

var chatio = io.of('/chat');
chatio.authorization(authorization);
chatio.on('connection', function(sock) {
    var ip = sock.handshake.address.address;
    var me = sock.handshake.user;
    var my_rooms = {};
    var is_dead = false;

    // assign anonymous nicknames if not authenticated
    if (!me.name) {
        me.is_staff = false;
        me.name = "anon" + guest_counter++;
    }

    // drop old user if they join chat in a new browser window
    if (user_internal[me.name])
        user_internal[me.name].sock.disconnect();

    log("connected");

    function log(msg) {
        console.error("%s(%s): %s", me.name, ip, msg);
    }

    function safe(funk) {
        return function failsafe() {
            try {
                return funk.apply(null, arguments);
            } catch (err) {
                console.error("%s", err);
                console.trace();
                sock.disconnect();
            }
        };
    }

    function undead(funk) {
        return function _undead() {
            if (!is_dead)
                return funk.apply(null, arguments);
        };
    }

    function on_disconnect() {
        is_dead = true;
        log("disconnected");
        for (var room in my_rooms) {
            sock.broadcast.to(room).emit('leave', {
                room: room,
                user: me
            });
            delete all_rooms[room].users[me.name];
        }
        my_rooms = {};
        delete all_users[me.name];
        delete user_internal[me.name];
    }

    function on_ping() {
        sock.emit('pong');
    }

    function on_join(msg) {
        if (typeof(msg) != "object" ||
            typeof(msg.room) != "string" ||
            !msg.room.match(/^[a-z][a-z0-9]{2,19}$/)) {
            log("bad join message: " + JSON.stringify(msg));
            sock.disconnect();
            return;
        }
        if (my_rooms[msg.room])
            return; // already member
        if (!all_rooms[msg.room]) {
            all_rooms[msg.room] = {
                name: msg.room,
                users: {}
            };
        }
        all_rooms[msg.room].users[me.name] = me;
        my_rooms[msg.room] = all_rooms[msg.room];
        sock.join(msg.room);
        sock.emit('join_ack', {
            room: msg.room,
            user: me,
            users: all_rooms[msg.room].users
        });
        sock.broadcast.to(msg.room).emit('join', {
            room: msg.room,
            user: me
        });
    }

    function on_msg(msg) {
        if (typeof(msg) != "object" ||
            typeof(msg.room) != "string" ||
            typeof(msg.text) != "string" ||
            msg.text.length < 1 ||
            msg.text.length > 200) {
            log("bad msg message: " + JSON.stringify(msg));
            sock.disconnect();
            return;
        }
        if (!my_rooms[msg.room])
            return; // not a member
        chatio.in(msg.room).emit('msg', {
            room: msg.room,
            user: me,
            text: msg.text,
            emo: msg.emo
        });
    }

    function on_kick(msg) {
        if (typeof(msg) != "object" ||
            typeof(msg.room) != "string" ||
            typeof(msg.user) != "object" ||
            typeof(msg.user.name) != "string") {
            log("bad kick message: " + JSON.stringify(msg));
            sock.disconnect();
            return;
        }
        if (!me.is_staff) {
            log("tried to kick w/o ops: " + JSON.stringify(msg));
            return;
        }
        var ui = user_internal[msg.user.name];
        if (ui)
            ui.kick(msg);
    }

    function on_leave(msg) {
        if (typeof(msg) != "object" ||
            typeof(msg.room) != "string") {
            log("bad leave message: " + JSON.stringify(msg));
            sock.disconnect();
            return;
        }
        if (!my_rooms[msg.room])
            return; // not a member
        sock.broadcast.to(msg.room).emit('leave', {
            room: msg.room,
            user: me
        });
        sock.emit('leave_ack', {
            room: msg.room,
            user: me
        });
        sock.leave(msg.room);
        delete my_rooms[msg.room];
        delete all_rooms[msg.room].users[me.name];
    }

    function kick(msg) {
        if (msg.user.name == me.name && my_rooms[msg.room]) {
            sock.emit('kicked', msg);
            on_leave(msg);
        }
    };

    sock.on('ping', safe(on_ping));
    sock.on('join', safe(throttle(ip, safe(undead(on_join)))));
    sock.on('msg', safe(throttle(ip, safe(undead(on_msg)))));
    sock.on('kick', safe(on_kick));
    sock.on('leave', safe(on_leave));
    sock.on('disconnect', on_disconnect);

    all_users[me.name] = me;
    user_internal[me.name] = {sock: sock, kick: kick};
});

//////////////////////////////////////////////////////////////////////
// conference bridge: websocket interface

var confs = {};
var confio = io.of('/conf');
confio.authorization(authorization);
confio.on('connection', function(sock) {
    var me = sock.handshake.user;
    sock.on('monitor start', function(conf) {
        sock.emit("conference", confs[conf] || {name: conf, members: {}});
        sock.join(conf);
        console.log("JOINING %j", "conf " + conf);
    });
    sock.on('monitor stop', function(conf) {
        sock.leave(conf);
    });
    if (me.is_staff) {
        sock.on('mute', function(conf, id) {
            if (!confs[conf] || !confs[conf].members[id])
                return;
            fs_api("conference " + conf + " mute " + id);
        });
        sock.on('unmute', function(conf, id) {
            if (!confs[conf] || !confs[conf].members[id])
                return;
            fs_api("conference " + conf + " unmute " + id);
        });
        sock.on('kick', function(conf, id) {
            if (!confs[conf] || !confs[conf].members[id])
                return;
            fs_api("conference " + conf + " kick " + id);
        });
    }
});

//////////////////////////////////////////////////////////////////////
// conference bridge: freeswitch interface

var fsev = freeswitch.eventSocket(settings.freeswitch);
fsev.on('connect', function() {
    fsev.send("event json CUSTOM conference::maintenance");
}).on('event', function(type, event) {
    if (event["Event-Subclass"] != "conference::maintenance")
        return;

    var s = (event["Conference-Name"] + "@" +
             event["Conference-Profile-Name"] + ": " +
             event["Action"] + " " +
             event["Caller-Caller-ID-Number"]);
    if (fs_bool(event["Talking"])) {
        s += " (Talking " + event["Energy-Level"] + ")";
    }
    console.log(s);

    var name = event["Conference-Name"];
    var id = parseInt(event["Member-ID"]);
    switch (event["Action"]) {
    case "add-member":
        if (!confs[name])
            confs[name] = {name: name, members: {}};
        confs[name].members[id] = {
            id: id,
            conf: name,
            cid: mask(event["Caller-Caller-ID-Number"]),
            talking: fs_bool(event["Talking"]),
            muted: !fs_bool(event["Speak"]),
            energy: fs_bool(event["Energy-Level"]),
        };
        confio.in(name).emit("member join", confs[name].members[id]);
        console.log("BROADCASTING %j", "conf " + name);
        break;
    case "del-member":
        if (confs[name] && confs[name].members[id]) {
            confio.in(name).emit("member leave", confs[name].members[id]);
            delete confs[name].members[id];
            if (Object.keys(confs[name].members).length == 0)
                delete confs[name];
        }
        break;
    case "mute-member":
    case "unmute-member":
    case "start-talking":
    case "stop-talking":
        if (confs[name] && confs[name].members[id]) {
            var conf = confs[name].members[id];
            conf.muted = !fs_bool(event["Speak"]);
            conf.talking = fs_bool(event["Talking"]);
            conf.energy = fs_bool(event["Energy-Level"]);
            confio.in(name).emit("member update", conf);
        }
        break;
    }
});

//////////////////////////////////////////////////////////////////////
// notifications: websocket interface

var notifyio = io.of('/notifications');
notifyio.authorization(authorization);
notifyio.on('connection', function(sock) {
    sock.join("all");
    var me = sock.handshake.user;
    if (me.name) {
        sock.join("user." + me.name);
    }
});

//////////////////////////////////////////////////////////////////////
// notifications: subscriber receiving json messages from web app

function on_notification(data, rinfo) {
    // todo: secure me from local system users
    try {
        var msg = JSON.parse(data.toString('ascii'));
        if (typeof msg != "object" ||
            typeof msg.type != "string" || !msg.type.match(/^ows\.[.a-z]+$/) ||
            typeof msg.dest != "string" || !msg.dest.match(/^[._@+a-zA-Z0-9]+$/)) {
            console.error("bad notify msg: " + JSON.stringify(msg));
            return;
        }
        // console.log("send %s msg to %s: %j", msg.type, msg.dest, msg.msg);
        notifyio.in(msg.dest).emit(msg.type, msg.msg);
    } catch (e) {
        console.trace(e);
    }
}

var notify_sub = dgram.createSocket('udp4', on_notification);
notify_sub.bind(settings.notify_sub.port, settings.notify_sub.host);
console.log("notification subscriber listening on %s:%d",
            settings.notify_sub.host, settings.notify_sub.port);

//////////////////////////////////////////////////////////////////////
// flash media policy server

// var fps = net.createServer(function(sock) {
//     console.log("got request to flash policy server!");
//     sock.write('<?xml version="1.0"?>\n' +
//                '<!DOCTYPE cross-domain-policy SYSTEM "http://www.' +
//                'macromedia.com/xml/dtds/cross-domain-policy.dtd">\n' +
//                '<cross-domain-policy>\n' +
//                '  <allow-access-from domain="occupywallst.org"' +
//                '      to-ports="443" secure="true"/>' +
//                '</cross-domain-policy>');
//     sock.end();
// });

// fps.listen(843);
// console.log("flash policy server listening on %s:%d",
//             fps.address().address, fps.address().port);

//////////////////////////////////////////////////////////////////////
// Utilities

/// Return one row from database
function db_fetch(query, args, callback) {
    pg.connect(settings.db, function(err, db) {
        if (err) {
            console.error("failed to connect to postgresql: %s", err);
            callback("database is down D:", null);
            return;
        }
        db.query(query, args, function(err, result) {
            if (err) {
                console.error("query failed: %s", err);
                console.error("sql(%j, %j)", query, args);
                callback("query failed", null);
                return;
            }
            if (result.rows.length == 0) {
                callback("row not found", null);
                return;
            }
            callback(null, result.rows[0]);
        });
    });
}

/// Fetch Django session data from cache
function get_session(sessionid, callback) {
    if (!sessionid) {
        callback("sessionid not found", null);
        return;
    }
    cache.get(sessionid, function(err, result) {
        if (err) {
            callback("session not found", null);
            return;
        }
        var session;
        try {
            session = JSON.parse(result);
            if (typeof(session) != "object")
                throw "not an object";
        } catch (err) {
            console.error("corrupt session data: %s", err);
            console.error("session data: %j", result);
            callback("corrupt session data", null);
            return;
        }
        callback(null, session);
    });
}

/// Fetch Django auth user row from db
function get_user(userid, callback) {
    var query = ("SELECT *" +
                 "  FROM auth_user" +
                 " WHERE id = $1" + 
                 "   AND is_active = true");
    db_fetch(query, [userid], function(err, user) {
        if (err) { callback(err, null); return; }
        callback(null, user);
    });
}

// generates a random id for chat users
function gen_uid(bytes, callback) {
    fs.open(settings.random, 'r', function(err, fd) {
        if (err) {
            console.error(err);
            callback("no random device", null);
            return;
        }
        var buf = new Buffer(bytes);
        fs.read(fd, buf, 0, buf.length, 0, function(err, bytes, buf) {
            if (err) {
                console.error(err);
                callback("no random bytes", null);
                return;
            }
            fs.close(fd);
            callback(null, buf.toString('base64'));
        });
    });
}

/// formats and masks last four digits of caller ids
function mask(s) {
    var m = s.match(/^\+?1([2-9]\d\d)([2-9]\d\d)(\d\d\d\d)$/);
    if (m)
        return "+1 " + m[1] + "-" + m[2] + "-xxxx";
    var m = s.match(/^\+?(\d{6,})$/);
    if (m)
        return "+" + m[1].slice(0, m[1].length - 4);
    return s;
}

/// turns string bool into normal bool
function fs_bool(s) {
    return (s == "true");
}

/// send a single command to freeswitch not caring about result
function fs_api(cmd) {
    var fsev = freeswitch.eventSocket(settings.freeswitch);
    var deathclock = setTimeout(function() {
        fsev.close();
    }, 1000);
    fsev.on('connect', function() {
        fsev.send("api " + cmd);
        fsev.close();
        clearTimeout(deathclock);
    });
}

//////////////////////////////////////////////////////////////////////
// prevent crashes at all costs

process.on('uncaughtException', function (err) {
    console.error('UNHANDLED EXCEPTION');
    console.trace(err);
});
