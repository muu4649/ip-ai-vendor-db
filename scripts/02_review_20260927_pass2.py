# -*- coding: utf-8 -*-
"""
2026-09-27 レビュー2巡目：1工程のまま残った66社を紹介文・公式情報と再照合し、
明記されている機能だけを副工程として追加する。記録は logs/20260927_review.csv に追記。
"""
import csv, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA, LOG = ROOT / "data", ROOT / "logs" / "20260927_review.csv"
TODAY = "2026-09-27"

ADD = [
 ("Patently", ["03", "07"], "紹介文・patently.com：検索・ドラフト・出願・分析を一つにまとめたプラットフォーム"),
 ("Leegal AI", ["03", "12"], "紹介文・leegal.ai：先行技術調査からFTO、明細書までをエージェントが連続処理"),
 ("PatSeer Technologies", ["07"], "紹介文・patseer.com：特許検索・分析プラットフォーム、分析テンプレート"),
 ("NLPatent", ["12"], "紹介文・nlpatent.com：FTOでの利用"),
 ("anovIP", ["12"], "紹介文・anovip.com：FTOとポートフォリオ分析"),
 ("IP8", ["07"], "紹介文・ip8.ai：ポートフォリオを仕分ける分析"),
 ("Edge", ["06"], "紹介文・tryedge.io：図面エディタを統合"),
 ("PatentPal", ["06"], "紹介文・patentpal.com：フローチャート・ブロック図を生成"),
 ("IPRally", ["07"], "iprally.com：AI Patent Search, Review & Classification"),
 ("Ambercite", ["07"], "紹介文・ambercite.com：引用ネットワーク分析、特許関係マップ"),
 ("Huski.ai", ["11"], "紹介文・huski.ai：商標侵害の早期検知"),
 ("DrugPatentWatch", ["13"], "紹介文・drugpatentwatch.com：Orange Book/Purple Bookと訴訟データを結合"),
]

def main():
    vendors = list(csv.DictReader((DATA/"vendors.csv").open(encoding="utf-8-sig")))
    vid = {v["name"]: v["vendor_id"] for v in vendors}
    p = DATA / "vendor_categories.csv"
    rows = list(csv.DictReader(p.open(encoding="utf-8-sig")))
    have = {(r["vendor_id"], r["cat_id"]) for r in rows}
    log = []
    for name, cats, src in ADD:
        for c in cats:
            k = (vid[name], c)
            if k in have:
                continue
            rows.append({"vendor_id": k[0], "cat_id": c, "role": "副", "source": src, "checked_at": TODAY})
            have.add(k)
            log.append((name, "追加（2巡目）", c, src))
    rows.sort(key=lambda r: (r["vendor_id"], r["cat_id"]))
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["vendor_id", "cat_id", "role", "source", "checked_at"])
        w.writeheader(); w.writerows(rows)
    with LOG.open("a", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(log)
    print(f"2巡目 追加 {len(log)}件 / vendor_categories {len(rows)}行")

if __name__ == "__main__":
    main()
