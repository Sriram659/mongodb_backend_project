from pymongo import MongoClient
from dotenv import load_dotenv
import pandas as pd
from pathlib import Path
import openpyxl
import os

# MongoDB connection
repo_root = Path(__file__).parent
dotenv_path = repo_root / ".env"
load_dotenv(dotenv_path)
connection_string = os.getenv("MONGO_URI")
print("Loaded MONGO_URI:", os.getenv("MONGO_URI"))
client = MongoClient(connection_string)
db = client["mini_marche"]
collection = db["inventory"]

# Import from Excel
def read_excel_inventory(filename="inventory.xlsx"):
    print(f"Reading from: {filename}")
    df = pd.read_excel(filename)
    records = df.to_dict(orient="records")
    return records

# Insert to DB    
def insert_data_to_db(records):
    if records:
        for record in records:
            collection.update_one(
                {
                    "brand": record["brand"],
                    "type": record["type"],
                    "volume": record["volume"],
                    "category": record["category"]
                },
                {"$set": record},
                upsert=True
            )
        print("Data inserted/updated successfully.")
    else:
        print("No records to insert.")

# Low Stock Query and filtering
def get_low_stock_products(threshold=10, filter_type=None, filter_brand=None, filter_category=None):
    query = {"stock": {"$lt": threshold}}

    if filter_type:
        query["type"] = {"$regex": f"^{filter_type}$", "$options": "i"}
    if filter_brand:
        query["brand"] = {"$regex": f"^{filter_brand}$", "$options": "i"}
    if filter_category:
        query["category"] = {"$regex": f"^{filter_category}$", "$options": "i"}
        
    results = collection.find(query)
    return list(results)

# Export low stock to Excel (overwrite if exists)
def export_low_stock_to_excel(filename="low_stock.xlsx", threshold=10):
    low_stock = get_low_stock_products(threshold)

    if not low_stock:
        print("No low stock items to export.")
        return

    df = pd.DataFrame(low_stock)
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])  
    df.to_excel(filename, index=False)
    print(f"Exported low stock items to '{filename}'.")

# --- Main Menu ---
if __name__ == "__main__": 
    # Check if running in GitHub Actions (non-interactive environment)
    if os.getenv('GITHUB_ACTIONS') == 'true':
        print("Running in GitHub Actions - executing automated tasks...")
        
        # Option 1: Import data from Excel to DB
        print("1. Importing data from Excel...")
        records = read_excel_inventory("inventory.xlsx")
        insert_data_to_db(records)
        
        # Option 2: Show low stock products (without filters)
        print("2. Checking low stock products...")
        low_stock_items = get_low_stock_products(threshold=10)
        
        if not low_stock_items:
            print("No low stock items found.")
        else:
            print(f"\nFound {len(low_stock_items)} low stock products:")
            for item in low_stock_items:
                print(f"- {item['brand']} ({item['type']}), Volume: {item['volume']}, Stock: {item['stock']}, Category: {item['category']}")
        
        # Option 3: Export low stock to Excel
        print("3. Exporting low stock products to Excel...")
        export_low_stock_to_excel()
        
        print("GitHub Actions tasks completed successfully!")
        
    else:
        # Interactive mode for local development
        while True:
            print("1. Import data from excel to db")
            print("2. Show low stock products (with optional type/brand/category filters)")
            print("3. Export low stock products to Excel")
            print("4. Exit")

            choice = input("Choose an option: ")

            if choice == '1':
                records = read_excel_inventory("inventory.xlsx")
                insert_data_to_db(records)
                
            elif choice == '2':
                filter_type = input("Enter product type (or press Enter to skip): ").strip() or None
                filter_brand = input("Enter brand (or press Enter to skip): ").strip() or None
                filter_category = input("Enter category (or press Enter to skip): ").strip() or None

                low_stock_items = get_low_stock_products(
                    threshold=10,
                    filter_type=filter_type,
                    filter_brand=filter_brand,
                    filter_category=filter_category
                )

                if not low_stock_items:
                    print("No matching low stock items.")
                else:
                    print("\nLow Stock Products:")
                    for item in low_stock_items:
                        print(f"- {item['brand']} ({item['type']}), Volume: {item['volume']}, Stock: {item['stock']}, Category: {item['category']}")
            
            elif choice == '3':
                export_low_stock_to_excel()

            elif choice == '4':
                print("Exiting program.")
                break

            else:
                print("Invalid option. Please try again.")