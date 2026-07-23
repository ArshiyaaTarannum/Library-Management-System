SELECT 1;
SHOW DATABASES;
USE library;
SHOW TABLES;
SELECT * FROM Book LIMIT 5;
ALTER TABLE Book
ADD COLUMN EntryDate DATE;

CREATE TABLE BorrowBook(
    IssueID VARCHAR(10) PRIMARY KEY,
    BookID VARCHAR(20),
    StudentName VARCHAR(100),
    StudentID VARCHAR(30),
    IssueDate DATE,
    DueDate DATE,
    ReturnDate DATE,
    Status VARCHAR(20)
);

ALTER TABLE BorrowBook
ADD EntryDate DATE DEFAULT (CURRENT_DATE);
ALTER TABLE BorrowBook
ADD CONSTRAINT fk_book
FOREIGN KEY(BookID)
REFERENCES Book(BookID);

ALTER TABLE Book
ADD COLUMN Language VARCHAR(50) NOT NULL,
ADD COLUMN Edition VARCHAR(50) NOT NULL,
ADD COLUMN TotalCopies INT NOT NULL DEFAULT 1,
ADD COLUMN PurchasePrice DECIMAL(10,2) NOT NULL DEFAULT 0.00;
CREATE TABLE BookCopy (
    CopyID VARCHAR(20) PRIMARY KEY,
    BookID VARCHAR(20) NOT NULL,
    Shelf VARCHAR(30) NOT NULL,
    Status ENUM(
        'Available',
        'Issued',
        'Reserved',
        'Lost',
        'Damaged',
        'Repair'
    ) DEFAULT 'Available',
    ConditionRemark ENUM(
        'Excellent',
        'Good',
        'Worn',
        'Damaged',
        'Repair Needed',
        'Lost'
    ) DEFAULT 'Excellent',
    CustomRemark VARCHAR(255),
    DateAdded DATE DEFAULT (CURRENT_DATE),
    FOREIGN KEY (BookID)
    REFERENCES Book(BookID)
    ON DELETE CASCADE
);
CREATE DATABASE library_backup;
CREATE TABLE library_backup.Book AS
SELECT * FROM library.Book;

CREATE TABLE library_backup.Category AS
SELECT * FROM library.Category;
USE library;

CREATE TABLE Shelf(

    ShelfID VARCHAR(10) PRIMARY KEY,

    ShelfName VARCHAR(50) NOT NULL,

    Location VARCHAR(100),

    Capacity INT DEFAULT 50,

    Status ENUM(
        'Active',
        'Inactive'
    ) DEFAULT 'Active'

);

ALTER TABLE Book
DROP COLUMN Status,
DROP COLUMN TotalCopies;
INSERT INTO BookCopy
(
    CopyID,
    BookID,
    Shelf,
    Status,
    ConditionRemark,
    DateAdded
)

SELECT

    CONCAT(
        'CP',
        LPAD(
            ROW_NUMBER() OVER(),
            6,
            '0'
        )
    ),

    BookID,

    'Unassigned',

    'Available',

    'Excellent',

    EntryDate

FROM Book;
ALTER TABLE BookCopy
MODIFY Shelf VARCHAR(30) DEFAULT 'Unassigned';
SELECT * FROM BookCopy;
SHOW CREATE TABLE BookCopy;

CREATE DATABASE IF NOT EXISTS library;
USE library;

CREATE TABLE IF NOT EXISTS Category (
    CategoryID   VARCHAR(10) PRIMARY KEY,
    CategoryName VARCHAR(50) NOT NULL
);

DROP TABLE IF EXISTS BookCopy;
DROP TABLE IF EXISTS Book;
DROP TABLE IF EXISTS BorrowBook;

CREATE TABLE Book (
    BookID          VARCHAR(20) PRIMARY KEY,
    BookName        VARCHAR(100) NOT NULL,
    Author          VARCHAR(100) NOT NULL,
    CategoryID      VARCHAR(10) NOT NULL,
    Publication     VARCHAR(150),
    PublicationDate DATE,
    EntryDate       DATE NOT NULL,
    Language        VARCHAR(50),
    Edition         VARCHAR(50),
    PurchasePrice   DECIMAL(10,2),

    FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID)
);

