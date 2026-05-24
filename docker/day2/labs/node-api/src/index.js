const express = require('express');

const app = express();
const port = process.env.PORT || 3000;

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'handbook-node-api' });
});

app.get('/', (_req, res) => {
  res.send('Docker Day 2 — Node API');
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Listening on ${port}`);
});
