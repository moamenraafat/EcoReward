import datetime
import time

all_transactions = []

def process_transaction(user, machine, material_inserted):
  """
  ال user دي عباره عن بيانات المستخدم هتتخزن في لست 
  ال machine دي عباره عن بيانات الماكين هتتخزن في لست 
  ال material_inserted دي عباره عن المادة المدخلة في الماكينه بنوعها و القيمه المقابله ليها هتتخزن في لست 
  """
transaction_id = f"TXN-{len(all_transactions) + 1001}"
current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")



