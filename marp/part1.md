---
marp: true
theme: default
size: 16:9
paginate: true
headingDivider: 2
backgroundImage: url('https://marp.app/assets/hero-background.svg')
---

<!-- I部 データベース論理設計のアンチパターン -->

# SQLアンチパターン<br> I部 データベース論理設計のアンチパターン

<!-- --- -->
## 第1章 ジェイウォーク（信号無視）

<!-- --- -->
## 第1章 ジェイウォーク（信号無視）
- **目的**: 複数の値を持つ属性を格納する
- **アンチパターン**: カンマ区切りでリストを格納する
- **問題点**:
  - 検索・更新・検証が困難

<!-- --- -->

## 多vs多の状況ってあるある……
`product`データに担当者を一人つけている<br>
  → これを複数人対応させたい。(社内、社外もろもろ……)

<!-- --- -->

## 1-1 多vs多の構成 ~アンチパターン~
カンマ区切りで複数データを管理する
```sql
CREATE TABLE Products (
  product_id   SERIAL PRIMARY KEY,
  product_name VARCHAR(1000),
  account_id   VARCHAR(100), -- カンマ区切りのリスト
  -- 他の列. . .
);

INSERT INTO Products (product_id, product_name, account_id)
VALUES (DEFAULT, 'Visual TurboBuilder', '12,34');
```
<!-- --- -->

##  1-1 多vs多の構成 ~アンチパターンへのツッコミ~
* 外からクエリでいじると死ぬ(1-2-1~3,5)
    * `WHERE`, `JOIN`, `sum()`などの集約関数,値の検証などなど……
* `acount_id`のUPDATEで死ぬ (1-2-4)
* 区切り文字は当該データ内で本当に使用されないか(1-2-6)
* 設定された長さは問題ないか(1-2-7)

<!-- --- -->

## 1-1 具体例
アカウントID`12`が含まれるデータを引っ張るには……
```SQL
SELECT * FROM Products WHERE account_id REGEXP '[[:<:]]12[[:>:]]';
```
`JOIN`でも死ぬ
```SQL
SELECT * FROM Products AS p INNER JOIN Accounts AS a
    ON p.account_id REGEXP '[[:<:]]' || a.account_id || '[[:>:]]'
WHERE p.product_id = 123;
```

## 1-1 具体例
`COUNT()`が使えないからカンマをカウント。無駄にハッキー……
```SQL
SELECT product_id, LENGTH(account_id) - LENGTH(REPLACE(account_id, ',', '')) + 1
    AS contacts_per_product
FROM Products;
```
`VECHAR(30)`だとしてエントリーの長さは妥当？
```SQL
UPDATE Products SET account_id = '10,14,18,22,26,30,34,38,42,46' --10件
WHERE product_id = 123;

UPDATE Products SET account_id = '101418,222630,343842,467790' --4件
WHERE product_id = 123;
```

<!-- --- -->

## 1-1 解決策「交差テーブル」

|交差テーブル|ジェイクウォーク|
|-|-|
|![ left ](/image/crossig.png)|![ right ](/image/jakewark.png)|

→……だから「信号無視」ってな！
<!-- --- -->

## 1-1 交差テーブル作成クエリ
`Product`と`Account`のIDを持ってきて突っ込む
```SQL
CREATE TABLE Contacts (
  product_id  BIGINT UNSIGNED NOT NULL,
  account_id  BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (product_id, account_id),
  FOREIGN KEY (product_id) REFERENCES Products(product_id),
  FOREIGN KEY (account_id) REFERENCES Accounts(account_id)
);

INSERT INTO Contacts (product_id, account_id)
VALUES (123, 12), (123, 34), (345, 23), (567, 12), (567, 34);
```
<!-- --- -->

## 1-1 ほぉら、楽になったろう。（join）
JOIN操作が楽になりました。
```SQL
SELECT * FROM Products AS p INNER JOIN Accounts AS a
    ON p.account_id REGEXP '[[:<:]]' || a.account_id || '[[:>:]]'
WHERE p.product_id = 123;
```
```SQL
SELECT a.*
FROM Accounts AS a INNER JOIN Contacts AS c ON a.account_id = c.account_id
WHERE c.product_id = 123;
```
<!-- --- -->

## 1-1 ほぉら、楽になったろう。（集約）
集約操作が楽になりました。
```SQL
SELECT product_id, LENGTH(account_id) - LENGTH(REPLACE(account_id, ',', '')) + 1
    AS contacts_per_product
FROM Products;
```
```SQL
SELECT product_id, COUNT(*) AS accounts_per_product
FROM Contacts
GROUP BY product_id;
```

