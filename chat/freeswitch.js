// node.js module for talking to freeswitch mod_event_socket
//
// the goal here is to get information about what's happening in the
// phone system in real-time and dispatch it to the web browser.

var net = require("net");
var util = require('util');
var events = require('events');

function EventSocket(options) {
    this.host = "localhost",
    this.port = 8021;
    this.password = "ClueCon";
    this.reconnect_timeout = 5000;
    this.login_timeout = 1000;
    for (var k in options) {
        this[k] = options[k];
    }
    this.sock = null;
    this.want_close = false;
}

util.inherits(EventSocket, events.EventEmitter);

EventSocket.prototype.connect = function() {
    var self = this;
    var state;
    var login_timer;
    var buf = "";

    function log(msg) {
        console.log("freeswitch(%s:%d): %s", self.host, self.port, msg);
    }

    function pre_auth(msg) {
        if (msg.is('auth/request')) {
            self.send("auth " + self.password);
            state = auth;
        } else {
            log("expected auth/request but got: %j", msg);
            self.sock.end();
        }
    }

    function auth(msg) {
        if (msg.is_ok()) {
            self.emit('connect');
            state = established;
            clearTimeout(login_timer);
        } else {
            log("auth failed: %j", msg);
            self.sock.end();
        }
    }

    function established(msg) {
        if (msg.is_event()) {
            self.emit('event', msg.hdrs['content-type'], msg.body);
        } else {
            self.emit('msg', msg);
        }
    }

    self.sock = net.createConnection(self.port, self.host);
    self.sock.setEncoding('utf8');
    self.sock.on('connect', function() {
        log("connected");
        state = pre_auth;
        login_timer = setTimeout(function() {
            console.log("freeswitch login timer expired");
            self.sock.end();
        }, self.login_timeout);
    }).on('error', function(e) {
        log(e.message);
    }).on('close', function() {
        self.sock = null;
        clearTimeout(login_timer);
        if (self.want_close) {
            self.emit('close');
        } else {
            setTimeout(function() {
                self.connect();
            }, self.reconnect_timeout);
        }
    }).on('data', function(data) {
        try {
            buf += data;
            var res = parse(buf);
            if (!res)
                return;
            var msg = res.msg;
            buf = res.remain;
            if (msg.is('text/disconnect-notice')) {
                self.sock.end();
            } else {
                state(msg);
            }
        } catch (e) {
            console.error(e);
            self.sock.end();
        }
    });
};

EventSocket.prototype.send = function(cmd) {
    this.sock.write(cmd + "\n\n");
    return this;
};

EventSocket.prototype.close = function() {
    this.want_close = true;
    this.sock.end();
    return this;
};

/// ghetto buffering / message parsing
function parse(data) {
    if (data.length > 1024 * 1024)
        throw "too much buffer D:";
    var hdrs = {};
    var body = "";
    var remain = "";
    var hend = data.indexOf("\n\n");
    if (hend == -1)
        return null;
    var hdrs = data.slice(0, hend).split(/\n/);
    for (i in hdrs) {
        var hdr = hdrs[i];
        var j = hdr.indexOf(': ');
        if (j == -1)
            throw "bad freeswitch header";
        var key = hdr.slice(0, j).toLowerCase();
        var val = hdr.slice(j + 2);
        hdrs[key] = val;
    }
    if (!hdrs['content-type'])
        throw "freeswitch msg missing content-type";
    if (hdrs['content-length']) {
        var len = parseInt(hdrs['content-length']);
        if (data.length - hend - 2 < len)
            return null;
        body = data.slice(hend + 2, hend + 2 + len);
        remain = data.slice(hend + 2 + len);
    } else {
        remain = data.slice(hend + 2);
    }
    if (hdrs['content-type'] == 'text/event-json') {
        body = JSON.parse(body);
    }
    return {msg: new Message(hdrs, body), remain: remain};
}

function Message(hdrs, body) {
    this.hdrs = hdrs;
    this.body = body;
};

/// returns true is msg is a command response and was successful
Message.prototype.is = function(type) {
    return (this.hdrs['content-type'] == type &&
            true);
};

/// returns true is msg is a command response and was successful
Message.prototype.is_ok = function() {
    return (this.is('command/reply') &&
            this.hdrs['reply-text'].match(/^\+OK/) &&
            true);
};

/// returns true if msg is an event
Message.prototype.is_event = function() {
    return (this.hdrs['content-type'].match(/^text\/event-/) &&
            true);
};

exports.eventSocket = function(options) {
    var es = new EventSocket(options);
    es.connect();
    return es;
};
