""" Main
This is the program's starting point. It shows a menu and asks YOU
for input at every step (your name, your email, how many bottles you
recycled...)
"""

from user import register_user, login_user, get_user_summary
from material import setup_default_materials, list_materials, find_material_by_name
from transaction import process_transaction

# A default machine,since we don't have real hardware in this project
current_machine = {"machine_id": "ER-001", "location": "Sadat City University"}

# Keeps track of who is currently logged in (None = nobody logged in yet)
logged_in_user = None

def show_main_menu():
    print("\n===== EcoReward =====")
    print("1. Create account")
    print("2. Log in")
    print("3. Recycle materials (requires login)")
    print("4. View my profile (requires login)")
    print("5. Exit")


def handle_create_account():
    print("\n--- Create account ---")
    name = input("Full name: ")
    email = input("Email: ")
    password = input("Password: ")
    confirm_password = input("Confirm password: ")

    result = register_user(name, email, password, confirm_password)
    print(result["message"])

def handle_login():
    global logged_in_user
    print("\n--- Log in ---")
    email = input("Email: ")
    password = input("Password: ")

    result = login_user(email, password)
    print(result["message"])

    if result["success"]:
        logged_in_user = result["user"]

def handle_recycle():
    print("\n--- Recycle materials ---")
    if logged_in_user is None:
        print("You must log in first.")
        return

    print("Connected to machine:", current_machine["machine_id"])
    print("Available materials:")
    for material in list_materials():
        print(f"  - {material['name']} ({material['points_per_unit']} points each)")

    materials_inserted = []
    while True:
        material_name = input("\nMaterial name (or leave empty to finish): ")
        if material_name == "":
            break

        material = find_material_by_name(material_name)
        if material is None:
            print("This material is not recognized, try again.")
            continue

        quantity_text = input(f"How many {material_name} did you recycle? ")
        if not quantity_text.isdigit():
            print("Please enter a valid number.")
            continue

        quantity = int(quantity_text)
        materials_inserted.append({"material": material, "quantity": quantity})

    if len(materials_inserted) == 0:
        print("No materials entered, session cancelled.")
        return

    transaction = process_transaction(logged_in_user, current_machine, materials_inserted)
    print(f"\nGreat job! You earned {transaction['points_earned']} points.")
    print(f"Your new balance is {logged_in_user['points']} points.")

def handle_view_profile():
    print("\n--- My profile ---")
    if logged_in_user is None:
        print("You must log in first.")
        return

    summary = get_user_summary(logged_in_user)
    print(f"Name: {summary['name']}")
    print(f"Total points: {summary['total_points']}")
    print(f"Total recycling sessions: {summary['total_transactions']}")
    print("Materials recycled:")
    for material_name, quantity in summary["materials_recycled"].items():
        print(f"  - {material_name}: {quantity}")


def main():
    setup_default_materials()

    while True:
        show_main_menu()
        choice = input("Choose an option: ")

        if choice == "1":
            handle_create_account()
        elif choice == "2":
            handle_login()
        elif choice == "3":
            handle_recycle()
        elif choice == "4":
            handle_view_profile()
        elif choice == "5":
            print("Goodbye")
            break
        else:
            print("Invalid option, please choose again.")

    if __name__ == "__main__":
     main()
