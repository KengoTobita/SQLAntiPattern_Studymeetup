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

[注]この章、サンプルDB使ってねぇ。

<!-- --- -->
## 第2章 ナイーブツリー（素朴な木）


<!-- --- -->
<!-- --- -->
<!-- --- -->
<!-- --- -->
<!-- --- -->
<!-- --- -->
<!-- --- -->
<!-- --- -->
<!-- --- -->
<!-- --- -->

## 第3章 IDリクワイアド（とりあえずID）
- **目的**: 主キーの規約確立
- **アンチパターン**: 全てのテーブルにid列
- **解決策**: 状況に応じて自然キーや複合キーを検討

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
- **アンチパターン**: 汎用属性テーブルの使用
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


