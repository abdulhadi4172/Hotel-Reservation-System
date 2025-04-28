import pg8000
from tkinter import *
from tkinter import messagebox, ttk
import datetime

# Establish Database Connection
connection = pg8000.connect(
    user='assignment',
    password='assignment',
    database='Hidden Paradise Hotel',
    host='localhost'
)
cursor = connection.cursor()
print("Connected to DB")

root = Tk()
root.title("Hotel Reservation System")
root.geometry("900x600")

# Function to Validate First Login (General Dashboard Access)
def validate_login():
    username = username_entry.get()
    password = password_entry.get()
    if username == "Abdul" and password == "Hadi":
        messagebox.showinfo("Sucess", "Sucessfully Logged in")
        dashboard_frame.lift()
    else:
        messagebox.showerror("Error", "Invalid Username or Password")

# Function to Validate Manager Login (Report Access)
def validate_manager_login():
    username = manager_username_entry.get()
    password = manager_password_entry.get()
    if username == "admin" and password == "admin":
        messagebox.showinfo("Sucess", "Login Sucessfully to Manager Page")
        report_frame.lift()
    else:
        messagebox.showerror("Error", "Invalid Manager Credentials")

# Function to Check Room Availability
def check_room_availability():
    cursor.execute("SELECT Room_ID, Room_Type, Price FROM Room WHERE Status = 'Available'")
    available_rooms = cursor.fetchall()
    
    if available_rooms:
        rooms_text = "Available Rooms:\n"
        for room in available_rooms:
            rooms_text += f"Room ID: {room[0]}, Type: {room[1]}, Price: ${room[2]}\n"
        messagebox.showinfo("Room Availability", rooms_text)
    else:
        messagebox.showinfo("Room Availability", "No rooms available at the moment.")

# Fetch available rooms
def fetch_available_rooms():
    cursor.execute("SELECT Room_ID, Room_Type FROM Room WHERE Status = 'Available'")
    rooms = cursor.fetchall()
    return rooms

# Function to update the room dropdown dynamically
def update_room_dropdown():
    available_rooms = fetch_available_rooms()
    room_dict.clear()
    for room in available_rooms:
        room_dict[f"Room {room[0]} - {room[1]}"] = room[0]
    room_dropdown['values'] = list(room_dict.keys())

# Function to Mark Room as Available After Payment
def mark_room_available():
    guest_id = payment_guest_id_entry.get()
    try:
        cursor.execute("""
            UPDATE Room 
            SET Status = 'Available' 
            WHERE Room_ID IN (
                SELECT Room_ID FROM Booking_Room 
                JOIN Booking ON Booking.Booking_ID = Booking_Room.Booking_ID 
                WHERE Booking.Guest_ID = %s
            );
        """, (guest_id,))
        connection.commit()
        messagebox.showinfo("Success", "Room marked as available successfully!")
        update_room_dropdown()  # Refresh available rooms after payment
    except Exception as e:
        messagebox.showerror("Error", f"Database Error: {e}")

