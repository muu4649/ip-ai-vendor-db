# -*- coding: utf-8 -*-
"""
データベースを引くためのコマンド。

    python3 scripts/query.py                 使い方を表示
    python3 scripts/query.py stats           全体の集計
    python3 scripts/query.py cats            カテゴリ一覧と社数
    python3 scripts/query.py find 明細書      名前・紹介文・展示内容を横断検索
    python3 scripts/query.py cat 04          カテゴリIDで絞る
    python3 scripts/query.py region 日本      地域で絞る
    python3 scripts/query.py mcp             MCP／AIエージェント連携に対応
    python3 scripts/query.py new             2026年の新規・大型更新
    python3 scripts/query.py onprem          オンプレミス／ローカル実行
    python3 scripts/query.py booth           フェア出展社をブース順
    python3 scripts/query.py excluded        マップ対象外の機関・企業
    python3 scripts/query.py sql "SELECT ..."  任意のSQL

    末尾に --csv を付けるとCSVで出力する（他のツールに渡す用）。
"""

import csv
import pathlib
import sqlite3
import sys

DBFILE = pathlib.Path(__file__).resolve().parents[1] / "db" / "ipai.sqlite"
BASE = """SELECT name AS 社名, region AS 地域, categories AS 工程,
                 CASE is_mcp WHEN 1 THEN 'MCP' ELSE '' END AS 連携,
                 CASE is_new_2026 WHEN 1 THEN '2026' ELSE '' END AS 更新,
                 ifnull(booth,'') AS ブース, ifnull(deployment,'') AS 提供形態, url AS URL
            FROM v_vendor_full"""


def show(rows, cols, as_csv=False):
    if as_csv:
        cw = csv.writer(sys.stdout)
        cw.writerow(cols)
        cw.writerows(rows)
        return
    if not rows:
        print("該当なし")
        return
    w = [max(len(str(c)), *(len(str(r[i])) for r in rows)) for i, c in enumerate(cols)]
    w = [min(x, 46) for x in w]

    def cut(s, n):
        s = str(s)
        return s if len(s) <= n else s[: n - 1] + "…"

    print(" | ".join(cut(c, w[i]).ljust(w[i]) for i, c in enumerate(cols)))
    print("-+-".join("-" * x for x in w))
    for r in rows:
        print(" | ".join(cut(v, w[i]).ljust(w[i]) for i, v in enumerate(r)))
    print(f"\n{len(rows)}件")


def main():
    if not DBFILE.exists():
        sys.exit("db/ipai.sqlite がありません。先に python3 scripts/build.py を実行してください。")
    args = [a for a in sys.argv[1:] if a != "--csv"]
    as_csv = "--csv" in sys.argv
    if not args:
        print(__doc__)
        return

    con = sqlite3.connect(DBFILE)
    cmd, arg = args[0], (args[1] if len(args) > 1 else "")

    if cmd == "stats":
        for title, q in [
            ("地域別", "SELECT region AS 地域, count(*) AS 社数 FROM vendors "
                       "WHERE status='active' GROUP BY region ORDER BY 社数 DESC"),
            ("フェーズ別（延べ）",
             "SELECT c.phase AS フェーズ, count(*) AS 延べ社数 FROM vendor_categories vc "
             "JOIN categories c ON c.cat_id=vc.cat_id GROUP BY c.phase ORDER BY min(c.sort)"),
            ("属性", "SELECT 'MCP対応' AS 区分, count(*) AS 社数 FROM vendors WHERE is_mcp=1 "
                    "UNION ALL SELECT '2026年更新', count(*) FROM vendors WHERE is_new_2026=1 "
                    "UNION ALL SELECT 'フェア出展', count(DISTINCT vendor_id) FROM exhibitions "
                    "UNION ALL SELECT '提供形態を確認済', count(*) FROM vendors WHERE deployment<>'' "
                    "UNION ALL SELECT '合計', count(*) FROM vendors WHERE status='active'"),
        ]:
            cur = con.execute(q)
            print(f"■ {title}")
            show(cur.fetchall(), [d[0] for d in cur.description])
            print()
        return

    q, p = None, ()
    if cmd == "cats":
        q = ("SELECT c.cat_id AS ID, c.phase AS フェーズ, c.title AS 工程, "
             "count(vc.vendor_id) AS 社数, c.subtitle AS 説明 FROM categories c "
             "LEFT JOIN vendor_categories vc ON vc.cat_id=c.cat_id "
             "GROUP BY c.cat_id ORDER BY c.sort")
    elif cmd == "find":
        q = (BASE + " WHERE name LIKE ?1 OR description LIKE ?1 OR categories LIKE ?1 "
                    "OR ifnull(exhibit_name,'') LIKE ?1 OR ifnull(exhibit_note,'') LIKE ?1 "
                    "OR ifnull(deployment,'') LIKE ?1 ORDER BY name")
        p = (f"%{arg}%",)
    elif cmd == "cat":
        q = (BASE + " WHERE cat_ids LIKE ?1 ORDER BY name")
        p = (f"%{arg}%",)
    elif cmd == "region":
        q = BASE + " WHERE region=? ORDER BY name"
        p = (arg,)
    elif cmd == "mcp":
        q = BASE + " WHERE is_mcp=1 ORDER BY name"
    elif cmd == "new":
        q = BASE + " WHERE is_new_2026=1 ORDER BY region, name"
    elif cmd == "onprem":
        q = (BASE + " WHERE deployment LIKE '%オンプレ%' OR deployment LIKE '%ローカル%' "
                    "OR deployment LIKE '%国内サーバー%' ORDER BY name")
    elif cmd == "booth":
        q = ("SELECT e.booth AS ブース, v.name AS 社名, e.exhibit_name AS 展示, "
             "v.region AS 地域, v.url AS URL FROM exhibitions e "
             "JOIN vendors v ON v.vendor_id=e.vendor_id ORDER BY e.booth")
    elif cmd == "excluded":
        q = "SELECT name AS 名称, kind AS 区分, reason AS 理由 FROM excluded ORDER BY kind, name"
    elif cmd == "sql":
        q = arg
    else:
        sys.exit(f"不明なコマンド: {cmd}\n\n{__doc__}")

    cur = con.execute(q, p)
    show(cur.fetchall(), [d[0] for d in cur.description], as_csv)


if __name__ == "__main__":
    main()