<!-- --- -->

## 1-1 ほぉら、楽になったろう。（その他）
* 値の検証についても外部キーの制約によってなされる
* 区切り文字からの開放
* リストの長さ問題からの開放

<!-- --- -->

## [場外乱闘]交差テーブル以外の方法
* MongoDBとかNoSQLの使用(次章詳しく)
* PostgreSQLの`jsonb`とかを使う
    → RDB in JSON?!

<!-- --- -->
## [場外乱闘]PostgreSQLでJSONを扱うには？
`json`と`josnb`があり、どちらもJSON形式をほぼほぼサポートしてるらしい。
<table>
 <tr>
   <th>json型</th>
   <td>入力値のコピー</td>
   <td>空白、キー順序、キー被りがOK</td>
 </tr>
 <tr>
   <th>jsonb型</th>
   <td>入力後に変換</td>
   <td>SELECT高速化、インデクスをサポート</td>
 </tr>
</table>

## [場外乱闘]　JSON内部データ型について
<table summary="JSONプリミティブ型とPostgreSQL型の対応表" border="1"><colgroup><col><col><col></colgroup><thead><tr><th>JSON プリミティブ型</th><th><span class="productname">PostgreSQL</span>型</th><th>注釈</th></tr></thead><tbody><tr><td><code class="type">string</code></td><td><code class="type">text</code></td><td><code class="literal">\u0000</code>は許可されません。
またデータベースエンコーディングがUTF8でない場合、非アスキーのユニコードエスケープも許可されません。</td></tr><tr><td><code class="type">number</code></td><td><code class="type">numeric</code></td><td><code class="literal">NaN</code> と <code class="literal">infinity</code> 値は許可されません</td></tr><tr><td><code class="type">boolean</code></td><td><code class="type">boolean</code></td><td>小文字の<code class="literal">true</code> と <code class="literal">false</code> という綴りのみ許可されます</td></tr><tr><td><code class="type">null</code></td><td>(none)</td><td>SQLの<code class="literal">NULL</code>とは概念が異なります</td></tr></tbody></table>


## [場外乱闘]実は便利？`jsonb`型
```SQL
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  profile JSONB
);

INSERT INTO users (profile) VALUES
  ('{"name": "Taro", "age": 30, "skills": ["SQL", "Python"], "address": {"city": "Tokyo", "zip": "100-0001"}}'),
  ('{"name": "Hanako", "age": 25, "skills": ["JavaScript"], "address": {"city": "Osaka", "zip": "530-0001"}}');

```
`->`でJSONとして、`->>`で文字として
```SQL
SELECT profile->'address'->>'city' AS city FROM users;
SELECT profile->>'name' AS name FROM users;
SELECT * AS skills FROM users WHERE (profile->>'age')::int >=30;
```

## [場外乱闘]実は便利？`jsonb`型
```SQL
SELECT id, jsonb_array_elements_text(profile->'skills') AS skill FROM users;
 
 id |    skil    
----+------------
  1 | SQL
  1 | Python
  2 | JavaScript

```

```SQL
SELECT id, jsonb_object_keys(profile) AS keys FROM users;
```
```SQL
UPDATE users
SET profile = jsonb_set(profile, '{skills}', (profile->'skills') || '"Go"')
WHERE profile->>'name' = 'Hanako';
```

## [場外乱闘]実は便利？`jsonb`型
<table data-start="875" data-end="1153" node="[object Object]"><thead data-start="875" data-end="925"><tr data-start="875" data-end="925"><th data-start="875" data-end="888">表記</th><th data-start="888" data-end="919">意味</th><th data-start="919" data-end="925">備考</th></tr></thead><tbody data-start="983" data-end="1153"><tr data-start="983" data-end="1038"><td><code data-start="985" data-end="991">'Go'</code></td><td>SQL文字列 <code data-start="1007" data-end="1013">"Go"</code>（JSONではない）</td><td>❌ エラーになります</td></tr><tr data-start="1039" data-end="1092"><td><code data-start="1041" data-end="1049">'"Go"'</code></td><td>SQL文字列としての JSON文字列 <code data-start="1075" data-end="1081">"Go"</code></td><td>✅ 正しい！</td></tr><tr data-start="1093" data-end="1153"><td><code data-start="1095" data-end="1105">'["Go"]'</code></td><td>SQL文字列としての JSON配列 <code data-start="1128" data-end="1136">["Go"]</code></td><td>✅ 配列で追加する時など</td></tr></tbody></table>

