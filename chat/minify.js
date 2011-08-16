#!/usr/bin/env node

var fs = require('fs');
var uglify = require('uglify-js');

var outfile = process.argv[2];
var infiles = process.argv.slice(3);

function min(code) {
    var ast = uglify.parser.parse(code);
    ast = uglify.uglify.ast_mangle(ast);
    ast = uglify.uglify.ast_squeeze(ast);
    return uglify.uglify.gen_code(ast);
}

var size = 0;
var outcode = '';
for (var n in infiles) {
    var infile = infiles[n];
    var incode = fs.readFileSync(infile, 'utf8');
    size += incode.length;
    outcode += min(incode) + ';\n';
}

fs.writeFileSync(outfile, outcode);
console.error("occupywallst javascript minified %d% to %dkB",
              100 - Math.round(outcode.length / size * 100),
              Math.round(outcode.length / 1024));
