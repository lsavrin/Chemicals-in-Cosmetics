# -*- coding: utf-8 -*-
"""
Created on Sat Apr  5 23:04:57 2025

@author: lsav1
"""
import pandas as pd
import pyodbc

# === Load and Clean CSV ===
df = pd.read_csv("C:/Users/lsav1/OneDrive/Desktop/chemicals_cleaned.csv")
df.columns = df.columns.str.strip()

for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].astype(str).str.strip()

date_cols = ['InitialDateReported', 'MostRecentDateReported', 'DiscontinuedDate',
             'ChemicalCreatedAt', 'ChemicalUpdatedAt', 'ChemicalDateRemoved']
for col in date_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')   
        
# === Connect to SQL Server ===
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

# === Load COMPANY ===
for _, row in df.iterrows():
    try:
        company_id_number = str(row['CompanyId']).strip()
        company_name = str(row['CompanyName']).strip()
        if not company_id_number or not company_name:
            continue
        cursor.execute("SELECT company_id FROM company WHERE company_id_number = ?", company_id_number)
        if not cursor.fetchone():
            cursor.execute("INSERT INTO company (company_name, company_id_number) VALUES (?, ?)", company_name, company_id_number)
    except Exception as e:
        print(f"Error inserting company: {e}")

print("Companies loaded")
conn.commit()
cursor.close()
conn.close()

# === Load BRAND ===
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

for _, row in df.iterrows():
    try:
        brand_name = str(row['BrandName']).strip()
        company_id_number = str(row['CompanyId']).strip()
        if not brand_name or not company_id_number:
            continue
        cursor.execute("SELECT company_id FROM company WHERE company_id_number = ?", company_id_number)
        company = cursor.fetchone()
        if not company:
            continue
        cursor.execute("SELECT brand_id FROM brand WHERE brand_name = ?", brand_name)
        if not cursor.fetchone():
            cursor.execute("INSERT INTO brand (brand_name, company_id) VALUES (?, ?)", brand_name, company[0])
    except Exception as e:
        print(f"Error inserting brand: {e}")

print("Brands loaded")
conn.commit()
cursor.close()
conn.close()

# === Load CATEGORY ===
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

for _, row in df.iterrows():
    try:
        cat_id = str(row['PrimaryCategoryId']).strip()
        cat_name = str(row['PrimaryCategory']).strip()
        if not cat_id or not cat_name:
            continue
        cursor.execute("SELECT category_id FROM category WHERE category_id_number = ?", cat_id)
        if not cursor.fetchone():
            cursor.execute("INSERT INTO category (category_name, category_id_number) VALUES (?, ?)", cat_name, cat_id)
    except Exception as e:
        print(f"Error inserting category: {e}")

print("Categories loaded")
conn.commit()
cursor.close()
conn.close()

# === Load SUBCATEGORY ===
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

for _, row in df.iterrows():
    try:
        subcat_id = str(row['SubCategoryId']).strip()
        subcat_name = str(row['SubCategory']).strip()
        cat_id = str(row['PrimaryCategoryId']).strip()
        if not subcat_id or not subcat_name or not cat_id:
            continue
        cursor.execute("SELECT category_id FROM category WHERE category_id_number = ?", cat_id)
        category = cursor.fetchone()
        if not category:
            continue
        cursor.execute("SELECT subcategory_id FROM subcategory WHERE subcategory_id_number = ?", subcat_id)
        if not cursor.fetchone():
            cursor.execute("INSERT INTO subcategory (sub_cat_name, subcategory_id_number, category_id) VALUES (?, ?, ?)",
                           subcat_name, subcat_id, category[0])
    except Exception as e:
        print(f"Error inserting subcategory: {e}")

print("Subcategories loaded")
conn.commit()
cursor.close()
conn.close()

# === Load COLOR_SHADE_FORMULATION ===
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

