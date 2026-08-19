import datetime
import time

# قائمة عامة لحفظ كل المعاملات اللي بتحصل في السيستم
all_transactions = []

def process_transaction(user, machine, material_inserted):
 """
 user: قاموس فيه بيانات المستخدم الحالي 
    machine: قاموس فيه بيانات الماكينة 
    materials_inserted: قائمة بالمواد اللي اترمت 
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
