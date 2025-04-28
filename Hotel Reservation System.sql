CREATE TABLE Guest (
    Guest_ID SERIAL PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Contact_Number VARCHAR(15) UNIQUE NOT NULL,
    Address TEXT NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE Room (
    Room_ID SERIAL PRIMARY KEY,
    Room_Type VARCHAR(50) NOT NULL,
    Price DECIMAL(10,2) NOT NULL,
    Status VARCHAR(20) CHECK (Status IN ('Available', 'Booked', 'Maintenance')) NOT NULL
);

INSERT INTO Room (Room_Type, Price, Status) values
('Single', 50.00, 'Available'),
('Single', 50.00, 'Available'),
('Double', 80.00, 'Available'),
('Suite', 150.00, 'Available');

CREATE TABLE Booking (
    Booking_ID SERIAL PRIMARY KEY,
    Guest_ID INT REFERENCES Guest(Guest_ID) ON DELETE CASCADE,
    Check_in_Date DATE NOT NULL,
    Check_out_Date DATE NOT NULL,
    Total_Amount DECIMAL(10,2) NOT NULL
);

CREATE TABLE Booking_Room (
    Booking_Room_ID SERIAL PRIMARY KEY,
    Booking_ID INT REFERENCES Booking(Booking_ID) ON DELETE CASCADE,
    Room_ID INT REFERENCES Room(Room_ID) ON DELETE CASCADE,
    Check_in_Date DATE NOT NULL,
    Check_out_Date DATE NOT NULL
);

CREATE TABLE Service (
    Service_ID SERIAL PRIMARY KEY,
    Service_Name VARCHAR(100) NOT NULL,
    Service_Cost DECIMAL(10,2) NOT NULL
);

INSERT INTO Service (Service_Name, Service_Cost) VALUES
('Extra Bed', 20.00),
('Airport Pickup', 50.00),
('Breakfast', 10.00),
('Laundry', 15.00);

CREATE TABLE Booking_Service (
    Booking_Service_ID SERIAL PRIMARY KEY,
    Booking_ID INT REFERENCES Booking(Booking_ID) ON DELETE CASCADE,
    Service_ID INT REFERENCES Service(Service_ID) ON DELETE CASCADE,
    Quantity INT CHECK (Quantity > 0) NOT NULL
);

CREATE TABLE Payment (
    Payment_ID SERIAL PRIMARY KEY,
    Booking_ID INT REFERENCES Booking(Booking_ID) ON DELETE CASCADE,
    Amount_Paid DECIMAL(10,2) NOT NULL,
    Payment_Date DATE NOT NULL,
    Payment_Method VARCHAR(20) CHECK (Payment_Method IN ('Credit Card', 'Cash', 'Online')) NOT NULL
);

CREATE TABLE Check_Out (
    Check_Out_ID SERIAL PRIMARY KEY,
    Guest_ID INT REFERENCES Guest(Guest_ID),
    Booking_ID INT REFERENCES Booking(Booking_ID),
    Check_Out_Date DATE NOT NULL,
    Total_Amount DECIMAL(10,2) NOT NULL
);