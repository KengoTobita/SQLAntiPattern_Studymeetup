import psycopg2
from faker import Faker
import random

fake = Faker()

# Dockercomposeで立ち上げたDBに接続するためのリトライ処理
conn = psycopg2.connect(
        dbname="antipat",
        user="user",
        password="pass",
        host="db",
        port="5432"
        )

cur = conn.cursor()

# ----------------------------------------
def insert_bug_status():
    statuses = ['NEW', 'ASSIGNED', 'FIXED', 'VERIFIED', 'CLOSED']
    for status in statuses:
        cur.execute("INSERT INTO BugStatus (status) VALUES (%s) ON CONFLICT DO NOTHING", (status,))
    print("Inserted BugStatus")

def insert_accounts(n:int=10):
    for _ in range(n):
        cur.execute("""
            INSERT INTO Accounts (account_name, first_name, last_name, email, password_hash, portrait_image, hourly_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            fake.user_name(),
            fake.first_name(),
            fake.last_name(),
            fake.email(),
            fake.sha256(),
            None,
            round(random.uniform(20, 150), 2)
        ))
    print(f"Inserted {n} Accounts")

def insert_products(n:int=5):
    for _ in range(n):
        cur.execute("INSERT INTO Products (product_name) VALUES (%s)", (fake.company(),))
    print(f"Inserted {n} Products")

def insert_bugs(n:int=20):
    cur.execute("SELECT account_id FROM Accounts")
    account_ids = [row[0] for row in cur.fetchall()]
    cur.execute("SELECT status FROM BugStatus")
    status_list = [row[0] for row in cur.fetchall()]

    for _ in range(n):
        date_reported = fake.date_between(start_date='-30d', end_date='today')
        cur.execute("""
            INSERT INTO Bugs (date_reported, summary, description, resolution, reported_by, assigned_to, verified_by, status, priority, hours)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            date_reported,
            fake.sentence(nb_words=6),
            fake.text(max_nb_chars=200),
            fake.text(max_nb_chars=100),
            random.choice(account_ids),
            random.choice(account_ids),
            random.choice(account_ids),
            random.choice(status_list),
            random.choice(['Low', 'Medium', 'High', 'Critical']),
            round(random.uniform(1, 40), 2)
        ))
    print(f"Inserted {n} Bugs")

def insert_comments(n:int=40):
    cur.execute("SELECT bug_id FROM Bugs")
    bug_ids = [row[0] for row in cur.fetchall()]
    cur.execute("SELECT account_id FROM Accounts")
    account_ids = [row[0] for row in cur.fetchall()]

    for _ in range(n):
        cur.execute("""
            INSERT INTO Comments (bug_id, author, comment_date, comment)
            VALUES (%s, %s, %s, %s)
        """, (
            random.choice(bug_ids),
            random.choice(account_ids),
            fake.date_time_between(start_date='-30d', end_date='now'),
            fake.paragraph()
        ))
    print(f"Inserted {n} Comments")

def insert_tags():
    cur.execute("SELECT bug_id FROM Bugs")
    bug_ids = [row[0] for row in cur.fetchall()]
    tags_pool = ["UI", "Backend", "Performance", "Crash", "Security", "UX"]

    for bug_id in bug_ids:
        tags = random.sample(tags_pool, k=random.randint(1, 3))
        for tag in tags:
            cur.execute("INSERT INTO Tags (bug_id, tag) VALUES (%s, %s) ON CONFLICT DO NOTHING", (bug_id, tag))
    print("Inserted Tags")

def insert_bug_products():
    cur.execute("SELECT bug_id FROM Bugs")
    bug_ids = [row[0] for row in cur.fetchall()]
    cur.execute("SELECT product_id FROM Products")
    product_ids = [row[0] for row in cur.fetchall()]

    for bug_id in bug_ids:
        linked = random.sample(product_ids, k=random.randint(1, 2))
        for product_id in linked:
            cur.execute("""
                INSERT INTO BugsProducts (bug_id, product_id) VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (bug_id, product_id))
    print("Inserted BugsProducts")

def insert_screenshots():
    cur.execute("SELECT bug_id FROM Bugs")
    bug_ids = [row[0] for row in cur.fetchall()]

    for bug_id in bug_ids:
        num_images = random.randint(0, 3)  # 0〜3枚の画像を付ける
        for i in range(num_images):
            fake_image_data = fake.binary(length=1024)  # 1KBのバイナリ
            caption = fake.sentence(nb_words=6)
            cur.execute("""
                INSERT INTO Screenshots (bug_id, image_id, screenshot_image, caption)
                VALUES (%s, %s, %s, %s)
            """, (
                bug_id, i + 1, fake_image_data, caption
            ))
    print("Inserted Screenshots")

# ----------------------------------------

# データ生成と挿入
insert_bug_status()
insert_accounts(15)
insert_products(5)
insert_bugs(30)
insert_comments(60)
insert_tags()
insert_bug_products()
insert_screenshots()

# コミットと終了
conn.commit()
cur.close()
conn.close()
print("✅ ダミーデータ挿入完了")
