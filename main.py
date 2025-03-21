import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from PIL import Image, ImageTk

# Database connection
def connect_db():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='***************',
            database='waste_marketplace'
        )
        return conn
    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", str(e))
        return None

conn = connect_db()
cursor = conn.cursor() if conn else None

# Function to handle login
def login_user():
    global logged_in_user
    username = entry_username.get()
    password = entry_password.get()
    role = role_var.get()

    if not username or not password:
        messagebox.showerror("Error", "Please fill in all fields!")
        return

    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role=%s", (username, password, role))
    user = cursor.fetchone()

    if user:
        logged_in_user = user
        messagebox.showinfo("Success", "Login Successful!")
        if role == 'buyer':
            open_buyer_dashboard()
        elif role == 'seller':
            open_seller_dashboard()
    else:
        messagebox.showerror("Error", "Invalid credentials!")

# Function to handle sign-up
def signup_user():
    username = entry_username.get()
    password = entry_password.get()
    role = role_var.get()

    if not username or not password:
        messagebox.showerror("Error", "Please fill in all fields!")
        return

    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
        conn.commit()
        messagebox.showinfo("Success", "Registration Successful! Please log in.")
        switch_to_login()
    except mysql.connector.Error as e:
        if e.errno == 1062:  # Duplicate entry error code
            messagebox.showerror("Error", "Username already exists!")
        else:
            messagebox.showerror("Error", str(e))

# Function to switch to sign-up mode
def switch_to_signup():
    btn_action.config(text="Sign Up", command=signup_user)
    switch_label.config(text="Already have an account? Login")
    switch_button.config(text="Login", command=switch_to_login)

# Function to switch to login mode
def switch_to_login():
    btn_action.config(text="Login", command=login_user)
    switch_label.config(text="Don't have an account? Sign Up")
    switch_button.config(text="Sign Up", command=switch_to_signup)

# Function to open buyer dashboard
def open_buyer_dashboard():
    buyer_window = tk.Toplevel(window)
    buyer_window.title("Buyer Dashboard")
    buyer_window.geometry("800x500")

    tk.Label(buyer_window, text="Available Products", font=("Arial", 18, "bold")).pack(pady=20)

    # List available products
    cursor.execute("SELECT product_id, product_name, price, quantity FROM products WHERE quantity > 0")
    products = cursor.fetchall()

    product_list = tk.Listbox(buyer_window, width=50)
    for product in products:
        product_list.insert(tk.END, f"{product[0]} - {product[1]} - ${product[2]} - {product[3]} available")
    product_list.pack(pady=10)

    tk.Label(buyer_window, text="Select Product ID and Quantity to Buy", font=("Arial", 12)).pack(pady=5)
    entry_product_id = tk.Entry(buyer_window)
    entry_product_id.pack(pady=5)
    entry_quantity = tk.Entry(buyer_window)
    entry_quantity.pack(pady=5)

    def place_order():
        product_id = entry_product_id.get()
        quantity = int(entry_quantity.get())
        cursor.execute("SELECT price, quantity FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        if product and quantity <= product[1]:
            total_price = product[0] * quantity
            try:
                cursor.execute("INSERT INTO orders (buyer_id, product_id, quantity, total_price) VALUES (%s, %s, %s, %s)",
                               (logged_in_user[0], product_id, quantity, total_price))
                conn.commit()
                messagebox.showinfo("Success", "Order placed successfully!")
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))
        else:
            messagebox.showerror("Error", "Invalid product or quantity")

    tk.Button(buyer_window, text="Place Order", command=place_order).pack(pady=10)

