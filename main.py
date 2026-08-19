""" Main
This is the program's starting point. It shows a menu and asks YOU
for input at every step (your name, your email, how many bottles you
recycled...)
"""
from datetime import datetime

# قائمة عامة لحفظ كل المعاملات اللي بتحصل في السيستم
all_transactions = []

def process_transaction(user, machine, materials_inserted):
    """
    user: قاموس فيه بيانات المستخدم الحالي (جاهز من زميلك)
    machine: قاموس فيه بيانات الماكينة (جاهز من زميلك)
    materials_inserted: قائمة بالمواد اللي اترمت [{"material": mat_dict, "quantity": 3}]
    """
    
    # 1. توليد Transaction ID وتاريخ العملية
    transaction_id = f"TXN-{len(all_transactions) + 1001}"
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    total_points_earned = 0
    transaction_materials = []

    # 2. حساب النقاط بناءً على كل خامة
    for item in materials_inserted:
        material_data = item["material"]  # قاموس الخامة (Name, Points, Type)
        quantity = item["quantity"]
        
        points = material_data["points_per_unit"] * quantity
        total_points_earned += points
        
        transaction_materials.append({
            "name": material_data["name"],
            "quantity": quantity,
            "points_earned": points
        })

    # 3. تحديث نقاط المستخدم وسجله (User Points & Recycling History)
    user["points"] += total_points_earned

    # 4. بناء هيكل الـ Transaction بالكامل
    transaction = {
        "transaction_id": transaction_id,
        "user_id": user["id"],
        "user_name": user["name"],
        "machine_id": machine["machine_id"],
        "materials": transaction_materials,
        "points_earned": total_points_earned,
        "date": current_date
    }

    # 5. حفظ المعاملة في القائمة العامة وفي سجل المستخدم
    all_transactions.append(transaction)
    user["recycling_history"].append(transaction)

    # إرجاع تفاصيل المعاملة
    return transaction


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




#دة جزء machine  بتاعي يخواتي
machine = {
    "machineID": "M001",
    "location": "cairo mall",
    "Status": "Available",
    "Accepted_materials": ["Plastic", "Glass", "Paper", "Metal"]
}

def display_machine(machine):
    print("==== machine Informations ====")
    print(f"Machine ID: {machine["machineID"]}")
    print(f"Location: {machine["location"]}")
    print(f"Status: {machine["Status"]}")    
    print(f"Accepted Materials: {machine["Accepted_materials"]}")

def isAvailable(machine):
    if machine["Status"] == "Available":
        return True
    else:
        return False        

def check_material(machine, material):
    if material in machine["Accepted_material"]:
        print(f"{material} is accepted.")
        return True
    else:
        print(f"{material} is not accepted")
        return False

def change_status(machine, new_status):
     machine["Status"] = new_status 
     print(f"machine status changed to {new_status}")  




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