## [場外乱闘]実は便利？`jsonb`型
```SQL
CREATE INDEX idx_profile_ops ON users USING gin (profile);
CREATE INDEX idx_profile_path ON users USING gin (profile jsonb_path_ops);
CREATE INDEX idx_profile_name ON users ((profile->>'name'));
CREATE INDEX idx_profile_age ON users (((profile->>'age')::int));
```


## [場外乱闘]実は便利？`jsonb`型
<table data-start="400" data-end="679" node="[object Object]"><thead data-start="400" data-end="429"><tr data-start="400" data-end="429"><th data-start="400" data-end="411">インデックス種別</th><th data-start="411" data-end="416">対象</th><th data-start="416" data-end="421">特徴</th><th data-start="421" data-end="429">主な用途</th></tr></thead><tbody data-start="476" data-end="679"><tr data-start="476" data-end="527"><td>GIN + <code data-start="484" data-end="495">jsonb_ops</code></td><td>JSON全体</td><td>多機能だが重い</td><td>複雑なクエリ向け</td></tr><tr data-start="528" data-end="586"><td>GIN + <code data-start="536" data-end="552">jsonb_path_ops</code></td><td>JSON全体</td><td><code data-start="564" data-end="568">@&gt;</code>専用・高速</td><td>部分一致検索が主</td></tr><tr data-start="587" data-end="634"><td>関数インデックス</td><td>JSONのキー指定</td><td>軽量でクエリ特化</td><td>よく使うキーに最適</td></tr><tr data-start="635" data-end="679"><td>複合インデックス</td><td>複数条件に対応</td><td>高度な最適化</td><td>AND条件などに対応</td></tr></tbody></table>

## [場外乱闘]実は便利？`jsonb`型
ジェイウォークにはこう！
```SQL
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title TEXT,
    tags JSONB
);
INSERT INTO posts (title, tags)
VALUES
('Post A', '["tech", "ai"]'),
('Post B', '["science", "ai"]'),
('Post C', '["opensource"]');
```
## [場外乱闘]実は便利？`jsonb`型
特定の値を
```SQL
SELECT * FROM posts WHERE tags ? 'ai';
```
すべて含むか(`@>`演算子)
```SQL
SELECT * FROM posts WHERE tags @> '["ai", "tech"]';
```
いずれかを含むか(`?|`演算子)
```SQL
SELECT * FROM posts WHERE tags ?| array['tech', 'opensource'];
```

<!-- --- -->

## 1-1 ジェイクウォークまとめ
* 「このリストでサポートしなくてはならない最大エントリー数は？」
* 「SQLで単語協会を一致させる方法を知ってる？」
*  「リストのエントリに絶対に使われない文字って？」

**一つ一つの値は個別の行と列に格納しよう**

<!-- --- -->

# 第2章 ナイーブツリー（素朴な木）

<!-- --- -->
## 第2章 ナイーブツリー（素朴な木）
- **目的**: 階層構造の格納
- **アンチパターン**: 隣接リストのみを使用

<!-- --- -->
## 第2章 ナイーブツリー（素朴な木）
枝分かれや連鎖を繰り返す階層構造をEDBで実現する場合に使用。
RDBに突っ込むならそれなりに工夫が必要

* 商品カテゴリーのパンくず表示
* 組織体系のツリー表示
* サイトメニューの改装ナビ

本書籍では「**バグ報告のレスバを表示する**」という
ユースケースでアンチパターンを紹介

<!-- --- -->
## 2-2 アンチパターン: 常に親にのみ依存
通称:**隣接リスト**
```SQL
CREATE TABLE Comments (
  comment_id   SERIAL PRIMARY KEY,
  parent_id    BIGINT UNSIGNED, --お客様！！困ります！！あーっ！！
  bug_id       BIGINT UNSIGNED NOT NULL,
  author       BIGINT UNSIGNED NOT NULL,
  comment_date DATETIME NOT NULL,
  comment      TEXT NOT NULL,
  FOREIGN KEY (parent_id) REFERENCES Comments(comment_id),
  FOREIGN KEY (bug_id) REFERENCES Bugs(bug_id),
  FOREIGN KEY (author) REFERENCES Accounts(account_id)
);
```
<!-- --- -->