# Function to Add Guest
def add_guest():
    name = guest_name_entry.get()
    contact = guest_contact_entry.get()
    address = guest_address_entry.get()
    email = guest_email_entry.get()
    checkin_date = datetime.date.today()
    stay_duration = int(guest_days_entry.get())
    checkout_date = checkin_date + datetime.timedelta(days=stay_duration)
    selected_room = room_var.get()
    room_id = room_dict.get(selected_room)
    
    if not name or not contact or not address or not email or not room_id:
        messagebox.showerror("Error", "All fields are required!")
        return
    
    try:
        cursor.execute(
            "INSERT INTO Guest (Name, Contact_Number, Address, Email) VALUES (%s, %s, %s, %s) RETURNING Guest_ID;",
            (name, contact, address, email)
        )
        guest_id = cursor.fetchone()[0]
        cursor.execute(
            "INSERT INTO Booking (Guest_ID, Check_in_Date, Check_out_Date, Total_Amount) VALUES (%s, %s, %s, 0) RETURNING Booking_ID;",
            (guest_id, checkin_date, checkout_date)
        )
        booking_id = cursor.fetchone()[0]
        cursor.execute(
            "INSERT INTO Booking_Room (Booking_ID, Room_ID, Check_in_Date, Check_out_Date) VALUES (%s, %s, %s, %s);",
            (booking_id, room_id, checkin_date, checkout_date)
        )
        cursor.execute("UPDATE Room SET Status = 'Booked' WHERE Room_ID = %s;", (room_id,))
        connection.commit()
        messagebox.showinfo("Success", f"Guest added successfully! Guest ID: {guest_id}, Room Booked: {room_id}")
        update_room_dropdown()  # Refresh available rooms after booking
    except Exception as e:
        messagebox.showerror("Error", f"Database Error: {e}")

# Fetch service names and costs from the database
def fetch_services():
    cursor.execute("SELECT Service_ID, Service_Name, Service_Cost FROM Service")
    return cursor.fetchall()

services = fetch_services()
service_dict = {f"{service[1]} - ${service[2]}": service[0] for service in services}  # Mapping 'Service Name - Cost' -> Service ID

# Function to Add Extra Services
def add_service():
    guest_id = service_guest_id_entry.get()
    selected_service = service_name_var.get()
    service_id = service_dict.get(selected_service)  # Get Service ID from selected name
    quantity = service_quantity_entry.get()
    
    if not guest_id or not service_id or not quantity:
        messagebox.showerror("Error", "All fields are required!")
        return
    
    try:
        cursor.execute(
            "INSERT INTO Booking_Service (Booking_ID, Service_ID, Quantity) VALUES "
            "((SELECT Booking_ID FROM Booking WHERE Guest_ID = %s), %s, %s);",
            (guest_id, service_id, quantity)
        )
        connection.commit()
        messagebox.showinfo("Success", "Service added successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Database Error: {e}")

# Function to Process Payment
def process_payment():
    guest_id = payment_guest_id_entry.get()
    
    # Calculate extra services cost
    cursor.execute("""
        SELECT SUM(Service_Cost * Quantity) FROM Booking_Service 
        JOIN Service ON Booking_Service.Service_ID = Service.Service_ID 
        WHERE Booking_ID = (SELECT Booking_ID FROM Booking WHERE Guest_ID = %s);
    """, (guest_id,))
    service_cost = cursor.fetchone()[0] or 0
    
    # Calculate room cost based on stay duration
    cursor.execute("""
        SELECT Room.Price, Booking.Check_in_Date, Booking.Check_out_Date 
        FROM Room 
        JOIN Booking_Room ON Room.Room_ID = Booking_Room.Room_ID 
        JOIN Booking ON Booking.Booking_ID = Booking_Room.Booking_ID 
        WHERE Booking.Guest_ID = %s;
    """, (guest_id,))
    room_data = cursor.fetchone()
    
    if room_data:
        room_price, checkin_date, checkout_date = room_data
        stay_duration = (checkout_date - checkin_date).days
        room_cost = room_price * stay_duration
    else:
        room_cost = 0
    
    total_amount = service_cost + room_cost
    
    messagebox.showinfo("Total Payment", f"Total Amount for Guest ID {guest_id}: ${total_amount}\nRoom Cost: ${room_cost}\nService Cost: ${service_cost}")
    
# Function to Mark Room as Available After Payment
def mark_room_available():
    guest_id = payment_guest_id_entry.get()
    try:
        cursor.execute("""
            UPDATE Room 
            SET Status = 'Available' 
            WHERE Room_ID IN (
                SELECT Room_ID FROM Booking_Room 
                JOIN Booking ON Booking.Booking_ID = Booking_Room.Booking_ID 
                WHERE Booking.Guest_ID = %s
            );
        """, (guest_id,))
        connection.commit()
        messagebox.showinfo("Success", "Room marked as available successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Database Error: {e}")
        