CREATE TABLE BookCopy (
    CopyID          VARCHAR(20) PRIMARY KEY,
    BookID          VARCHAR(20) NOT NULL,
    Shelf           VARCHAR(50) NOT NULL,
    Status          VARCHAR(20) NOT NULL,
    `Condition`     VARCHAR(20) NOT NULL,
    AdditionalRemark VARCHAR(255),
    DateAdded       DATE,

    FOREIGN KEY (BookID) REFERENCES Book(BookID)
);
CREATE TABLE Shelf
(
    ShelfID VARCHAR(10) PRIMARY KEY,
    ShelfName VARCHAR(50) NOT NULL UNIQUE,
    Description VARCHAR(255)
);
DESCRIBE Shelf;
ALTER TABLE Shelf
MODIFY Capacity INT NOT NULL DEFAULT 50,
MODIFY Status ENUM('Active','Inactive')
NOT NULL DEFAULT 'Inactive';

CREATE TABLE IF NOT EXISTS Member (
    MemberID      VARCHAR(20) PRIMARY KEY,
    MemberName    VARCHAR(100) NOT NULL,
    Phone         VARCHAR(20),
    Email         VARCHAR(100) UNIQUE,
    Address       VARCHAR(255),
    JoinDate      DATE NOT NULL,
    IsActive      TINYINT(1) NOT NULL DEFAULT 1,

    CHECK (IsActive IN (0,1))
);
ALTER TABLE Member
MODIFY COLUMN IsActive BOOLEAN NOT NULL DEFAULT TRUE;

CREATE TABLE IF NOT EXISTS IssueTransaction (

    TransactionID      VARCHAR(20) PRIMARY KEY,

    CopyID             VARCHAR(20) NOT NULL,
    MemberID           VARCHAR(20) NOT NULL,

    IssueDate          DATE NOT NULL,
    DueDate            DATE NOT NULL,
    ActualReturnDate   DATE,

    Status             VARCHAR(20) NOT NULL DEFAULT 'Issued',

    FineAmount         DECIMAL(10,2) NOT NULL DEFAULT 0,
    PaymentStatus      VARCHAR(20) NOT NULL DEFAULT 'Pending',

    RenewCount         INT NOT NULL DEFAULT 0,

    FOREIGN KEY (CopyID)
        REFERENCES BookCopy(CopyID),

    FOREIGN KEY (MemberID)
        REFERENCES Member(MemberID),

    CHECK (Status IN ('Issued','Returned')),

    CHECK (PaymentStatus IN ('Pending','Paid','Waived'))
);
ALTER TABLE IssueTransaction
MODIFY COLUMN Status
ENUM('Issued','Returned')
NOT NULL DEFAULT 'Issued',

MODIFY COLUMN PaymentStatus
ENUM('Pending','Paid','Waived')
NOT NULL DEFAULT 'Pending',

MODIFY COLUMN FineAmount
DECIMAL(10,2)
NOT NULL DEFAULT 0.00,

MODIFY COLUMN RenewCount
INT
NOT NULL DEFAULT 0;
DESCRIBE Member;
DESCRIBE IssueTransaction;

CREATE TABLE IF NOT EXISTS FinePayment (
    PaymentID      VARCHAR(20) PRIMARY KEY,
    TransactionID  VARCHAR(20) NOT NULL,
    AmountPaid     DECIMAL(10,2) NOT NULL,
    PaymentMode    VARCHAR(10) NOT NULL,
    PaymentDate    DATE NOT NULL,

    FOREIGN KEY (TransactionID) REFERENCES IssueTransaction(TransactionID)
);

CREATE TABLE LibraryPolicy
(
    PolicyID INT PRIMARY KEY DEFAULT 1,

    LibraryName VARCHAR(100) NOT NULL,

    MaxBooksPerMember INT NOT NULL DEFAULT 4,

    LoanPeriodDays INT NOT NULL DEFAULT 14,

    MembershipDurationMonths INT NOT NULL DEFAULT 12,

    FineBaseRate DECIMAL(10,2) NOT NULL DEFAULT 5,

    FineIncreaseEveryDays INT NOT NULL DEFAULT 30,

    FineRateIncrease DECIMAL(10,2) NOT NULL DEFAULT 5,

    FineCapBuffer DECIMAL(10,2) NOT NULL DEFAULT 100,

    AllowRenewal BOOLEAN DEFAULT TRUE,

    MaxRenewals INT DEFAULT 2
);