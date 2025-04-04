import os
import random
from typing import List, Optional, Tuple
import psycopg2
from faker import Faker

fake: Faker = Faker()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    port=os.getenv("DB_PORT")
)
cur = conn.cursor()

def insert_users(n: int = 10) -> None:
    for _ in range(n):
        cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s)",
            (fake.name(), fake.unique.email())
        )

def insert_addresses() -> None:
    cur.execute("SELECT id FROM users")
    user_ids: List[int] = [r[0] for r in cur.fetchall()]
    for user_id in user_ids:
        for _ in range(random.randint(1, 2)):
            cur.execute(
                """INSERT INTO addresses (user_id, address_line, city, postal_code, country)
                   VALUES (%s, %s, %s, %s, %s)""",
                (user_id, fake.street_address(), fake.city(), fake.postcode(), fake.country())
            )

def insert_categories() -> None:
    categories: List[Tuple[str, Optional[int]]] = [
        ('Electronics', None),
        ('Laptops', 1),
        ('Smartphones', 1),
        ('Fashion', None),
        ('Men', 4),
        ('Women', 4)
    ]
    for name, parent_id in categories:
        cur.execute(
            "INSERT INTO categories (name, parent_id) VALUES (%s, %s)",
            (name, parent_id)
        )
    # ❗ ナイーブツリー

def fake_tags() -> str:
    tag_pool: List[str] = ['electronics', 'home', 'fitness', 'beauty', 'kitchen', 'outdoors']
    return ",".join(random.sample(tag_pool, k=random.randint(1, 3)))
    # ❗ カンマ区切り

def insert_products(n: int = 20) -> None:
    cur.execute("SELECT id FROM categories")
    category_ids: List[int] = [r[0] for r in cur.fetchall()]
    
    if not category_ids:
        raise ValueError("No categories found in the database.")
    
    for _ in range(n):
        cur.execute(
            """INSERT INTO products (name, description, price, category_id, tags, product_type)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (
                fake.catch_phrase(),
                fake.text(max_nb_chars=100),
                round(random.uniform(10.0, 1000.0), 2),
                random.choice(category_ids),
                fake_tags(),
                random.choice(['physical', 'digital'])  # ❗ IDリクワイアド
            )
        )
        result = cur.fetchone()
        if result == None:
            raise ValueError("Failed to insert product and retrieve its ID.")
        else:
            insert_product_attributes(result[0])

def insert_product_attributes(product_id: int) -> None:
    attributes: List[Tuple[str, str]] = [
        ('color', random.choice(['red', 'blue', 'green', 'black'])),
        ('size', random.choice(['S', 'M', 'L', 'XL'])),
        ('brand', fake.company())
    ]
    for name, value in attributes:
        cur.execute(
            """INSERT INTO product_attributes (product_id, attribute_name, attribute_value)
               VALUES (%s, %s, %s)""",
            (product_id, name, value)
        )
    # ❗ EAV

def insert_orders(n: int = 15) -> None:
    cur.execute("SELECT id FROM users")
    user_ids: List[int] = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM addresses")
    address_ids: List[int] = [r[0] for r in cur.fetchall()]
    for _ in range(n):
        user_id: int = random.choice(user_ids)
        address_id: int = random.choice(address_ids)
        cur.execute(
            """INSERT INTO orders (user_id, address_id, status)
               VALUES (%s, %s, %s) RETURNING id""",
            (user_id, address_id, random.choice(['pending', 'shipped', 'delivered']))
        )
        result = cur.fetchone()
        if result == None:
            raise ValueError("Failed to insert order and retrieve its ID.")
        else:
            insert_order_items(result[0])
        

def insert_order_items(order_id: int) -> None:
    cur.execute("SELECT id, price FROM products")
    products: List[Tuple[int, float]] = cur.fetchall()
    for _ in range(random.randint(1, 3)):
        product_id, price = random.choice(products)
        quantity: int = random.randint(1, 5)
        cur.execute(
            """INSERT INTO order_items (order_id, product_id, quantity, unit_price)
               VALUES (%s, %s, %s, %s)""",
            (order_id, product_id, quantity, price)
        )

def main() -> None:
    insert_users()
    insert_addresses()
    insert_categories()
    insert_products()
    insert_orders()
    conn.commit()
    print("✅ Dummy data inserted.")

if __name__ == "__main__":
    main()
