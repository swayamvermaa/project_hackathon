import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from PIL import Image, ImageTk
import bcrypt

# Constants
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'vermaswayam@225346',
    'database': 'waste_marketplace'
}
PRIMARY_COLOR = "#1abc9c"  # Turquoise
SECONDARY_COLOR = "#ecf0f1"  # Light Grey
BTN_PRIMARY_COLOR = "#e74c3c"  # Alizarin Red
BTN_SECONDARY_COLOR = "#3498db"  # Peter River
FONT_LARGE = ("Arial", 18, "bold")
FONT_MEDIUM = ("Arial", 14)
FONT_SMALL = ("Arial", 12)
HIGHLIGHT_COLOR = "#f39c12"  # Yellow
TEXT_COLOR = "#2c3e50"  # Dark Grey

# Constants for text messages
WELCOME_MESSAGE = "Welcome to Waste Marketplace!"
TAGLINE = "Connecting Buyers & Sellers of Reusable Materials"
INSTRUCTIONS = "Sign in to your account or register as a new user to get started!"
LOGIN_PROMPT = "Login to access the best deals on reusable products."
SIGNUP_PROMPT = "Create a new account to buy and sell waste products effortlessly."
ENTER_DETAILS = "Please Enter Your Details Below"

# Database Connection
def connect_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", str(e))
        return None

conn = connect_db()
cursor = conn.cursor() if conn else None

# Hashing Passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# Login and Signup Functions
def login_user():
    global logged_in_user
    username, password, role = entry_username.get(), entry_password.get(), role_var.get()

    if not username or not password:
        messagebox.showerror("Error", "Please fill in all fields!")
        return

    cursor.execute(
        "SELECT * FROM users WHERE username=%s AND role=%s", 
        (username, role)
    )
    user = cursor.fetchone()

    if user and check_password(password, user[2].encode('utf-8')):  # Assuming password is in the third column
        logged_in_user = user
        messagebox.showinfo("Success", "Login Successful!")
        open_buyer_dashboard() if role == 'buyer' else open_seller_dashboard()
    else:
        messagebox.showerror("Error", "Invalid credentials!")

def signup_user():
    username, password, role = entry_username.get(), entry_password.get(), role_var.get()

    if not username or not password:
        messagebox.showerror("Error", "Please fill in all fields!")
        return

    hashed_password = hash_password(password)

    try:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
            (username, hashed_password, role)
        )
        conn.commit()
        messagebox.showinfo("Success", "Registration Successful! Please log in.")
        switch_to_login()
    except mysql.connector.Error as e:
        messagebox.showerror("Error", "Username already exists!" if e.errno == 1062 else str(e))


def switch_to_signup():
    btn_action.config(text="Sign Up", command=signup_user)
    switch_label.config(text="Already have an account? Login")
    switch_button.config(text="Login", command=switch_to_login)

def switch_to_login():
    btn_action.config(text="Login", command=login_user)
    switch_label.config(text="Don't have an account? Sign Up")
    switch_button.config(text="Sign Up", command=switch_to_signup)

# Dashboard Functions
def open_buyer_dashboard():
    buyer_window = create_window("Buyer Dashboard")
    display_product_list(buyer_window)
    setup_order_section(buyer_window)

def open_seller_dashboard():
    seller_window = create_window("Seller Dashboard")
    setup_add_product_section(seller_window)
    display_orders_section(seller_window)

# Buyer Dashboard Functions
def display_product_list(window):
    tk.Label(window, text="Available Products", font=FONT_LARGE).pack(pady=20)
    product_list = tk.Listbox(window, width=50)

    cursor.execute("SELECT product_id, product_name, price, quantity FROM products WHERE quantity > 0")
    for product in cursor.fetchall():
        product_list.insert(tk.END, f"{product[0]} - {product[1]} - ${product[2]} - {product[3]} available")

    product_list.pack(pady=10)

def setup_order_section(window):
    tk.Label(window, text="Select Product ID and Quantity to Buy", font=FONT_SMALL).pack(pady=5)
    entry_product_id = tk.Entry(window)
    entry_quantity = tk.Entry(window)

    entry_product_id.pack(pady=5)
    entry_quantity.pack(pady=5)

    def place_order():
        product_id, quantity = entry_product_id.get(), int(entry_quantity.get())
        cursor.execute("SELECT price, quantity FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        if product and quantity <= product[1]:
            try:
                cursor.execute(
                    "INSERT INTO orders (buyer_id, product_id, quantity, total_price) VALUES (%s, %s, %s, %s)",
                    (logged_in_user[0], product_id, quantity, product[0] * quantity)
                )
                conn.commit()
                messagebox.showinfo("Success", "Order placed successfully!")
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))
        else:
            messagebox.showerror("Error", "Invalid product or quantity")

    tk.Button(window, text="Place Order", command=place_order).pack(pady=10)

