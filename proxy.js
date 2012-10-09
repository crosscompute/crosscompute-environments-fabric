var https = require('https'),
    httpProxy = require('http-proxy'),
    fs = require('fs');
httpProxy.createServer(8888, 'localhost', {
    https: {
        key: fs.readFileSync('proxy.key', 'utf8'),
        cert: fs.readFileSync('proxy.pem', 'utf8')
    },
    target: {
        https: true
    }
}).listen(443);
