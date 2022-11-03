CREATE TABLE user (
    id int NOT NULL AUTO_INCREMENT,
    email varchar(100) NOT NULL,
    name varchar(1000) NOT NULL,
    password varchar(100) NOT NULL,
    admin int NOT NULL,
    phonenumber varchar(10),
    PRIMARY KEY (id)
);