## 2-2 わかりやすいER図
![w:700](/image/TreeAntipat.png)

<!-- --- -->

## 2-2 こんなデータになるお

<table>
  <thead>
    <tr>
      <th>comment_id</th>
      <th>parent_id</th>
      <th>bug_id</th>
      <th>author</th>
      <th>comment_date</th>
      <th>comment</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td>null</td>
      <td>1001</td>
      <td>201</td>
      <td>2025-04-01 10:00</td>
      <td>アプリが起動しません。</td>
    </tr>
    <tr>
      <td>2</td>
      <td>1</td>
      <td>1001</td>
      <td>202</td>
      <td>2025-04-01 10:05</td>
      <td>ログにエラーは出ていますか？</td>
    </tr>
    <tr>
      <td>3</td>
      <td>2</td>
      <td>1001</td>
      <td>201</td>
      <td>2025-04-01 10:10</td>
      <td>「Segmentation fault」と出ていました。</td>
    </tr>
    <tr>
      <td>4</td>
      <td>1</td>
      <td>1001</td>
      <td>203</td>
      <td>2025-04-01 10:15</td>
      <td>OSのバージョンは何ですか？</td>
    </tr>
    <tr>
      <td>5</td>
      <td>4</td>
      <td>1001</td>
      <td>201</td>
      <td>2025-04-01 10:20</td>
      <td>Ubuntu 22.04 です。</td>
    </tr>
  </tbody>
</table>
<!-- --- -->

## 2-2　隣接リストのここがクソ
* 階層構造の取得がめんどい(2-2-1)
* ノード操作がクソ(2-2-2)

<!-- --- -->

## 2-2-1 階層構造を取得するには
親だけなら……
```SQL
SELECT c1.*, c2.*
FROM Comments c1 LEFT OUTER JOIN Comments c2
  ON c2.parent_id = c1.comment_id;
```
N代目前なら……
```SQL
SELECT c1.*, c2.*, c3.*, c4.*
FROM Comments c1 -- 1階層目
  LEFT OUTER JOIN Comments c2
    ON c2.parent_id = c1.comment_id -- 2階層目
  LEFT OUTER JOIN Comments c3
    ON c3.parent_id = c2.comment_id -- 3階層目
  LEFT OUTER JOIN Comments c4
    ON c4.parent_id = c3.comment_id; -- 4階層目
```
<!-- --- -->
## 2-2-1 無理くり取得するなら
```SQL
SELECT * FROM Comments bug_id = 123;
```
　　　→　これの後に木構造を作成する
<!-- --- -->
## 2-2-2 
`INSERT`と`UPDATE`はよいよい……
```SQL
INSERT INTO Comments (bug_id, parent_id, author, comment_date, comment)
  VALUES (1234, 7, 23, CURRENT_TIMESTAMP, 'ありがとう!');

UPDATE Comments SET parent_id = 3 WHERE comment_id = 6;
```
`DELETE`はこわい！
```SQL
SELECT comment_id FROM Comments WHERE parent_id = 4; -- 5と6を返す
SELECT comment_id FROM Comments WHERE parent_id = 5; -- 何も返さない
SELECT comment_id FROM Comments WHERE parent_id = 6; -- 7を返す
SELECT comment_id FROM Comments WHERE parent_id = 7; -- 何も返さない
DELETE FROM Comments WHERE comment_id IN (7);
DELETE FROM Comments WHERE comment_id IN (5, 6);
DELETE FROM Comments WHERE comment_id = 4;
```
<!-- --- -->
## 2-2-2 【発展】`ON DELETE CASCADE`について
親が消されるとその子が自動で消されるテーブル定義ができる。
……なお、消されたくない子がいても対象なら自動で殺す。
```SQL
CREATE TABLE parent (
    id SERIAL PRIMARY KEY,
    name TEXT
);

CREATE TABLE child (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES parent(id) ON DELETE CASCADE,
    info TEXT
);
```
<!-- --- -->

## 2-2-3 隣接リストを用いていい場合①
* 隣接する親子の取得
* 列の挿入がシンプル
　→ アプリケーションが要求する操作がこれだけならGood

<!-- --- -->

## 2-2-3 隣接リストを用いていい場合①
SQL99以降は再帰クエリが使える。（現代なら大体OK）

