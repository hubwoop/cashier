PRAGMA foreign_keys = ON;

drop table if exists items_to_transactions;
create table items_to_transactions (
  item integer not null,
  'transaction' integer not null,
  foreign key(item) references items(id),
  foreign key('transaction') references transactions(id)
);

drop table if exists items;
create table items (
  id integer primary key autoincrement,
  title text not null,
  price real not null,
  image_link text,
  color text
);

drop table if exists transactions;
create table transactions (
  id integer primary key autoincrement,
  date text not null,
  sum real not null
);

