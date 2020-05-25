create database chatroom character set utf8;


create table Manage_info
(id int primary key auto_increment,
user varchar(24) not null,
passwd varchar(32)  not null,
reg_date datetime   default now(),
last_log datetime   default now(),
unique user_index (user));


create table Chat_record
(id int primary key auto_increment,
M_to_C int not null,
content varchar(144)  not null,
date_depart varchar(16) ,
time_depart varchar(16) ,
constraint M_to_C foreign key(M_to_C) references Manage_info(id));