for _, row in df.iterrows():
    try:
        csf_id = str(row['CSFId']).strip()
        csf_name = str(row['CSF']).strip()
        if not csf_id or not csf_name:
            continue
        cursor.execute("SELECT csf_id FROM color_shade_formulation WHERE csf_id_number = ?", csf_id)
        if not cursor.fetchone():
            cursor.execute("INSERT INTO color_shade_formulation (csf_name, csf_id_number) VALUES (?, ?)", csf_name, csf_id)
    except Exception as e:
        print(f"Error inserting color_shade_formulation: {e}")

print("Color shade formulations loaded")
conn.commit()
cursor.close()
conn.close()


# === Load PRODUCTS ===
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

for _, row in df.iterrows():
    try:
        cdphid = str(row['CDPHId']).strip()
        product_name = str(row['ProductName']).strip()
        brand_name = str(row['BrandName']).strip()
        subcat_id = str(row['SubCategoryId']).strip()
        if not cdphid or not product_name or not brand_name or not subcat_id:
            print(f"Skipping row with missing required fields. CDPHID={cdphid}")
            continue
        cursor.execute("SELECT brand_id FROM brand WHERE brand_name = ?", brand_name)
        brand = cursor.fetchone()
        cursor.execute("SELECT subcategory_id FROM subcategory WHERE subcategory_id_number = ?", subcat_id)
        subcat = cursor.fetchone()
        raw_csf_id = row.get('CSFId', '')
        if pd.notna(raw_csf_id) and str(raw_csf_id).strip():
            try:
                csf_id_lookup = str(raw_csf_id).strip()
                cursor.execute("SELECT csf_id FROM color_shade_formulation WHERE csf_id_number = ?", csf_id_lookup)
                csf = cursor.fetchone()
                csf_value = int(csf[0]) if csf else None
            except:
                csf_value = None
        else:
            csf_value = None
        if not (brand and subcat):
            print(f"Skipping product. Missing brand or subcategory. CDPHID={cdphid}")
            continue
        cursor.execute("SELECT product_name_id FROM product_name WHERE product_name = ?", product_name)
        name_row = cursor.fetchone()
        if name_row:
            product_name_id = name_row[0]
        else:
            cursor.execute("INSERT INTO product_name (product_name) VALUES (?)", product_name)
            cursor.execute("SELECT SCOPE_IDENTITY()")
            product_name_id = cursor.fetchone()[0]
        cursor.execute("SELECT product_id FROM products WHERE CDPHID = ?", cdphid)
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO products (product_name_id, brand_id, subcategory_id, csf_id, CDPHID)
                VALUES (?, ?, ?, ?, ?, ?)
            """, product_name_id, int(brand[0]), int(subcat[0]), csf_value, cdphid)
    except Exception as e:
        print(f" Error inserting product with CDPHID={cdphid}: {e}")

print("Products loaded")
conn.commit()
cursor.close()
conn.close()


# === Load PRODUCT_NAME ===
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

for _, row in df.iterrows():
    try:
        product_name = str(row['ProductName']).strip()
        cursor.execute("SELECT product_name_id FROM product_name WHERE product_name = ?", product_name)
        if not cursor.fetchone():
            cursor.execute("INSERT INTO product_name (product_name) VALUES (?)", product_name)
    except Exception as e:
        print(f"Error inserting product_name: {product_name} → {e}")

print("Product names loaded")
conn.commit()
cursor.close()
conn.close()

# === Load PRODUCTS ===
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

for _, row in df.iterrows():
    try:
        cdphid = str(row['CDPHId']).strip()
        product_name = str(row['ProductName']).strip()
        brand_name = str(row['BrandName']).strip()
        subcat_id = str(row['SubCategoryId']).strip()
        if not cdphid or not product_name or not brand_name or not subcat_id:
            print(f"Skipping row with missing required fields. CDPHID={cdphid}")
            continue
        cursor.execute("SELECT product_name_id FROM product_name WHERE product_name = ?", product_name)
        name_row = cursor.fetchone()
        if not name_row:
            print(f"product_name not found for '{product_name}' (CDPHID={cdphid})")
            continue
        product_name_id = name_row[0]
        cursor.execute("SELECT brand_id FROM brand WHERE brand_name = ?", brand_name)
        brand = cursor.fetchone()
        cursor.execute("SELECT subcategory_id FROM subcategory WHERE subcategory_id_number = ?", subcat_id)
        subcat = cursor.fetchone()
        csf_value = None
        raw_csf_id = row.get('CSFId', '')
        if pd.notna(raw_csf_id) and str(raw_csf_id).strip():
            try:
                cursor.execute("SELECT csf_id FROM color_shade_formulation WHERE csf_id_number = ?", str(raw_csf_id).strip())
                csf = cursor.fetchone()
                csf_value = int(csf[0]) if csf else None
            except:
                csf_value = None
        if not (brand and subcat):
            print(f"Missing brand or subcat for CDPHID={cdphid}")
            continue
        cursor.execute("""SELECT product_id FROM products WHERE product_name_id = ? AND brand_id = ? AND subcategory_id = ? AND (csf_id = ? OR (csf_id IS NULL AND ? IS NULL))""",
                       product_name_id, int(brand[0]), int(subcat[0]), csf_value, csf_value)
        if not cursor.fetchone():
            cursor.execute("""INSERT INTO products (product_name_id, brand_id, subcategory_id, csf_id, CDPHID)
                VALUES (?, ?, ?, ?, ?)
            """, product_name_id, int(brand[0]), int(subcat[0]), csf_value, cdphid)
    except Exception as e:
        print(f"Error inserting product CDPHID={cdphid}: {e}")

print("✅ Products loaded")
conn.commit()
cursor.close()
conn.close()


# === Load CHEMICALS ===
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

for _, row in df.iterrows():
    try:
        name = str(row['ChemicalName']).strip()
        if not name:
            continue
        cursor.execute("SELECT chemical_id FROM chemical WHERE chemical_name = ?", name)
        if not cursor.fetchone():
            cursor.execute("INSERT INTO chemical (chemical_name) VALUES (?)", name)
    except Exception as e:
        print(f"Error inserting chemical: {e}")

print("Chemicals loaded")
conn.commit()
cursor.close()
conn.close()

# === Load PRODUCT_CHEMICAL ===
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

for _, row in df.iterrows():
    try:
        product_name = str(row['ProductName']).strip()
        brand_name = str(row['BrandName']).strip()
        subcat_id = str(row['SubCategoryId']).strip()
        raw_csf_id = str(row.get('CSFId', '')).strip()
        cursor.execute("SELECT product_name_id FROM product_name WHERE product_name = ?", product_name)
        name_row = cursor.fetchone()
        cursor.execute("SELECT brand_id FROM brand WHERE brand_name = ?", brand_name)
        brand_row = cursor.fetchone()
        cursor.execute("SELECT subcategory_id FROM subcategory WHERE subcategory_id_number = ?", subcat_id)
        subcat_row = cursor.fetchone()
        csf_value = None
        if raw_csf_id:
            cursor.execute("SELECT csf_id FROM color_shade_formulation WHERE csf_id_number = ?", raw_csf_id)
            csf_row = cursor.fetchone()
            csf_value = int(csf_row[0]) if csf_row else None
        if not all([name_row, brand_row, subcat_row]):
            print(f"⚠️ Skipping due to missing lookup. ProductName: {product_name}, Brand: {brand_name}")
            continue
        cursor.execute("""
            SELECT product_id FROM products WHERE product_name_id = ? AND brand_id = ? AND subcategory_id = ? AND (csf_id = ? OR (csf_id IS NULL AND ? IS NULL)""", 
                    name_row[0], brand_row[0], subcat_row[0], csf_value, csf_value)
        product = cursor.fetchone()
        chemical_name = str(row.get('ChemicalName', '')).strip()
        if not chemical_name:
            continue
        cursor.execute("SELECT chemical_id FROM chemical WHERE chemical_name = ?", chemical_name)
        chemical = cursor.fetchone()

        if not product or not chemical:
            continue
        cursor.execute("""SELECT 1 FROM product_chemical WHERE product_id = ? AND chemical_id = ?""", product[0], chemical[0])
        if cursor.fetchone():
            continue
        initial_date = row.get('InitialDateReported')
        initial_date = "1900-01-01" if pd.isna(initial_date) else pd.to_datetime(initial_date).date()
        most_recent_date = row.get('MostRecentDateReported')
        most_recent_date = "1900-01-01" if pd.isna(most_recent_date) else pd.to_datetime(most_recent_date).date()
        discontinued_date = row.get('DiscontinuedDate')
        discontinued_date = "1900-01-01" if pd.isna(discontinued_date) else pd.to_datetime(discontinued_date).date()
        created_at = row.get('ChemicalCreatedAt')
        created_at = "1900-01-01" if pd.isna(created_at) else pd.to_datetime(created_at).date()
        updated_at = row.get('ChemicalUpdatedAt')
        updated_at = "1900-01-01" if pd.isna(updated_at) else pd.to_datetime(updated_at).date()
        removed_date = row.get('ChemicalDateRemoved')
        removed_date = "1900-01-01" if pd.isna(removed_date) else pd.to_datetime(removed_date).date()
        cursor.execute("""INSERT INTO product_chemical (chemical_id, product_id, initial_date_reported, most_recent_date_reported, discontinued_date, chemical_created_at, chemical_updated_at,
                chemical_date_removed, chemical_id_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            chemical[0],product[0],initial_date,most_recent_date,discontinued_date,created_at,updated_at,removed_date,row.get('ChemicalId'))
    except Exception as e:
        print(f"Error inserting product_chemical: {e}")

print("Product-chemical relationships loaded")
conn.commit()
cursor.close()
conn.close()

# === Load the missing rows dataset to PRODUCT CHEMICAL ===
df['CSFId'] = df['CSFId'].astype(str).str.lower().str.strip()

# Select rows where CSFId is missing
df_missing = df[df['CSFId'].isin(['', 'nan'])]
df_missing

conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

for _, row in df_missing.iterrows():
    try:
        product_name = str(row['ProductName']).strip().lower()
        brand_name = str(row['BrandName']).strip().lower()
        subcat_id = str(row['SubCategoryId']).strip()
        chemical_name = str(row['ChemicalName']).strip().lower()
        cursor.execute("SELECT product_name_id FROM product_name WHERE product_name = ?", product_name)
        name_row = cursor.fetchone()
        cursor.execute("SELECT brand_id FROM brand WHERE brand_name = ?", brand_name)
        brand_row = cursor.fetchone()
        cursor.execute("SELECT subcategory_id FROM subcategory WHERE subcategory_id_number = ?", subcat_id)
        subcat_row = cursor.fetchone()
        if not all([name_row, brand_row, subcat_row]):
            print(f"Skipping missing lookup: {product_name}, {brand_name}, {subcat_id}")
            continue
        cursor.execute("""SELECT product_id FROM products WHERE product_name_id = ? AND brand_id = ? AND subcategory_id = ? AND csf_id IS NULL""", name_row[0], brand_row[0], subcat_row[0])
        product = cursor.fetchone()
        if not product:
            print(f"Skipping missing product: {product_name}, {brand_name}, {subcat_id}, csf: {raw_csf_id}")
            continue
        cursor.execute("SELECT chemical_id FROM chemical WHERE chemical_name = ?", chemical_name)
        chemical = cursor.fetchone()
        if not chemical:
            print(f"Skipping missing chemical: {chemical_name}")
            continue
        cursor.execute("""SELECT 1 FROM product_chemical WHERE product_id = ? AND chemical_id = ?""", product[0], chemical[0])
        if cursor.fetchone():
            continue
        initial_date = row.get('InitialDateReported')
        initial_date = "1900-01-01" if pd.isna(initial_date) else pd.to_datetime(initial_date).date()
        most_recent_date = row.get('MostRecentDateReported')
        most_recent_date = "1900-01-01" if pd.isna(most_recent_date) else pd.to_datetime(most_recent_date).date()
        discontinued_date = row.get('DiscontinuedDate')
        discontinued_date = "1900-01-01" if pd.isna(discontinued_date) else pd.to_datetime(discontinued_date).date()
        created_at = row.get('ChemicalCreatedAt')
        created_at = "1900-01-01" if pd.isna(created_at) else pd.to_datetime(created_at).date()
        updated_at = row.get('ChemicalUpdatedAt')
        updated_at = "1900-01-01" if pd.isna(updated_at) else pd.to_datetime(updated_at).date()
        removed_date = row.get('ChemicalDateRemoved')
        removed_date = "1900-01-01" if pd.isna(removed_date) else pd.to_datetime(removed_date).date()
        cursor.execute("""INSERT INTO product_chemical (chemical_id, product_id, initial_date_reported, most_recent_date_reported, discontinued_date, chemical_created_at, chemical_updated_at,
                chemical_date_removed, chemical_id_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            chemical[0],product[0],initial_date,most_recent_date,discontinued_date,created_at,updated_at,removed_date,str(row.get('ChemicalId')))
    except Exception as e:
        print(f"Error inserting row: {e}")

print("Missing CSF rows successfully loaded.")
conn.commit()
cursor.close()
conn.close()


# === Load and Clean CSV Sales ===
df_sales = pd.read_csv("C:/Users/lsav1/OneDrive/Desktop/sales_cleaned.csv")
df_sales.columns = df_sales.columns.str.strip()

for col in df_sales.select_dtypes(include='object').columns:
    df_sales[col] = df_sales[col].astype(str).str.strip()

date_cols = ['transaction_date']
for col in date_cols:
    if col in df_sales.columns:
        df_sales[col] = pd.to_datetime(df_sales[col], errors='coerce')   
        
# === Load CUSTOMER ===
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

for _, row in df_sales.iterrows():
    try:
        name = str(row['Customer Name']).strip()
        gender_str = str(row['Customer Gender']).strip()
        if not name:
            continue
        cursor.execute("SELECT gender_id FROM gender WHERE gender = ?", gender_str)
        gender_row = cursor.fetchone()
        if not gender_row:
            print(f"Gender '{gender_str}' not found in gender table.")
            continue       
        gender_id = gender_row[0]    
        cursor.execute("SELECT customer_id FROM customer WHERE customer_name = ?", name)
        if not cursor.fetchone():
            cursor.execute("INSERT INTO customer (customer_name, gender_id) VALUES (?,?)", name, gender_id)
    except Exception as e:
        print(f"Error inserting customer: {e}")

print("Customer loaded")
conn.commit()
cursor.close()
conn.close()

df_sort = df_sales.sort_values(by='transaction_date') #sort needed to account for stock management

# === Load PRODUCT IN STORE ===
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

for _, row in df_sort.iterrows():
    try:
        product_name = str(row['ProductName']).strip()
        brand_name = str(row['BrandName']).strip()
        store_name = str(row['Store Name']).strip()
        price = float(row['Unit Price'])
        stock = int(row['Stock Remaining'])
        if not all([product_name, brand_name, store_name]):
            continue
        cursor.execute("SELECT brand_id FROM brand WHERE brand_name = ?", brand_name)
        brand_row = cursor.fetchone()
        if not brand_row:
            print(f"Brand not found: {brand_name}")
            continue
        brand_id = brand_row[0]
        cursor.execute("SELECT product_name_id FROM product_name WHERE product_name = ?", product_name)
        pn_row = cursor.fetchone()
        if not pn_row:
            print(f"Product name not found: {product_name}")
            continue
        product_name_id = pn_row[0]
        cursor.execute(""" SELECT TOP 1 product_id FROM products WHERE product_name_id = ? AND brand_id = ?""", product_name_id, brand_id)
        product_row = cursor.fetchone()
        if not product_row:
            print(f"Product not found for name: {product_name}, brand: {brand_name}")
            continue
        product_id = product_row[0]
        cursor.execute("SELECT store_id FROM store WHERE store_name = ?", store_name)
        store_row = cursor.fetchone()
        if not store_row:
            print(f"Store not found: {store_name}")
            continue
        store_id = store_row[0]
        cursor.execute("SELECT product_store_id FROM product_in_store WHERE store_id = ? AND product_id = ?", store_id, product_id)
        if cursor.fetchone():
            continue
        cursor.execute("""INSERT INTO product_in_store (store_id, product_id, price, stock_remaining) VALUES (?, ?, ?, ?)""", store_id, product_id, price, stock)
    except Exception as e:
        print(f"Error inserting product in store: {e}")

print("✅ Product-in-store load complete")
conn.commit()
cursor.close()
conn.close()

# === Load Initial stock ===
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

for _, row in df_sort.iterrows():
    try:
        product_name = str(row['ProductName']).strip()
        brand_name = str(row['BrandName']).strip()
        store_name = str(row['Store Name']).strip()
        price = float(row['Unit Price'])
        stock = int(row['Stock Remaining'])
        if not all([product_name, brand_name, store_name]):
            continue
        cursor.execute("SELECT brand_id FROM brand WHERE brand_name = ?", brand_name)
        brand_row = cursor.fetchone()
        if not brand_row:
            print(f"Brand not found: {brand_name}")
            continue
        brand_id = brand_row[0]
        cursor.execute("SELECT product_name_id FROM product_name WHERE product_name = ?", product_name)
        pn_row = cursor.fetchone()
        if not pn_row:
            print(f"Product name not found: {product_name}")
            continue
        product_name_id = pn_row[0]
        cursor.execute("""SELECT TOP 1 product_id FROM products WHERE product_name_id = ? AND brand_id = ?""", product_name_id, brand_id)
        product_row = cursor.fetchone()
        if not product_row:
            print(f"Product not found for name: {product_name}, brand: {brand_name}")
            continue
        product_id = product_row[0]
        cursor.execute("SELECT store_id FROM store WHERE store_name = ?", store_name)
        store_row = cursor.fetchone()
        if not store_row:
            print(f"Store not found: {store_name}")
            continue
        store_id = store_row[0]
        cursor.execute("SELECT product_store_id FROM product_in_store WHERE product_id = ? AND store_id = ?", product_id, store_id)
        if cursor.fetchone():
            continue  
        cursor.execute("""INSERT INTO product_in_store (product_id, store_id, price, stock_remaining) VALUES (?, ?, ?, ?)""", product_id, store_id, price, stock)
        cursor.execute("SELECT product_store_id FROM product_in_store WHERE product_id = ? AND store_id = ?", product_id, store_id)
        product_store_id = cursor.fetchone()[0]
        cursor.execute("""INSERT INTO stock_movement_log (product_store_id, quantity_changed, new_stock_remaining, reason) VALUES (?, ?, ?, ?)""", product_store_id, stock, stock, 'initial')
    except Exception as e:
        print(f"Error processing row: {e}")

print("Initial stock load complete")
conn.commit()
cursor.close()
conn.close()


# === Load transaction ===
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

for _, row in df_sales.iterrows():
    try:
        trans_id = str(row['Transaction ID']).strip()
        name = str(row['Customer Name']).strip()
        channel = str(row['Sales Channel']).strip()
        total = float(row['Transaction Total'])
        transaction_date = pd.to_datetime(row['transaction_date']).date()
        cursor.execute("SELECT 1 FROM transactions WHERE transaction_id_number = ?", trans_id)
        if cursor.fetchone():
            continue
        cursor.execute("SELECT customer_id FROM customer WHERE customer_name = ?", name)
        customer_row = cursor.fetchone()
        if not customer_row:
            print(f"Customer not found: {name}")
            continue
        customer_id = customer_row[0]
        cursor.execute("SELECT channel_id FROM saleschannel WHERE channel_name = ?", channel)
        channel_row = cursor.fetchone()
        if not channel_row:
            print(f"Channel not found: {channel}")
            continue
        channel_id = channel_row[0]
        cursor.execute("INSERT INTO transactions (transaction_date, transaction_total, transaction_id_number, customer_id, channel_id) VALUES (?, ?, ?, ?, ?)", transaction_date, total, trans_id, customer_id, channel_id)
    except Exception as e:
        print(f"Error inserting transaction: {e}")

print("Transaction load complete")
conn.commit()
cursor.close()
conn.close()


# === Load transaction line items===
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=LSComp;DATABASE=cosmetic_chemicals;Trusted_Connection=yes;")
cursor = conn.cursor()

for _, row in df_sales.iterrows():
    try:
        trans_id = str(row['Transaction ID']).strip()
        product_name = str(row['ProductName']).strip()
        brand_name = str(row['BrandName']).strip()
        store_name = str(row['Store Name']).strip()
        quantity = int(row['Sale Quantity'])
        line_total = float(row['Line Item Total'])
        unit_price = float(row['Unit Price'])
        if not all([trans_id, product_name, brand_name, store_name]):
            continue
        cursor.execute("SELECT transaction_id FROM transactions WHERE transaction_id_number = ?", trans_id)
        trans_row = cursor.fetchone()
        if not trans_row:
            print(f"Transaction not found: {trans_id}")
            continue
        transaction_id = trans_row[0]
        cursor.execute("SELECT brand_id FROM brand WHERE brand_name = ?", brand_name)
        brand_row = cursor.fetchone()
        if not brand_row:
            print(f"Brand not found: {brand_name}")
            continue
        brand_id = brand_row[0]
        cursor.execute("SELECT product_name_id FROM product_name WHERE product_name = ?", product_name)
        pn_row = cursor.fetchone()
        if not pn_row:
            print(f"Product name not found: {product_name}")
            continue
        product_name_id = pn_row[0]
        cursor.execute("""
           SELECT TOP 1 product_id FROM products WHERE product_name_id = ? AND brand_id = ?""", product_name_id, brand_id)
        product_row = cursor.fetchone()
        if not product_row:
            print(f"Product not found for name: {product_name}, brand: {brand_name}")
            continue
        product_id = product_row[0]
        cursor.execute("SELECT store_id FROM store WHERE store_name = ?", store_name)
        store_row = cursor.fetchone()
        if not store_row:
            print(f"Store not found: {store_name}")
            continue
        store_id = store_row[0]
        cursor.execute("SELECT product_store_id FROM product_in_store WHERE product_id = ? AND store_id = ?", product_id, store_id)
        ps_row = cursor.fetchone()
        if not ps_row:
            print(f"product_store_id not found for product: {product_name} in store: {store_name}")
            continue
        product_store_id = ps_row[0]
        cursor.execute("""INSERT INTO transaction_lineitem (transaction_id, product_store_id, sale_quantity, line_total, unit_price)
            VALUES (?, ?, ?, ?, ?)""", transaction_id, product_store_id, quantity, line_total, unit_price)
    except Exception as e:
        print(f"Error inserting line item: {e}")

print("Transaction line items load complete")
conn.commit()
cursor.close()
conn.close()

