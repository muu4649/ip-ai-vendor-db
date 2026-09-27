# 知財AIベンダーDB

生成AI・AIを組み込んだ製品／サービスを提供する知財領域のベンダーを、いつでも取り出せる形で保管するデータベース。

**現在の内容**：152社（うち買収済み1社を除く現役） / 18工程・381の工程割り当て / 2026年知財・情報フェア出展86社 / 対象外24機関（2026年9月27日時点）

---

## Webアプリ（Streamlit）

名鑑は Streamlit Community Cloud で公開する。アプリは `data/*.csv` を直接読み、`scripts/build.py` と同じ検査を通してから表示するので、**CSVを直して main に push すれば、公開中のアプリもそのまま更新される**。データに不整合があれば、アプリは表示を止めてエラーを出す。

できること：キーワード検索、属性（フェア出展・MCP対応・2026年更新・オンプレミス）・地域・工程での絞り込み、工程ごとの根拠の表示、工程別の社数と工程×地域の集計グラフ、フェア出展社のブース順一覧、絞り込み結果のCSV／Excel／JSONダウンロード。

ローカルで動かす：

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

無料枠のため、12時間アクセスがないとスリープし、次に開いた人は起動まで数十秒待つ。

push のたびに GitHub Actions（`.github/workflows/test.yml`）が、公開環境と同じ Python 3.12／3.13 でデータの検査とアプリの起動テスト（`tests/test_app.py`）を行う。手元と公開環境では依存パッケージの版が違うことがあるため（2026年9月27日、Altair と narwhals の組み合わせで公開版だけが TypeError になった）、**CIが赤いときは公開中のアプリも壊れている可能性がある**。

---

## すぐ使う

### Excelで開く

```
export/vendors.xlsx
```

1行1社。フィルタと折り返しを設定済み。列は社名・地域・国・提供形態・工程・ブース番号・URL・紹介文。CSVがよければ `export/vendors_full.csv`（UTF-8 BOM付きなのでExcelで文字化けしない）。

### コマンドで引く

```bash
python3 scripts/query.py stats           # 全体の集計
python3 scripts/query.py cats            # 18工程の一覧と社数
python3 scripts/query.py find 明細書      # 名前・紹介文・展示内容を横断検索
python3 scripts/query.py cat 04          # 工程IDで絞る
python3 scripts/query.py region 日本      # 地域で絞る
python3 scripts/query.py mcp             # MCP／AIエージェント連携に対応
python3 scripts/query.py new             # 2026年の新規・大型更新
python3 scripts/query.py onprem          # オンプレミス／ローカル実行
python3 scripts/query.py booth           # フェア出展社をブース番号順
python3 scripts/query.py excluded        # マップ対象外の機関・企業
```

末尾に `--csv` を付けると、そのまま他のツールに渡せるCSVで出る。

### SQLで引く

```bash
sqlite3 db/ipai.sqlite
```

```sql
-- 日本の明細書作成AIで、フェアに出展していた社
SELECT name, booth, deployment, url FROM v_vendor_full
 WHERE region='日本' AND cat_ids LIKE '%04%' AND booth IS NOT NULL;

-- 工程をまたいでいる社（プラットフォーム型）の上位
SELECT name, cat_count, categories FROM v_vendor_full
 ORDER BY cat_count DESC LIMIT 10;

-- 中間対応（05）に対応している社を、代表工程か対応工程かで分けて見る
SELECT v.name, vc.role, vc.source FROM vendor_categories vc
  JOIN vendors v ON v.vendor_id = vc.vendor_id
 WHERE vc.cat_id = '05' AND v.status = 'active' ORDER BY vc.role, v.name;
```

任意のSQLはコマンドからも実行できる。

```bash
python3 scripts/query.py sql "SELECT region, count(*) FROM vendors GROUP BY region"
```

### オフライン用の静的版

`web/ipai_finder.html` は、サーバーなしでブラウザだけで動く版。データを更新したら次を実行してから開く。

```bash
cp export/data.js web/data.js
```

---

## フォルダ構造