*隣接リスト + 再帰クエリ*
<table>
  <tr>
    <th>
      Good
    </th>
    <th>
      Bad 
    </th>
  </tr>
  <tr>
  <td>
    <li> モデリングがスッキリしてる。</li>
    <li> `INSERT`と`UPDATE`が楽</li>
    <li> 子孫、先祖、N代目までの制限も楽。</li>
  </td>
  <td>
    <li> ちゃんとしないと無限ループ(循環参照)</li>
    <li> 深いツリーならパフォーマンス悪化</li>
    <li> 毎回ツリー取得コストがかかる</li>
  </td>
  </tr>
</table>

<!-- --- -->

## 2-2-3 再帰クエリ例
```SQL
WITH CommentTree
    (comment_id, bug_id, parent_id, author, comment, depth)
AS (
    SELECT *, 0 AS depth FROM Comments
    WHERE parent_id IS NULL
  UNION ALL
    SELECT c.*, ct.depth+1 AS depth FROM CommentTree ct
    JOIN Comments c ON ct.comment_id = c.parent_id
)
SELECT * FROM CommentTree WHERE bug_id = 1234;
```

<!-- --- -->

## 隣接リスト以外の対処方法
* 経路列挙(2-5-1)
* 入れ子集合(2-5-2)
* 閉包テーブル(2-5-3)

<!-- --- -->
## 2-5-1 経路列挙
```SQL
CREATE TABLE Comments (
  comment_id   SERIAL PRIMARY KEY,
  path         VARCHAR(1000),
  bug_id       BIGINT UNSIGNED NOT NULL,
  author       BIGINT UNSIGNED NOT NULL,
  comment_date DATETIME NOT NULL,
  comment      TEXT NOT NULL,
  FOREIGN KEY (bug_id) REFERENCES Bugs(bug_id),
  FOREIGN KEY (author) REFERENCES Accounts(account_id)
);
```

<!-- --- -->
## 経路列挙型の具体的なデータ

<table>
  <thead>
    <tr>
      <th>comment_id</th>
      <th>path</th>
      <th>bug_id</th>
      <th>author</th>
      <th>comment_date</th>
      <th>comment</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td>/1/</td>
      <td>101</td>
      <td>10</td>
      <td>2024-04-01 10:00</td>
      <td>このバグはまだ再現できます。</td>
    </tr>
    <tr>
      <td>2</td>
      <td>/2/</td>
      <td>101</td>
      <td>11</td>
      <td>2024-04-01 10:05</td>
      <td>同様の現象を確認しました。</td>
    </tr>
    <tr>
      <td>3</td>
      <td>/1/3/</td>
      <td>101</td>
      <td>12</td>
      <td>2024-04-01 10:10</td>
      <td>OSのバージョンを教えてください。</td>
    </tr>
    <tr>
      <td>4</td>
      <td>/1/3/4/</td>
      <td>101</td>
      <td>10</td>
      <td>2024-04-01 10:20</td>
      <td>macOS Sonoma 14.3 です。</td>
    </tr>
    <tr>
      <td>5</td>
      <td>/2/5/</td>
      <td>101</td>
      <td>13</td>
      <td>2024-04-01 10:25</td>
      <td>回避策としてキャッシュクリアも有効でした。</td>
    </tr>
  </tbody>
</table>
<!-- --- -->

## 2-5-1 経路列挙型の操作(データ取得)

`||`は連結、`%`は*的なワイルドカード
```SQL
SELECT *
FROM Comments AS c
WHERE '1/4/6/7/' LIKE c.path || '%' ;
```
```SQL
SELECT *
FROM Comments AS c
WHERE c.path LIKE '1/4/' || '%' ;
```
```SQL
SELECT c.author, COUNT(*)
FROM Comments AS c
WHERE c.path LIKE '1/4/' || '%'
GROUP BY c.author;
```
<!-- --- -->

## 2-5-1 経路列挙型の操作(INSERT)
```SQL
INSERT INTO Comments (bug_id, author, comment_date, comment)
  VALUES (1234, 23, CURRENT_TIMESTAMP, 'ありがとう!');

UPDATE Comments
  SET path =
    (SELECT x.path FROM (
      SELECT path FROM Comments WHERE comment_id = 7
    ) AS x) || LAST_INSERT_ID() || '/'
WHERE comment_id = LAST_INSERT_ID();
```
* パスの正確な形成がなされているか怖い
* `VARCHAR()`の長さは適切か？

