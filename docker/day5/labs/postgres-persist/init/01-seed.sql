CREATE TABLE IF NOT EXISTS seed_data (
  id serial PRIMARY KEY,
  label text NOT NULL
);

INSERT INTO seed_data (label) VALUES ('init script ran on first volume init');
