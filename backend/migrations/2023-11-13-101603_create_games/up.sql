CREATE TABLE games (
  id INTEGER PRIMARY KEY NOT NULL,
  `teams` VARCHAR NOT NULL,
  `location` TEXT NOT NULL,
  `datetime` TEXT NOT NULL UNIQUE
)