# Seller Dashboard Functions
def setup_add_product_section(window):
    tk.Label(window, text="Add Product", font=FONT_LARGE).pack(pady=20)
    fields = {"Product Name": None, "Description": None, "Price": None, "Quantity": None}
    for label, entry in fields.items():
        tk.Label(window, text=label).pack(pady=5)
        fields[label] = tk.Entry(window)
        fields[label].pack(pady=5)

    def add_product():
        values = [fields[label].get() for label in fields]
        if not all(values):
            messagebox.showerror("Error", "Please fill in all fields!")
            return
        try:
            cursor.execute(
                "INSERT INTO products (seller_id, product_name, product_description, price, quantity) VALUES (%s, %s, %s, %s, %s)", 
                (logged_in_user[0], *values)
            )
            conn.commit()
            messagebox.showinfo("Success", "Product added successfully!")
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))

    tk.Button(window, text="Add Product", command=add_product).pack(pady=20)

def display_orders_section(window):
    tk.Label(window, text="Your Orders", font=FONT_LARGE).pack(pady=20)
    cursor.execute(
        "SELECT orders.order_id, products.product_name, orders.quantity, orders.total_price, orders.status "
        "FROM orders JOIN products ON orders.product_id = products.product_id "
        "WHERE products.seller_id = %s", (logged_in_user[0],)
    )
    for order in cursor.fetchall():
        tk.Label(window, text=f"Order {order[0]}: {order[1]} - {order[2]} pcs - ${order[3]} - Status: {order[4]}").pack()

# Helper Functions
def create_window(title):
    window = tk.Toplevel()
    window.title(title)
    window.geometry("800x500")
    window.resizable(True, True)  # Make window resizable
    return window

# Placeholder handling functions
def on_username_focus_in(event):
    if entry_username.get() == "Enter your email":
        entry_username.delete(0, tk.END)
        entry_username.config(fg="black")

def on_username_focus_out(event):
    if entry_username.get() == "":
        entry_username.insert(0, "Enter your email")
        entry_username.config(fg="grey")

def on_password_focus_in(event):
    if entry_password.get() == "Password":
        entry_password.delete(0, tk.END)
        entry_password.config(show="*", fg="black")

def on_password_focus_out(event):
    if entry_password.get() == "":
        entry_password.insert(0, "Password")
        entry_password.config(show="", fg="grey")

# Main Window Setup
window = tk.Tk()
window.title("Waste Products Marketplace")
window.geometry("1000x600")
window.configure(bg=SECONDARY_COLOR)

# Layout - Left Panel with Attractive Text
left_frame = tk.Frame(window, bg=PRIMARY_COLOR, width=350, padx=30, pady=40)
left_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")

tk.Label(left_frame, text=WELCOME_MESSAGE, font=FONT_LARGE, bg=PRIMARY_COLOR, fg="white").grid(row=0, column=0, pady=20)
tk.Label(left_frame, text=TAGLINE, font=FONT_SMALL, bg=PRIMARY_COLOR, fg="white", wraplength=280).grid(row=1, column=0, pady=10)
tk.Label(left_frame, text=INSTRUCTIONS, font=FONT_SMALL, bg=PRIMARY_COLOR, fg="white", wraplength=280).grid(row=2, column=0, pady=20)

# Layout - Right Panel with Attractive Text and Forms
right_frame = tk.Frame(window, bg=SECONDARY_COLOR, padx=40, pady=40)
right_frame.grid(row=0, column=1, rowspan=2, sticky="nsew")

tk.Label(right_frame, text=ENTER_DETAILS, font=FONT_LARGE, bg=SECONDARY_COLOR, fg=HIGHLIGHT_COLOR).pack(pady=20)
entry_username = tk.Entry(right_frame, font=FONT_MEDIUM, fg="grey")
entry_password = tk.Entry(right_frame, font=FONT_MEDIUM, fg="grey", show="")

entry_username.insert(0, "Enter your email")
entry_password.insert(0, "Password")

entry_username.bind("<FocusIn>", on_username_focus_in)
entry_username.bind("<FocusOut>", on_username_focus_out)
entry_password.bind("<FocusIn>", on_password_focus_in)
entry_password.bind("<FocusOut>", on_password_focus_out)

entry_username.pack(pady=10, ipadx=20, ipady=8, fill="x")
entry_password.pack(pady=10, ipadx=20, ipady=8, fill="x")

# Role Selection
role_var = tk.StringVar(value="buyer")
tk.Label(right_frame, text="Role:", font=FONT_SMALL, bg=SECONDARY_COLOR, fg=TEXT_COLOR).pack(anchor="w", pady=5)
ttk.Radiobutton(right_frame, text="Buyer", variable=role_var, value="buyer", style="TRadiobutton").pack(anchor="w")
ttk.Radiobutton(right_frame, text="Seller", variable=role_var, value="seller", style="TRadiobutton").pack(anchor="w")

# Login/Signup Action Button
btn_action = tk.Button(right_frame, text="Login", command=login_user, font=FONT_MEDIUM, bg=BTN_PRIMARY_COLOR, fg="white")
btn_action.pack(pady=20, ipadx=20, ipady=10)

# Switch between Login and Signup with Informative Text
switch_label = tk.Label(right_frame, text=LOGIN_PROMPT, bg=SECONDARY_COLOR, font=FONT_SMALL, fg=TEXT_COLOR)
switch_button = tk.Button(right_frame, text="Sign Up", command=switch_to_signup, font=FONT_SMALL, bg=BTN_SECONDARY_COLOR, fg="white")
switch_label.pack()
switch_button.pack()

window.mainloop()
if conn:
    conn.close()