# Function to Generate Weekly Report
def generate_weekly_report():
    try:
        cursor.execute("""
            SELECT Guest.Guest_ID, Guest.Name, Room.Room_Type, Booking.Check_in_Date, Booking.Check_out_Date, 
                   COALESCE(Payment.Amount_Paid, 0), Room.Status
            FROM Booking 
            JOIN Guest ON Booking.Guest_ID = Guest.Guest_ID
            JOIN Booking_Room ON Booking.Booking_ID = Booking_Room.Booking_ID
            JOIN Room ON Booking_Room.Room_ID = Room.Room_ID
            LEFT JOIN Payment ON Booking.Booking_ID = Payment.Booking_ID
            WHERE Booking.Check_in_Date >= CURRENT_DATE - INTERVAL '7 days';
        """)
        report_data = cursor.fetchall()
        
        if report_data:
            report_text = "Weekly Report:\n\n"
            for idx, row in enumerate(report_data, start=1):
                guest_id, guest_name, room_type, check_in, check_out, amount_paid, room_status = row
                payment_status = "Completed" if room_status == "Available" else "Pending"
                report_text += (f"{idx}. Guest ID: {guest_id}, Guest: {guest_name}, Room: {room_type}, Check-in: {check_in}, "
                                f"Check-out: {check_out}, Payment Status: {payment_status}\n")
            messagebox.showinfo("Weekly Report", report_text)
        else:
            messagebox.showinfo("Weekly Report", "No bookings in the past 7 days.")
    except Exception as e:
        messagebox.showerror("Error", f"Database Error: {e}")

# Function to Generate Monthly Report
def generate_monthly_report():
    try:
        cursor.execute("""
            SELECT Guest.Guest_ID, Guest.Name, Room.Room_Type, Booking.Check_in_Date, Booking.Check_out_Date, 
                   COALESCE(Payment.Amount_Paid, 0), Room.Status
            FROM Booking 
            JOIN Guest ON Booking.Guest_ID = Guest.Guest_ID
            JOIN Booking_Room ON Booking.Booking_ID = Booking_Room.Booking_ID
            JOIN Room ON Booking_Room.Room_ID = Room.Room_ID
            LEFT JOIN Payment ON Booking.Booking_ID = Payment.Booking_ID
            WHERE Booking.Check_in_Date >= CURRENT_DATE - INTERVAL '30 days';
        """)
        report_data = cursor.fetchall()
        
        if report_data:
            report_text = "Monthly Report:\n\n"
            for idx, row in enumerate(report_data, start=1):
                guest_id, guest_name, room_type, check_in, check_out, amount_paid, room_status = row
                payment_status = "Completed" if room_status == "Available" else "Pending"
                report_text += (f"{idx}. Guest ID: {guest_id}, Guest: {guest_name}, Room: {room_type}, Check-in: {check_in}, "
                                f"Check-out: {check_out}, Payment Status: {payment_status}\n")
            messagebox.showinfo("Monthly Report", report_text)
        else:
            messagebox.showinfo("Monthly Report", "No bookings in the past 30 days.")
    except Exception as e:
        messagebox.showerror("Error", f"Database Error: {e}")

# Function to Add Room
def add_room():
    room_type = room_type_entry.get()
    price = room_price_entry.get()
    status = room_status_entry.get()
    
    if not room_type or not price or not status:
        messagebox.showerror("Error", "All fields are required!")
        return
    
    try:
        cursor.execute("INSERT INTO Room (Room_Type, Price, Status) VALUES (%s, %s, %s);", (room_type, price, status))
        connection.commit()
        messagebox.showinfo("Success", "Room added successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Database Error: {e}")

