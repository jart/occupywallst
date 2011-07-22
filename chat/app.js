
var settings = {
    domain: "dev.occupywallst.org",
    db: {'database': 'occupywallst'},
    ssl_enable: false,
    ssl_key: '/etc/apache2/ssl/occupywallst.org/key',
    ssl_cert: '/etc/apache2/ssl/occupywallst.org/crt-cabundle',
    random: '/dev/urandom',
};

var fs = require("fs");
var net = require("net");
var express = require('express');
var memcached = require('memcached');
var cache = new memcached("127.0.0.1:11211");
var pg = require('pg').native;

var app;
if (settings.ssl_enable) {
    app = express.createServer({
        key: fs.readFileSync(settings.ssl_key),
        cert: fs.readFileSync(settings.ssl_cert)
    });
} else {
    app = express.createServer();
}

var io = require('socket.io').listen(app);

app.configure(function () {
    app.set('views', __dirname + '/views');
    app.set('view engine', 'jade');
    app.redirect('login', ((settings.use_ssl ? 'https' : 'http') + 
                           '://' + settings.domain + '/login/'));
    // app.use(express.logger());
    app.use(express.bodyParser());
    app.use(express.methodOverride());
    app.use(express.cookieParser());
    app.use(app.router);
    app.use(express.static(__dirname + '/public'));
});
app.configure('development', function () {
    app.use(express.errorHandler({dumpExceptions: true, showStack: true}));
});
app.configure('production', function () {
    app.use(express.errorHandler()); 
});

io.configure(function () {
});
io.configure('development', function () {
    console.log("SOCKET.IO DEVELOPMENT MODE");
    io.set('log level', 3);
    io.set('transports', ['websocket', 'flashsocket']);
});
io.configure('production', function () {
    console.log("SOCKET.IO PRODUCTION MODE");
    io.set('log level', 1);
    io.enable('browser client etag');
    io.enable('browser client minification');
    io.set('transports', ['websocket', 'flashsocket', 'htmlfile',
                          'xhr-polling', 'jsonp-polling']);
});

//////////////////////////////////////////////////////////////////////

app.get('/', function (req, res) {
    // if (!req.cookies.sessionid) {
    //     res.redirect('login');
    //     return;
    // }
    res.render('index', {});
});

var all_users = {};
var all_rooms = {};
var guest_counter = 1;
var all_user_ids = {};
var ip_limits = {};