<!-- --- -->
## 2-5-2 入れ子集合
nsleft：そのノードに「入ったとき」の通過番号
nsright：そのノードから「出たとき」の通過番号
```SQL
CREATE TABLE Comments (
  comment_id   SERIAL PRIMARY KEY,
  nsleft       INTEGER NOT NULL,
  nsright      INTEGER NOT NULL,
  bug_id       BIGINT UNSIGNED NOT NULL,
  author       BIGINT UNSIGNED NOT NULL,
  comment_date DATETIME NOT NULL,
  comment      TEXT NOT NULL,
  FOREIGN KEY (bug_id) REFERENCES Bugs (bug_id),
  FOREIGN KEY (author) REFERENCES Accounts(account_id)
);
```

<!-- --- -->
## 2-5-2 入れ子集合 データ例

<table>
  <thead>
    <tr>
      <th>comment_id</th>
      <th>nsleft</th>
      <th>nsright</th>
      <th>bug_id</th>
      <th>author</th>
      <th>comment</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td>1</td>
      <td>8</td>
      <td>101</td>
      <td>10</td>
      <td>このバグを確認しました。</td>
    </tr>
    <tr>
      <td>2</td>
      <td>2</td>
      <td>5</td>
      <td>101</td>
      <td>11</td>
      <td>再現条件を教えてください。</td>
    </tr>
    <tr>
      <td>4</td>
      <td>3</td>
      <td>4</td>
      <td>101</td>
      <td>12</td>
      <td>macOS 14.3 で発生しています。</td>
    </tr>
    <tr>
      <td>3</td>
      <td>6</td>
      <td>7</td>
      <td>101</td>
      <td>13</td>
      <td>こちらでも同様の事象が確認されました。</td>
    </tr>
  </tbody>
</table>

<!-- --- -->
## 2-5-2 入れ子集合でのデータ操作(データ取得)

```SQL
SELECT c2.*
FROM Comments AS c1
  INNER JOIN Comments AS c2-- C2: 先祖候補
    ON c1.nsleft BETWEEN c2.nsleft AND c2.nsright
WHERE c1.comment_id = 6;
```

```SQL
SELECT c2.*
FROM Comments AS c1
  INNER JOIN Comments as c2 --C2: 子孫候補
    ON c2.nsleft BETWEEN c1.nsleft AND c1.nsright
WHERE c1.comment_id = 4;
```
<!-- --- -->
## 2-5-2 入れ子集合(削除時の木構造変化)
ノードを削除すると削除対象の子が、親の子供になる
```SQL
-- この時点では depth は 4
SELECT c1.comment_id, COUNT(c2.comment_id) AS depth
FROM Comments AS c1
  INNER JOIN Comments AS c2
    ON c1.nsleft BETWEEN c2.nsleft AND c2.nsright
WHERE c1.comment_id = 7
GROUP BY c1.comment_id;

DELETE FROM Comments WHERE comment_id = 6; --ここで削除

-- depth は 3 になる（上とおんなじ）
SELECT c1.comment_id, COUNT(c2.comment_id) AS depth
FROM Comments AS c1
  INNER JOIN Comments AS c2
    ON c1.nsleft BETWEEN c2.nsleft AND c2.nsright
WHERE c1.comment_id = 7
GROUP BY c1.comment_id;
```
<!-- --- -->

## 2-5-2 入れ子集合(挿入)
あー、クソクソクソクソ。
```SQL
-- NS値8と9を入れるためにスペースを空ける
UPDATE Comments
  SET nsleft = CASE WHEN nsleft > 7 THEN nsleft+2 ELSE nsleft END,
      nsright = nsright+2
WHERE nsright >= 7;

-- コメント5の新しい子供を作成し、NS値に8と9を割り当てる
INSERT INTO Comments (nsleft, nsright, bug_id, author, comment_date, comment)
  VALUES (8, 9, 1234, 12, CURRENT_TIMESTAMP, '私もそう思います!');
```
<!-- --- -->
## 2-5-2 [場外乱闘]入れ子区間モデル
ノードの追加・削除・移動が頻繁
```
ルート:       [0.0 ---------------------- 1.0]
子A:             [0.1 ------ 0.4]
子B:                               [0.6 ---- 0.9]
```
<!-- --- -->