# Function to Remove Room
def remove_room():
    room_id = room_id_entry.get()
    
    if not room_id:
        messagebox.showerror("Error", "Room ID is required!")
        return
    
    try:
        cursor.execute("DELETE FROM Room WHERE Room_ID = %s;", (room_id,))
        connection.commit()
        messagebox.showinfo("Success", "Room removed successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Database Error: {e}")

# First Login Page (General Access)
login_frame = Frame(root, bg='#ffd580')
login_frame.place(x=0, y=0, relheight=1, relwidth=1)
Label(login_frame, text='Login Page', font=("Arial", 16)).pack(pady=10)
Label(login_frame, text="Username").pack()
username_entry = Entry(login_frame)
username_entry.pack()
Label(login_frame, text="Password").pack()
password_entry = Entry(login_frame, show="*")
password_entry.pack()
Button(login_frame, text='Login', command=validate_login).pack()


# Dashboard Frame
dashboard_frame = Frame(root, bg='#add8e6')
dashboard_frame.place(x=0, y=0, relheight=1, relwidth=1)

Label(dashboard_frame, text='Dashboard', font=("Arial", 16)).pack(pady=10)
Button(dashboard_frame, text='Check Room Availability', command=check_room_availability).pack(pady=5)
Button(dashboard_frame, text='Add Guest', command=lambda: guest_frame.lift()).pack(pady=5)
Button(dashboard_frame, text='Extra Services', command=lambda: service_frame.lift()).pack(pady=5)
Button(dashboard_frame, text='Process Payment', command=lambda: payment_frame.lift()).pack(pady=5)
Button(dashboard_frame, text='Reports (Manager Login)', command=lambda: manager_login_frame.lift()).pack(pady=5)



# Guest Frame
guest_frame = Frame(root, bg='#FFD580')
guest_frame.place(x=0, y=0, relheight=1, relwidth=1)

Label(guest_frame, text='Guest Registration', font=("Arial", 16), bg='#FFD580').pack(pady=10)
Label(guest_frame, text='Guest Name').pack()
guest_name_entry = Entry(guest_frame)
guest_name_entry.pack()

Label(guest_frame, text='Contact Number').pack()
guest_contact_entry = Entry(guest_frame)
guest_contact_entry.pack()

Label(guest_frame, text='Address').pack()
guest_address_entry = Entry(guest_frame)
guest_address_entry.pack()

Label(guest_frame, text='Email').pack()
guest_email_entry = Entry(guest_frame)
guest_email_entry.pack()

Label(guest_frame, text='Stay Duration (Days)').pack()
guest_days_entry = Entry(guest_frame)
guest_days_entry.pack()

Label(guest_frame, text='Select Room').pack()
room_var = StringVar()
room_dict = {}  # Define the dictionary here
room_dropdown = ttk.Combobox(guest_frame, textvariable=room_var)
room_dropdown.pack()
update_room_dropdown()  # Ensure dropdown updates dynamically




# Now we can safely update the dropdown
update_room_dropdown()

Button(guest_frame, text='Add Guest', command=add_guest, bg='#4CAF50', fg='white').pack(pady=10)
Button(guest_frame, text='Back', command=lambda: dashboard_frame.lift()).pack()

# Extra Services Frame
service_frame = Frame(root, bg='#E6E6FA')
service_frame.place(x=0, y=0, relheight=1, relwidth=1)

Label(service_frame, text='Assign Extra Services', font=("Arial", 16), bg='#E6E6FA').pack(pady=10)
Label(service_frame, text='Guest ID').pack()
service_guest_id_entry = Entry(service_frame)
service_guest_id_entry.pack()

Label(service_frame, text='Service').pack()
service_name_var = StringVar()
service_dropdown = ttk.Combobox(service_frame, textvariable=service_name_var, values=list(service_dict.keys()))
service_dropdown.pack()

Label(service_frame, text='Quantity').pack()
service_quantity_entry = Entry(service_frame)
service_quantity_entry.pack()

