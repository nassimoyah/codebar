import tkinter as tk 
from tkinter import messagebox
import cv2
from pyzbar.pyzbar import decode
import pygame
import time
import threading
import sys
import json
from concurrent.futures import ThreadPoolExecutor

# Global variables
discount_percentage = 100
ITEMS_FILE = "items.json"  # File to store items
items = {}
price = 0
window_open = False
executor = ThreadPoolExecutor(max_workers=2)  # Thread pool for managing GUI windows
camera_index = 0  # Default to camera 0
cap = None  # To hold the camera object

# Initialize audio
pygame.mixer.init()
pygame.mixer.music.load("C:\\beep\\beep-02.wav")

def load_items():
    """Load items from a JSON file."""
    global items
    try:
        with open(ITEMS_FILE, "r") as file:
            items = json.load(file)
            # Convert keys back to bytes
            items = {bytes(key, "utf-8"): value for key, value in items.items()}
    except FileNotFoundError:
        # If the file doesn't exist, start with default items
        items = {
          
        }
    except json.JSONDecodeError:
        print("Error decoding JSON. Starting with default items.")
        items = {}

def save_items():
    """Save items to a JSON file."""
    # Convert byte keys to strings for JSON serialization
    serializable_items = {key.decode("utf-8"): value for key, value in items.items()}
    with open(ITEMS_FILE, "w") as file:
        json.dump(serializable_items, file, indent=4)

def set_camera(index):
    global camera_index, cap
    camera_index = index
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        messagebox.showerror("Camera Error", f"Failed to open camera {camera_index}")
        sys.exit(1)

    camera_selection_window.destroy()  # Close the camera selection window
    start_camera_feed()  # Start camera feed

def choose_camera():
    global camera_selection_window
    camera_selection_window = tk.Tk()
    camera_selection_window.title("Select Camera")
    camera_selection_window.geometry("300x150")

    tk.Label(camera_selection_window, text="Select the camera to use:").pack(pady=10)

    button_cam0 = tk.Button(camera_selection_window, text="Camera 0", command=lambda: set_camera(0))
    button_cam0.pack(pady=5)

    button_cam1 = tk.Button(camera_selection_window, text="Camera 1", command=lambda: set_camera(1))
    button_cam1.pack(pady=5)

    camera_selection_window.mainloop()

def start_camera_feed():
    global cap
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        detected_barcodes = decode(frame)

        cv2.putText(frame, f"Total: {price:.2f}", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255), 2)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c') and is_debounced():
            executor.submit(open_calculator)
        elif key == ord('f') and is_debounced():
            executor.submit(open_window)

        if detected_barcodes:
            for barcode in detected_barcodes:
                if barcode.data:
                    process_barcode(barcode.data)
                    if not pygame.mixer.music.get_busy():
                        pygame.mixer.music.play()
                    time.sleep(1.5)

        cv2.imshow('Scanner', frame)

    cap.release()
    cv2.destroyAllWindows()

def open_window():
    global window_open
    if window_open:
        return
    window_open = True

    def on_close():
        global window_open
        window_open = False
        root.destroy()

    def update_price(percentage):
        payable_price = price * (percentage / 100)
        result_label.config(text=f"Price to pay: {payable_price:.2f}")

    def reset_client():
        global price
        price = 0
        result_label.config(text=f"Total Price: {price:.2f}")

    root = tk.Tk()
    root.title("Price Calculation")
    root.geometry("350x300")
    root.protocol("WM_DELETE_WINDOW", on_close)

    tk.Label(root, text="Select the percentage to pay:").pack(pady=10)

    for percentage in [10, 15, 20]:
        tk.Button(root, text=f"{percentage}%", command=lambda p=percentage: update_price(p)).pack(pady=5)

    global result_label
    result_label = tk.Label(root, text=f"Total Price: {price:.2f}", font=("Arial", 12, "bold"))
    result_label.pack(pady=20)

    tk.Button(root, text="Finish with Client", command=reset_client).pack(pady=10)

    root.mainloop()

def add_new_item(code):
    global items

    def save_item():
        global price
        name = name_entry.get()
        try:
            item_price = float(price_entry.get())
            items[code] = {"name": name, "price": item_price}
            price += item_price
            save_items()  # Save the updated items to the file
            messagebox.showinfo("Item Added", f"Item '{name}' added with price: {price:.2f}")
            new_item_window.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid price.")

    new_item_window = tk.Tk()
    new_item_window.title("Add New Item")
    new_item_window.geometry("300x200")

    tk.Label(new_item_window, text="Enter Item Name:").pack(pady=5)
    name_entry = tk.Entry(new_item_window)
    name_entry.pack(pady=5)

    tk.Label(new_item_window, text="Enter Item Price:").pack(pady=5)
    price_entry = tk.Entry(new_item_window)
    price_entry.pack(pady=5)

    tk.Button(new_item_window, text="Save Item", command=save_item).pack(pady=10)
    new_item_window.mainloop()

def process_barcode(code):
    global price
    if code in items:
        item = items[code]
        print(f"Item: {item['name']}")
        price += item['price']
    else:
        print(f"Scanned Code: {code}. Item not found.")
        add_new_item(code)

def open_calculator():
    calc_window = tk.Tk()
    calc_window.title("Calculator")
    calc_window.geometry("300x400")

    current_input = tk.StringVar()

    def on_button_click(button_text):
        current_input.set(current_input.get() + button_text)

    def calculate_result():
        try:
            result = eval(current_input.get())
            global price
            price += result
            current_input.set("")
        except Exception:
            messagebox.showerror("Invalid Input", "Error in calculation.")

    def clear_input():
        current_input.set("")

    button_frame = tk.Frame(calc_window)
    button_frame.pack(pady=10)

    buttons = [
        ('7', '8', '9', '+'),
        ('4', '5', '6', '-'),
        ('1', '2', '3', ''),
        ('0', '.', '=', '')
    ]

    for row in buttons:
        row_frame = tk.Frame(button_frame)
        row_frame.pack()
        for button_text in row:
            if button_text:
                button = tk.Button(row_frame, text=button_text, width=5, height=2,
                                   command=lambda text=button_text: on_button_click(text))
                button.pack(side=tk.LEFT)

    tk.Button(calc_window, text="=", width=10, height=2, command=calculate_result).pack(pady=10)
    tk.Button(calc_window, text="Clear", width=10, height=2, command=clear_input).pack(pady=10)

    tk.Label(calc_window, textvariable=current_input, font=("Arial", 16)).pack(pady=20)
    calc_window.mainloop()

last_pressed = time.time()

def is_debounced(interval=0.3):
    global last_pressed
    now = time.time()
    if now - last_pressed > interval:
        last_pressed = now
        return True
    return False

# Load items at the beginning
load_items()

# Run the camera selection window first
choose_camera()