## 2-5-3 閉包テーブル
```SQL
CREATE TABLE Comments (
  comment_id   SERIAL PRIMARY KEY,
  bug_id       BIGINT UNSIGNED NOT NULL,
  author       BIGINT UNSIGNED NOT NULL,
  comment_date DATETIME NOT NULL,
  comment      TEXT NOT NULL,
  FOREIGN KEY (bug_id) REFERENCES Bugs(bug_id),
  FOREIGN KEY (author) REFERENCES Accounts(account_id)
);

CREATE TABLE TreePaths (
  ancestor    BIGINT UNSIGNED NOT NULL,
  descendant  BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (ancestor, descendant),
  FOREIGN KEY (ancestor) REFERENCES Comments(comment_id),
  FOREIGN KEY (descendant) REFERENCES Comments(comment_id)
);
```

<!-- --- -->
## 2-5-3 閉包テーブルのデータ例
<!-- 閉包テーブルのダミーデータ（HTML表示） -->

### 閉包テーブル
|データ|木構造|
|-|-|
|![]()|![]()|

<!-- --- -->
## 閉包テーブル（先祖・子孫抽出）
```SQL
SELECT c.*
FROM Comments AS c
  INNER JOIN TreePaths AS t ON c.comment_id = t.ancestor
WHERE t.descendant = 6;
```
```SQL
SELECT c.*
FROM Comments AS c
  INNER JOIN TreePaths AS t ON c.comment_id = t.descendant
WHERE t.ancestor = 4;
```
<!-- --- -->
## 閉包テーブル（挿入）
```SQL
INSERT INTO Comments (comment_id, bug_id, author, comment_date, comment)
  VALUES (8, 1234, 23, CURRENT_TIMESTAMP, '確認お願いします');

INSERT INTO TreePaths (ancestor, descendant)
  SELECT t.ancestor, 8
  FROM TreePaths AS t
  WHERE t.descendant = 5
 UNION ALL
  SELECT 8, 8;
```
<!-- --- -->
## 閉包テーブル（削除抽出）
コメント7の子孫コメントを消す
```SQL
DELETE FROM TreePaths WHERE descendant = 7;
```
サブツリー自体を殺す
```SQL
DELETE FROM TreePaths
WHERE descendant IN (SELECT x.id FROM
                       (SELECT descendant AS id
                        FROM TreePaths
                        WHERE ancestor = 4) AS x);
```
<!-- --- -->
## [場外乱闘]そもそもRDBで木構造だぁ？！

* グラフDB　Ex)Neo4j
* **ドキュメント指向DB** Ex)MongoDB
　　→ JSONで殴れ！

<!-- --- -->

## [場外乱闘]そもそもRDBで木構造だぁ？！
```JSON
{
  "_id": ObjectId("..."),
  "article_id": ObjectId("..."),
  "author": "alice",
  "text": "この記事、面白いですね！",
  "timestamp": ISODate("2025-04-02T10:00:00Z"),
  "replies": [
    {
      "author": "bob",
      "text": "ほんとそれ！",
      "timestamp": ISODate("2025-04-02T10:05:00Z"),
      "replies": [
        {
          "author": "charlie",
          "text": "同感。",
          "timestamp": ISODate("2025-04-02T10:07:00Z"),
          "replies": []
        }
      ]
    },
    {
      "author": "dan",
      "text": "でもちょっと偏ってるかも",
      "timestamp": ISODate("2025-04-02T10:06:00Z"),
      "replies": []
    }
  ]
}
```
<!-- --- -->
## [場外乱闘]MongoDB(挿入)

```javascript
db.comments.insertOne({
  article_id: ObjectId("..."),
  author: "eve",
  text: "新しいコメントです！",
  timestamp: new Date(),
  replies: []
});
```
```javascript
db.comments.updateOne(
  { _id: ObjectId("...") },  // 親コメントの _id
  { $push: {
      "replies": {
        author: "frank",
        text: "返信します！",
        timestamp: new Date(),
        replies: []
      }}});
```
<!-- --- -->

  ## [場外乱闘]MongoDB(更新・抽出)
```javascript
db.tree.updateOne(
  { name: "Node A" },
  { $pull: { children: { name: "Node A-2" } } }
);
```
```javascript
db.comments.find({ article_id: ObjectId("...") })
  .sort({ timestamp: 1 });
```

<!-- --- -->
  ## [場外乱闘]MongoDB(削除)
```SQL
db.comments.deleteOne({ _id: ObjectId("...") });
```
```SQL
db.comments.updateOne(
  { _id: ObjectId("...") },
  { $pull: { replies: { text: "返信します！" } } }
);
```
<!-- --- -->
## 木構造データを扱うには


<!-- --- -->
## ナイーブツリーまとめ(紹介した木構造まとめ)