io.of('/chat').authorization(function (handshake, callback) {
    handshake.user = {};
    var cookies = handshake.headers.cookie;
    var res = cookies.match(/sessionid=([0-9a-f]+)/);
    var sessionid = res ? res[1] : null;
    get_session(sessionid, function (err, session) {
        if (err) { callback(null, true); return; }
        get_user(session._auth_user_id, function (err, user) {
            if (err) { callback(null, true); return; }
            handshake.user.name = user.username;
            handshake.user.is_op = user.is_staff;
            callback(null, true);
        });
    });
}).on('connection', function (sock) {
    var my_rooms = {};
    var me = sock.handshake.user;
    if (!me.name) {
        me.is_op = false;
        me.name = "anon" + guest_counter++;
    }
    all_users[me.name] = me;
    all_user_ids[me.name] = sock.id;

    // penalize ip addresses that do more than:
    // - 5 things every 10 seconds
    // - 20 things every 60 seconds
    var ip = sock.handshake.address.address;
    if (!ip_limits[ip]) {
        ip_limits[ip] = [
            {
                start: Date.now(),
                interval: 60 * 1000,
                max: 20,
                count: 0,
                penalty: 2000,
                prev: null,
            },
            {
                start: Date.now(),
                interval: 20 * 1000,
                max: 5,
                count: 0,
                penalty: 1000,
            },
        ];
    }
    var limits = ip_limits[ip];
    var last_penalty_ends = Date.now();
    var is_dead = false;

    function throttle(callback) {
        var timeout = 0;
        for (var i in limits) {
            var limit = limits[i];
            var now = Date.now();
            var end = limit.start + limit.interval;
            if (now > end) {
                limit.start = now;
                limit.count = 1;
            } else {
                limit.count++;
                if (limit.count >= limit.max) {
                    timeout = Math.max(timeout, limit.penalty);
                }
            }
        }
        if (timeout > 0) {
            if (last_penalty_ends > now) {
                timeout += last_penalty_ends - now;
            }
            if (timeout > 20000) {
                console.log("User %s (%s) floods!  Dropping msg", me.name, ip);
            } else {
                console.log("User %s (%s) msg being throttled for %dms",
                        me.name, ip, timeout);
                setTimeout(callback, timeout);
                last_penalty_ends = now + timeout;
            }
        } else {
            callback();
        }
    }

    sock.on('join', function (msg) {
        throttle(function () {
            if (is_dead || my_rooms[msg.room] || !msg.room)
                return;
            if (!all_rooms[msg.room]) {
                all_rooms[msg.room] = {
                    name: msg.room,
                    users: {},
                };
            }
            all_rooms[msg.room].users[me.name] = me;
            my_rooms[msg.room] = all_rooms[msg.room];
            sock.join(msg.room);
            sock.emit('join_ack', {
                room: msg.room,
                user: me,
                users: all_rooms[msg.room].users,
            });
            sock.broadcast.to(msg.room).emit('join', {
                room: msg.room,
                user: me,
            });
        });
    });

    sock.on('msg', function (msg) {
        throttle(function () {
            if (is_dead || !my_rooms[msg.room] || !msg.text)
                return;
            sock.broadcast.to(msg.room).emit('msg', {
                room: msg.room,
                user: me,
                text: msg.text,
                emo: msg.emo,
            });
        });
    });

    sock.on('kick', function (msg) {
        if (!me.is_op)
            return;
        if (!all_users[msg.user.name])
            return;
        process.emit('kick', msg);
    });

    sock.on('disconnect', function () {
        is_dead = true;
        var room;
        for (room in my_rooms) {
            sock.broadcast.to(room).emit('leave', {
                room: room,
                user: me,
            });
            delete all_rooms[room].users[me.name];
        }
        my_rooms = {};
        delete all_users[me.name];
        delete all_user_ids[sock.id];
    });

    function on_leave(msg) {
        if (!my_rooms[msg.room])
            return;
        sock.broadcast.to(msg.room).emit('leave', {
            room: msg.room,
            user: me,
        });
        sock.emit('leave_ack', {
            room: msg.room,
            user: me,
        });
        sock.leave(msg.room);
        delete my_rooms[msg.room];
        delete all_rooms[msg.room].users[me.name];
    }

    sock.on('leave', on_leave);

    process.on('kick', function (msg) {
        if (msg.user.name == me.name && my_rooms[msg.room]) {
            sock.emit('kicked', msg);
            on_leave(msg);
        }
    });
});

app.listen(80, "chat." + settings.domain);
console.log("https listening on %s:%d in %s mode", app.address().address,
            app.address().port, app.settings.env);

//////////////////////////////////////////////////////////////////////

// var fps = net.createServer(function (sock) {
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

/// Return one row from database
function db_fetch(query, args, callback) {
    pg.connect(settings.db, function(err, db) {
        if (err) {
            console.log("failed to connect to postgresql");
            console.error(err);
            callback("database is down D:", null);
            return;
        }
        db.query(query, args, function(err, result) {
            if (err) {
                console.log("query failed: %s %j", query, args);
                console.error(err);
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
    cache.get(sessionid, function (err, result) {
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
            console.log("corrupt session data: %s", result);
            console.error(err);
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
    fs.open(settings.random, 'r', function (err, fd) {
        if (err) {
            console.error(err);
            callback("no random device", null);
            return;
        }
        var buf = new Buffer(bytes);
        fs.read(fd, buf, 0, buf.length, 0, function (err, bytes, buf) {
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