Button(service_frame, text='Add Service', command=add_service, bg='#4CAF50', fg='white').pack(pady=10)
Button(service_frame, text='Back', command=lambda: dashboard_frame.lift()).pack()

# Payment Frame
payment_frame = Frame(root, bg='#D3D3D3')
payment_frame.place(x=0, y=0, relheight=1, relwidth=1)

Label(payment_frame, text='Process Payment', font=("Arial", 16), bg='#D3D3D3').pack(pady=10)
Label(payment_frame, text='Guest ID').pack()
payment_guest_id_entry = Entry(payment_frame)
payment_guest_id_entry.pack()

Button(payment_frame, text='Calculate Total Payment', command=process_payment, bg='#4CAF50', fg='white').pack(pady=10)
Button(payment_frame, text='Payment Successfully', command=mark_room_available, bg='#008CBA', fg='white').pack(pady=10)
Button(payment_frame, text='Back', command=lambda: dashboard_frame.lift()).pack()

# Manager Login Frame
manager_login_frame = Frame(root, bg='#D3D3D3')
manager_login_frame.place(x=0, y=0, relheight=1, relwidth=1)
Label(manager_login_frame, text='Manager Login', font=("Arial", 16)).pack(pady=10)
Label(manager_login_frame, text="Username").pack()
manager_username_entry = Entry(manager_login_frame)
manager_username_entry.pack()
Label(manager_login_frame, text="Password").pack()
manager_password_entry = Entry(manager_login_frame, show="*")
manager_password_entry.pack()
Button(manager_login_frame, text='Login', command=validate_manager_login).pack()
Button(manager_login_frame, text='Back', command=lambda: dashboard_frame.lift()).pack()

# Report Frame (Accessible Only to Managers)
report_frame = Frame(root, bg='#C0C0C0')
report_frame.place(x=0, y=0, relheight=1, relwidth=1)
Label(report_frame, text='Manager Reports', font=("Arial", 16)).pack(pady=10)
Button(report_frame, text='Generate Weekly Report', command=generate_weekly_report).pack(pady=5)
Button(report_frame, text='Generate Monthly Report', command=generate_monthly_report).pack(pady=5)
Button(report_frame, text='Add Room', command=lambda: add_room_frame.lift()).pack(pady=5)
Button(report_frame, text='Edit Room', command=lambda: edit_room_frame.lift()).pack(pady=5)
Button(report_frame, text='Back', command=lambda: dashboard_frame.lift()).pack()

# Add Room Frame
add_room_frame = Frame(root, bg='#E6E6FA')
add_room_frame.place(x=0, y=0, relheight=1, relwidth=1)
Label(add_room_frame, text='Add New Room', font=("Arial", 16)).pack(pady=10)
Label(add_room_frame, text='Room Type').pack()
room_type_entry = Entry(add_room_frame)
room_type_entry.pack()
Label(add_room_frame, text='Price').pack()
room_price_entry = Entry(add_room_frame)
room_price_entry.pack()
Label(add_room_frame, text='Status').pack()
room_status_entry = Entry(add_room_frame)
room_status_entry.pack()
Button(add_room_frame, text='Add Room', command=add_room).pack(pady=10)
Button(add_room_frame, text='Back', command=lambda: report_frame.lift()).pack()

# Edit Room Frame
edit_room_frame = Frame(root, bg='#FFCCCB')
edit_room_frame.place(x=0, y=0, relheight=1, relwidth=1)
Label(edit_room_frame, text='Remove Room', font=("Arial", 16)).pack(pady=10)
Label(edit_room_frame, text='Room ID').pack()
room_id_entry = Entry(edit_room_frame)
room_id_entry.pack()
Button(edit_room_frame, text='Remove Room', command=remove_room).pack(pady=10)
Button(edit_room_frame, text='Back', command=lambda: report_frame.lift()).pack()


login_frame.lift()
root.mainloop()