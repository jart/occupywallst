// throttler: prevent a function from being called too much

function throttler(settings) {
    var sessions = {};
    var sweep_count = 0;

    function get_session(id) {
        if (sessions[id])
            return sessions[id];
        sweep();
        var now = Date.now();
        var session = {
            last_event: now,
            last_penalty_ends: now,
            limits: []
        };
        for (var i in settings.limits) {
            session.limits.push({
                interval: settings.limits[i].interval,
                max: settings.limits[i].max,
                penalty: settings.limits[i].penalty,
                start: now,
                count: 0
            });
        }
        sessions[id] = session;
        return session;
    }

    function sweep() {
        if (++sweep_count == 100) {
            sweep_count = 0;
            var now = Date.now();
            var sessions2 = {};
            for (var id in sessions) {
                var session = sessions[i];
                if (session.last_event + settings.max_age > now) {
                    sessions2[id] = session;
                }
            }
            sessions = sessions2;
        }
    }

    function throttle(id, callback) {
        var session = get_session(id);
        var now = Date.now();
        var timeout = 0;
        session.last_event = now;
        for (var i in session.limits) {
            var limit = session.limits[i];
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
            if (session.last_penalty_ends > now) {
                timeout += session.last_penalty_ends - now;
            }
            if (timeout > 20000) {
                if (settings.logging)
                    console.log("%s: flood detected, dropping action", id);
            } else {
                if (settings.logging)
                    console.log("%s: action throttled for %dms", id, timeout);
                setTimeout(callback, timeout);
                session.last_penalty_ends = now + timeout;
            }
        } else {
            callback();
        }
    }

    return throttle;
}

exports.throttler = throttler;
