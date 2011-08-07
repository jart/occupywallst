
process.on('uncaughtException', function (err) {
    console.error('UNHANDLED EXCEPTION');
    console.trace(err);
});

fuck();

//////////////////////////////////////////////////////////////////////

// var pg = require('pg').native;

// pg.connect({'database': 'occupywallst'}, function(err, db) {
//     if (err) {
//         console.dir(err);
//         process.exit(0);
//     }
//     var query = ("SELECT *" +
//                  "  FROM auth_user" +
//                  " WHERE id = $1");
//     db.query(query, [1], function(err, result) {
//         console.log("Row count: %d", result.rows.length);
//         console.log("Username: %s", result.rows[0].username);
//         process.exit(0);
//     });
// });

//////////////////////////////////////////////////////////////////////

// var memcached = require('memcached');
// var cache = new memcached("127.0.0.1:11211");

// function get_user(handshake, callback) {
//     var cookies = handshake.headers.cookie;
//     var res = cookies.match(/sessionid=([0-9a-f]+)/);
//     var sessionid = res ? res[1] : null;
//     if (!sessionid) {
//         callback("no sessionid cookie found", null);
//         return;
//     }
//     cache.get(sessionid, function (err, result) {
//         if (err) {
//             callback("session not found", null);
//             return;
//         }
//         var session;
//         try {
//             session = JSON.parse(result);
//         } catch (err) {
//             console.log("corrupt session data: %s", result);
//             console.error(err);
//             callback("corrupt session data", null);
//             return;
//         }
//         callback(null, session);
//     });
// }

//////////////////////////////////////////////////////////////////////

// try {
//     console.dir(JSON.parse('{'));
// } catch (err) {
//     console.error(err);
// }

// process.exit(0);

// var memcached = require('memcached');
// var cache = new memcached("127.0.0.1:11211");
// console.log("--------------------------------");
// console.log("--------------------------------");
// console.log("--------------------------------");
// cache.get('8ce9d68e0b2d78be33c47b056c8b2d3e', function (err, result) {
//     console.dir(err);
//     console.dir(result);
// });
