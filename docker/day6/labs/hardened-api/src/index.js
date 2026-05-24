const express = require('express');

const app = express();
const port = process.env.PORT || 3000;

app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.get('/', (_req, res) => {
  res.json({ message: 'Day 6 hardened API' });
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Listening on ${port}`);
});