```
知財AIベンダーDB/
├── data/                       ← ここがマスター。編集するのはこの5ファイルだけ
│   ├── vendors.csv             ベンダー本体（153行、うち1社は買収済み）
│   ├── categories.csv          18工程の定義
│   ├── vendor_categories.csv   どの社がどの工程か（多対多・381行、主/副と根拠つき）
│   ├── exhibitions.csv         展示会の出展記録（86行）
│   └── excluded.csv            掲載基準から外した24機関・企業
├── db/
│   └── ipai.sqlite             自動生成。手で触らない
├── export/                     自動生成。配布・転用はここから
│   ├── vendors.xlsx            Excel用
│   ├── vendors_full.csv        フラットCSV
│   ├── exhibitors_2026.csv     フェア出展社のみ（ブース順）
│   ├── vendors.json            Webツール・記事生成用
│   └── data.js                 Artifact差し替え用
├── scripts/
│   ├── build.py                CSV → SQLite → export一式を再生成
│   ├── query.py                上記のコマンド群
│   ├── 00_migrate_from_drafts.py        初回移行（再実行不要）
│   ├── 01_review_20260927.py            工程の網羅化・URL全件修正（実行済み）
│   └── 02_review_20260927_pass2.py      同2巡目（実行済み）
├── logs/
│   └── 20260927_review.csv     見直しで何をどう変えたかの記録（160件、根拠つき）
├── streamlit_app.py            Webアプリ本体（Streamlit Community Cloudで公開）
├── requirements.txt            アプリの依存パッケージ（版を固定）
├── .streamlit/config.toml      アプリの配色設定
├── web/                        オフライン用の静的版
│   ├── ipai_finder.html        検索ツール本体
│   └── data.js                 export/data.js のコピー
├── assets/                     カオスマップ画像と記事の保管
└── README.md
```

**原則**：`data/*.csv` だけが手で書き換える場所。`db/` と `export/` は `build.py` がいつでも作り直す。

---

## 更新のしかた

### 1社追加する

1. `data/vendors.csv` に1行足す。`vendor_id` は既存の最大値+1（`V154` など）
2. `data/vendor_categories.csv` に、その `vendor_id` と工程IDの組を足す（複数可）。代表的な工程は `role=主`、それ以外に対応している工程は `role=副` とし、`source` に確認した根拠（URLや資料名）を書く
3. 展示会で見つけた社なら `data/exhibitions.csv` にも足す
4. `python3 scripts/build.py` を実行

`build.py` は投入前に検査する。IDの重複、社名の重複、存在しない工程IDへの紐付けがあれば**出力せずに止まる**ので、壊れたデータがexportに流れることはない。URL未確認や紹介文なしは警告だけ出して続行する。

### 半年ごとの棚卸し

```bash
python3 scripts/query.py stats                    # 前回との差を見る
python3 scripts/query.py sql "SELECT name, updated_at FROM vendors ORDER BY updated_at"
```

- 買収・統合されたベンダーは `status` を `merged` にし、`note` に統合先を書く（行は消さない。過去版との比較ができなくなる）
- サービス終了は `status` を `closed`
- `v_vendor_full` は `status='active'` だけを返すので、exportからは自動的に外れる
- `is_new_2026` は翌版で `is_new_2027` 相当に読み替える。列名を変えるより、`first_listed` と `updated_at` で判断するほうが壊れにくい

### 掲載基準を変えたとき

`data/excluded.csv` に理由つきで移す。逆に、対象外だった機関がAI製品を出したら `vendors.csv` に移す。どちらも履歴として残る形にしてある。

---

## データ辞書

### vendors.csv

| 列 | 内容 |
|---|---|
| vendor_id | `V001` 形式。一度振ったら変えない |
| name | 提供企業・団体名。製品名ではない |
| region | 日本 / 北米 / 欧州 / アジア・他 |
| country | 国名 |
| url | 公式サイト。2026年9月27日に全件の到達を確認済み（403はボット遮断でサイト自体は存在） |
| description | 一行紹介。製品名を文中に含める |
| deployment | クラウド / オンプレミス / ローカル実行など。**空欄は未確認**の意味 |
| is_mcp | MCP・AIエージェント連携に対応していれば1 |
| is_new_2026 | 2026年の新規参入または大型アップデートなら1 |
| status | active / merged / closed |
| first_listed | 初掲載の版（`2026-09`） |
| updated_at | 最終確認日 |
| note | 補足。統合先など |

### vendor_categories.csv

| 列 | 内容 |
|---|---|
| vendor_id / cat_id | どの社がどの工程に対応しているか |
| role | **主** = カオスマップに配置した代表的な工程 / **副** = 提供を確認できたそれ以外の工程 |
| source | 確認した根拠。公式サイトのURL、プレスリリース、出展社情報など |
| checked_at | 確認日 |

カオスマップを描くときは `role=主` だけを使えば従来どおりの配置になり、検索では主副の両方を使う。Webツールでは主を塗り、副を線で表示している。

### categories.csv

18工程。`phase` は 創出 / 権利化 / 管理・保護 / 活用・紛争 / 実装・体制 の5段階で、知財業務の時系列に沿う。`sort` が表示順。17（特許調査サービス）と18（知財AX導入支援）は日本市場に固有の層で、グローバル版のカオスマップには存在しない。

### exhibitions.csv

