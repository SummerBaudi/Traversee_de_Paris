import http from 'node:http';

const port = process.env.PORT || 3001;

const server = http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', service: 'api' }));
    return;
  }

  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ message: 'Traversée de Paris API bootstrap' }));
});

server.listen(port, () => {
  console.log(`API listening on http://localhost:${port}`);
});
