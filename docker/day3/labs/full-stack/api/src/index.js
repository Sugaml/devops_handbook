const express = require('express');
const { Pool } = require('pg');

const app = express();
const port = 3000;
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

app.get('/health', async (_req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({ status: 'ok', db: 'connected' });
  } catch (err) {
    res.status(503).json({ status: 'error', message: err.message });
  }
});

app.get('/', (_req, res) => {
  res.json({ message: 'Day 3 full-stack API' });
});

app.listen(port, '0.0.0.0', () => {
  console.log(`API listening on ${port}`);
});