展示会ごとの記録。`event` と `year` で版を分けるので、2027年のフェアは同じファイルに追記すればよい。`booth` が空欄なのは出展は確認できたがブース番号が取れなかった社。

---

## 掲載基準

**AI・生成AIを組み込んだ製品またはサービスを、公開情報で確認できるベンダーに限る。**

この基準から外れるものは `data/excluded.csv` に理由つきで記録している。公的機関（INPIT、WIPOなど）、業界団体、知財教育機関、AI活用を公表していない調査会社・翻訳会社・事務所が該当する。除外はAI搭載の有無という一点の判定であり、事業の価値や実務上の重要性を評価したものではない。

判定は公開情報にもとづく機械的なものなので、AI活用を公表していないだけで内部的に使っている事業者もありうる。

---

## このデータから作ったもの

| 成果物 | 場所 |
|---|---|
| カオスマップ 統合版・グローバル版・日本版 | `assets/*.png` `.svg` |
| 記事「生成AI×知財ベンダーカオスマップ 2026年9月版」 | 公開準備中（原稿はローカルの `assets/` にのみ保管し、リポジトリには含めていない） |
| 記事「生成AIサービスを目的に知財情報フェアをあるくなら」 | 同上 |
| Webアプリ「知財AIベンダー名鑑」 | `streamlit_app.py`（Streamlit Community Cloudで公開） |
| 静的版の検索ツール | `web/ipai_finder.html` |

カオスマップと記事の生成スクリプトは作成者のローカル環境に残してある。データは本DBに移行済みなので、再生成するなら `export/vendors.json` を読む形で組み直せる。

---

## 他のカオスマップとの関係

同じ2026年知財・情報フェアを対象に、早崎聡氏が[全出展社169社（151組織）・215製品を11カテゴリで整理したカオスマップ](https://note.com/satoshi_hayasaki/n/nce4dd531cf31)を公開している（2026年9月17日）。母集団が違うので、数字を直接比べても意味がない。

| | 早崎氏 | 本DB |
|---|---|---|
| 母集団 | フェアの全出展社 | AI・生成AIを搭載したベンダー |
| 対象 | 知財ソリューション全般 | AI製品を持つもののみ |
| 範囲 | フェア出展社のみ | フェア出展86社＋フェア外67社 |
| 含むもの | 公的機関・団体・海外代理人・大学・自治体 | 含まない（excluded.csvに記録） |
| 出典 | イベントポータルのAPI（網羅的） | 出展社情報＋各社公表情報（検証的） |

フェアの出展社を漏れなく把握したいなら早崎氏のマップ、AI製品で絞って比較検討したいなら本DB、という使い分けになる。

**この突合で3社の漏れが見つかった**（Dolcera、Elevate Services、TRIART）。いずれも主催者の出展社紹介文にAIへの言及がなく、社名だけでは判断できずに落としていたもので、各社サイトを確認して2026年9月18日に追加した。**出展社紹介文だけを見て判定すると漏れる**という教訓なので、次版では社名しか情報のない出展社を個別に調べる工程を必ず入れる。

---

## 2026年9月27日の見直し

サマリアが「特許検索」の1工程にしか登録されていないという指摘を受け、全件を点検した。初版は**カオスマップ上の配置＝代表的な機能1〜2個**だけで工程を登録しており、複数の機能を持つベンダーの対応範囲が大きく欠けていた。

| 項目 | 見直し前 | 見直し後 |
|---|---|---|
| 工程の割り当て | 252件 | 381件（追加131・削除2） |
| 1工程だけの社 | 101社 | 54社（翻訳・商標・契約管理など本当に単機能のもの） |
| サマリア | 特許検索のみ | 9工程（発明創出・発明届出・検索・明細書・拒絶理由対応・分析・権利維持判断・クリアランス・係争対応） |
| 存在しないドメインのURL | 14件 | 0件 |
| パス違いのURL（404） | 4件 | 0件 |

誤って登録していた工程も2件あった（ASUとユアサポの「中間対応」。いずれも該当機能を確認できず削除）。Specifioは「Spellbook傘下」と書いていたが、実際は2026年2月時点でPaximalに買収されていたため訂正し、`status=merged` にした。

変更はすべて `logs/20260927_review.csv` に根拠つきで残している。URLは推測で入れたものが混じっていたため、今後は**到達確認できたURLしか入れない**。

---

## 出典

各社公式サイト・プレスリリース、2026 知財・情報フェア＆コンファレンス（2026年9月16〜18日・東京ビッグサイト東3ホール）出展社情報、各社の資金調達・買収に関する一次発表。

機能の実効性は検証していない。紹介文に含まれる「最短30分」「4,000万ドル調達」などの数値はいずれも各社の公表値である。

整理：上村侑太郎（LeXi/Vent）
