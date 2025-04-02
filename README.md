# SQLAntiPattern_Studymeetup
「SQLアンチパターン」の勉強会資料。
スライド、図、コードなどを管理。

## ディレクトリ構成
```sh
.
├── docker-compose.yml # 本体
│
├── init # サンプルデータベースの初期化SQL
│   └── setup.sql
│
├── marp  # Marp形式のスライド
│   ├── intro.md
│   ├── part1.md
│   ├── part2.md
│   ├── part3.md
│   └── part4.md
│
├── mermaid # ER図関連
│   ├── erDiagram.png
│   └── sample_database.mmd
│
├── pyapp # Python関係
│   ├── Dockerfile
│   ├── generate_fake_data.py
│   └── requirements.txt
│
├── README.md
│
└── sql_files　# 勉強会で使うSQLファイル
    ├── ch01
    └──　......
```

## 参考書籍
<img src=https://www.oreilly.co.jp/books/images/picture_large978-4-87311-589-4.jpeg width=200>

公式サイトでSQLファイルなどの参考コードなどがダウンロード可能です。<br>
URL: https://www.oreilly.co.jp/books/9784873115894/

## DBのID・Password
書籍公式のサンプルデータベースを構築しておきました。<br>
書籍理解のための実行などで使用してください。<br>
```
User: user 
Pass: pass 
Port: 5432
```
|データベース名|内容|
|-|-|
|antipat|書籍公式のサンプルデータベース|
|ec1|第一章 前半まとめクイズ用|

## 実行手順
私のPCはUbuntuなのでMac特有の事柄は感知しません。


1. docker composeで環境を建てる
    ```
    docker compose up -d
    ```
1. DBコンテナに入り、データベースやSQLファイルの確認をする
    *PostgreSQLのdockerコンテナ内に入る*
    ```bash
    docker container exec -it sql_study_postgres-db /bin/bash
    cd sql_files # SQLファイルはここに
    ```

    *SQLファイル実行(シェルで)*
    ```bash
    psql -f {SQLファイル} -U user -d {DB名} 
    ```
    *SQLファイル実行(PostgreSQLインタラクティブシェルで)*
    ```sql
    \i {SQLファイル}
    ```
    *PosgreSQLインタラクティブシェル*
    ```bash
    psql -U user -d {DB名}
    ```

    | コマンド   | 説明                                      |
    |------------|-------------------------------------------|
    | \l         | データベース一覧を表示                    |
    | \c DB名    | 指定したデータベースに接続                |
    | \dt        | テーブル一覧を表示                        |
    | \d テーブル名 | テーブルの定義（スキーマ）を表示        |
    | \di        | インデックス一覧を表示                    |
    | \dv        | ビュー一覧を表示                          |
    | \df        | 関数一覧を表示                            |
    | \dn        | 名前空間（スキーマ）一覧を表示            |
    | \du        | ユーザー一覧を表示                        |
    | \e         | 外部エディタを開く（SQL文の編集）         |
    | \q         | `psql` を終了                             |
    | \?         | `psql` のヘルプ（使用可能なコマンド一覧） |
    | \x         | 拡張表示のオン/オフ切り替え（見やすく表示）|

## Marmaidについて
テーブル構成の可視化でMarmaidを使用しています。<br>
関連ファイルを`./marmaid`に転がしておきます。<br>
必要に応じてLiveEditerで表示してください<br>

Marmaid Live Editer: https://mermaid-js.github.io/mermaid-live-editor/