| モデル名 | 概要 |
|----------|------|
| 隣接リスト | `parent_id` を持つ構造。基本形 |
| 再帰クエリ | SQLのCTEでツリーを辿る |
| 入れ子集合 | `left/right` 番号を振って階層管理 |
| 閉包テーブル | 全ての親子関係を列挙 |
| MongoDB | JSONをネストして保持（NoSQL） |

<!-- --- -->
## ナイーブツリーまとめ(長所短所)

| モデル | 長所 | 短所 |
|--------|------|------|
| 隣接リスト | 実装が簡単 | 再帰が必要、JOINが増える |
| 再帰クエリ | SQLだけで完結 | パフォーマンスに課題、DB依存 |
| 入れ子集合 | ソート・取得が速い | 挿入・更新時に再計算が必要 |
| 閉包テーブル | 子孫・先祖が高速に取得可 | 書き込み時に行が多く追加される |
| MongoDB | ネストで直感的、一括取得可 | 深い階層の操作が難しい、サイズ制限あり |

<!-- --- -->
## ナイーブツリーまとめ(モデル選定ポイント)

| 要件 | 推奨モデル |
|------|------------|
| 実装が簡単 | 隣接リスト |
| 再帰を避けたい | 閉包テーブル / MongoDB |
| 並び順が重要 | 入れ子集合 |
| フルSQLで完結させたい | 再帰クエリ（CTE） |
| 一括取得したい | MongoDB（ネストドキュメント） |

　→ これをサイト内の要求に合わせていい感じに使おうぜ

<!-- --- -->
## ナイーブツリーまとめ(アンチパターンのヒヤリハット)
* 「今ツリーでは深さを何階層までサポートする？」
    →再帰クエリとか使えば？手はあるよ
* 「ツリー型のデータ構造を扱うコードなんて扱いたくねぇ！」
    →詰まっているなら別の方法でのアプローチを検討
* 「ツリーの中で孤児になったデータを清掃するためのスクリプトを……」
    →`CASCASDE`とか他の方法ならいい感じにいけるんでは？

<!-- --- -->
# 第3章 IDリクワイアド（とりあえずID）
<!-- --- -->

## 第3章 IDリクワイアド（とりあえずID）
- **目的**: 主キーの規約確立
- **アンチパターン**: 全てのテーブルにid列　
要約: 脳死でIDつけんじゃねぇ、ほんとに必要か考えるんだ。

<!-- --- -->



<!-- --- -->

## 第4章 キーレスエントリ（外部キー嫌い）
- **目的**: DBアーキテクチャの単純化
- **アンチパターン**: 外部キー制約を使わない
- **解決策**: 外部キー制約を宣言して整合性確保

<!-- --- -->

## 1〜4章のまとめハンズオン

### クイズ: 与太郎「ECのテーブル構成できたよ！」
簡単なECを想定したテーブル構成にツッコミどころがあるので、
これを確認してアンチパターンを指摘し、
改修をするよう納得の行く説明をしてください。
<table>
  <tr>
    <th>DB名</th>
    <td>ec1</td>
  </tr>
  <tr>
    <th>テーブル構成SQLファイル</th>
    <td>/init/sql/ec1_setup.sql</td>
  </tr>
</table>

[注]作者がChat-GPTと一緒に作成しました。
#### Hint: GPTChat  + Mermaidを活用しよう
















<!-- --- -->

## 第5章 EAV（エンティティ・アトリビュート・バリュー）
- **目的**: 可変属性のサポート
- **アンチパターン**: 汎用属性テ3ーブルの使用
- **解決策**:
  - 継承パターンの利用
  - サブタイプのモデリング

<!-- --- -->

## 第6章 ポリモーフィック関連
- **目的**: 複数の親テーブル参照
- **アンチパターン**: 二重目的の外部キー
- **解決策**:
  - リファレンス逆転
  - 交差テーブル
  - 共通親テーブル

<!-- --- -->

## 第7章 マルチカラムアトリビュート（複数列属性）
- **目的**: 複数値の属性格納
- **アンチパターン**: 複数列を定義
- **解決策**: 従属テーブルの作成

<!-- --- -->

## 第8章 メタデータトリブル（メタデータ大増殖）
- **目的**: スケーラビリティの向上
- **アンチパターン**: テーブルや列の複製
- **解決策**:
  - パーティショニング
  - 正規化

<!-- --- -->

## 次回: II部 データベース物理設計のアンチパターン
- 浮動小数点誤差
- 値の列定義の固定化
- メディアファイル保存の誤り