# Function to open seller dashboard
def open_seller_dashboard():
    seller_window = tk.Toplevel(window)
    seller_window.title("Seller Dashboard")
    seller_window.geometry("800x500")

    tk.Label(seller_window, text="Add Product", font=("Arial", 18, "bold")).pack(pady=20)

    # Fields for adding a new product
    tk.Label(seller_window, text="Product Name").pack(pady=5)
    product_name = tk.Entry(seller_window)
    product_name.pack(pady=5)

    tk.Label(seller_window, text="Description").pack(pady=5)
    product_description = tk.Entry(seller_window)
    product_description.pack(pady=5)

    tk.Label(seller_window, text="Price").pack(pady=5)
    price = tk.Entry(seller_window)
    price.pack(pady=5)

    tk.Label(seller_window, text="Quantity").pack(pady=5)
    quantity = tk.Entry(seller_window)
    quantity.pack(pady=5)

    def add_product():
        pname = product_name.get()
        pdesc = product_description.get()
        pprice = price.get()
        pqty = quantity.get()

        if not pname or not pdesc or not pprice or not pqty:
            messagebox.showerror("Error", "Please fill in all fields!")
            return

        try:
            cursor.execute("INSERT INTO products (seller_id, product_name, product_description, price, quantity) VALUES (%s, %s, %s, %s, %s)", 
                           (logged_in_user[0], pname, pdesc, pprice, pqty))
            conn.commit()
            messagebox.showinfo("Success", "Product added successfully!")
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))

    tk.Button(seller_window, text="Add Product", command=add_product).pack(pady=20)

    # Display existing orders
    tk.Label(seller_window, text="Your Orders", font=("Arial", 18, "bold")).pack(pady=20)
    cursor.execute("SELECT orders.order_id, products.product_name, orders.quantity, orders.total_price, orders.status "
                   "FROM orders JOIN products ON orders.product_id = products.product_id "
                   "WHERE products.seller_id = %s", (logged_in_user[0],))
    orders = cursor.fetchall()

    for order in orders:
        tk.Label(seller_window, text=f"Order {order[0]}: {order[1]} - {order[2]} pcs - ${order[3]} - Status: {order[4]}").pack()

# Main window configuration
window = tk.Tk()
window.title("Waste Products Marketplace")
window.geometry("800x500")
window.configure(bg="#f5f5f5")

# Left Panel
left_frame = tk.Frame(window, bg="#3366ff", width=300)
left_frame.pack(side="left", fill="y")

tk.Label(left_frame, text="Welcome to Waste Marketplace", font=("Arial", 18, "bold"), bg="#3366ff", fg="white").place(x=20, y=50)
tk.Label(left_frame, text="Buy & Sell Waste Products Easily", font=("Arial", 14), bg="#3366ff", fg="white").place(x=20, y=100)
tk.Label(left_frame, text="Join us today to make a difference!", font=("Arial", 12), bg="#3366ff", fg="white").place(x=20, y=150)

# Right Panel
right_frame = tk.Frame(window, bg="#f5f5f5")
right_frame.pack(side="right", expand=True, fill="both", padx=40, pady=40)

tk.Label(right_frame, text="Enter the Details", font=("Arial", 18, "bold"), bg="#f5f5f5").pack(pady=20)

# Username Entry
entry_username = tk.Entry(right_frame, font=("Arial", 14))
entry_username.insert(0, "Username")
entry_username.pack(pady=10, ipadx=20, ipady=8)

# Password Entry
entry_password = tk.Entry(right_frame, font=("Arial", 14), show="*")
entry_password.insert(0, "Password")
entry_password.pack(pady=10, ipadx=20, ipady=8)

# Role Selection
role_var = tk.StringVar(value="buyer")
tk.Label(right_frame, text="Role:", font=("Arial", 12), bg="#f5f5f5").pack(anchor="w", pady=5)
ttk.Radiobutton(right_frame, text="Buyer", variable=role_var, value="buyer").pack(anchor="w")
ttk.Radiobutton(right_frame, text="Seller", variable=role_var, value="seller").pack(anchor="w")

# Action Button (Login/Sign Up)
btn_action = tk.Button(right_frame, text="Login", command=login_user, font=("Arial", 14), bg="#007bff", fg="white")
btn_action.pack(pady=20, ipadx=20, ipady=10)

# Switch between Login and Sign-Up
switch_label = tk.Label(right_frame, text="Don't have an account? Sign Up", bg="#f5f5f5", font=("Arial", 12))
switch_label.pack()
switch_button = tk.Button(right_frame, text="Sign Up", command=switch_to_signup, font=("Arial", 12), bg="#ffcc00")
switch_button.pack()

# Run the main loop
window.mainloop()

if conn:
    conn.close()
