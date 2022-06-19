drop database if exists hashing;

create database hashing;

\c hashing;

create table users (
    id serial primary key,
    username text unique not null,
    password text not null
);