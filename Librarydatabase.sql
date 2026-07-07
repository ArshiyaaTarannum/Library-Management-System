CREATE DATABASE library;
USE library;
CREATE TABLE Category(
    CategoryID VARCHAR(10) PRIMARY KEY,
    CategoryName VARCHAR(50)
);
CREATE TABLE Book(
    BookID VARCHAR(20) PRIMARY KEY,
    BookName VARCHAR(100),
    Author VARCHAR(100),
    CategoryName VARCHAR(100) NOT NULL,
    Publication VARCHAR(150),
    PublicationDate DATE,
    FOREIGN KEY(CategoryID)
    REFERENCES Category(CategoryID)
);
USE library;

DELETE FROM Category
WHERE CategoryID in("CAT008");
SET SQL_SAFE_UPDATES = 1;
SELECT * FROM Category;
