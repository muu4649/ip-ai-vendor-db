# -*- coding: utf-8 -*-
"""
初回移行スクリプト（1回だけ実行すればよい）

_drafts に散っていた Python データを data/*.csv に正規化する。
以後は data/*.csv がマスターであり、このスクリプトを再実行する必要はない。
"""

import csv
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DRAFTS = ROOT.parent / "_drafts"
DATA = ROOT / "data"


def load(fname, mod):
    spec = importlib.util.spec_from_file_location(mod, DRAFTS / fname)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


D = load("20260917_1500_chaosmap2026H2_data_v3.py", "d3")
V = load("20260917_1410_chaosmap2026H2_vendorinfo_v2.py", "v2")
X = load("20260917_1600_pifc2026_exhibitors_v1.py", "x1")

REGION = {
    "JP": ("日本", "日本"), "US": ("北米", "米国"), "CA": ("北米", "カナダ"),
    "UK": ("欧州", "英国"), "FR": ("欧州", "フランス"), "DE": ("欧州", "ドイツ"),
    "NL": ("欧州", "オランダ"), "SE": ("欧州", "スウェーデン"), "FI": ("欧州", "フィンランド"),
    "BE": ("欧州", "ベルギー"), "LU": ("欧州", "ルクセンブルク"), "DK": ("欧州", "デンマーク"),
    "ES": ("欧州", "スペイン"), "SG": ("アジア・他", "シンガポール"), "KR": ("アジア・他", "韓国"),
    "CN": ("アジア・他", "中国"), "IN": ("アジア・他", "インド"), "AU": ("アジア・他", "オーストラリア"),
    "IL": ("アジア・他", "イスラエル"),
}
PHASE = {0: "創出", 1: "権利化", 2: "管理・保護", 3: "活用・紛争", 4: "実装・体制"}

# 提供形態が公開情報で確認できるもののみ記入する（空欄＝未確認）
DEPLOY = {
    "トランスエヌ": "オンプレミス",
    "アイビーリサーチ": "ローカル実行",
    "ユアサポ": "クラウド（生成物はローカル保存）",
    "AIVisor": "クラウド（国内サーバー完結）",
    "DeepIP": "クラウド／オンプレミス",
    "Genzo AI": "クラウド",
    "aiip": "クラウド",
    "Solve Intelligence": "クラウド",
    "Patlytics": "クラウド",
    "パテント・インテグレーション": "クラウド（MCP接続可）",
    "AI Samurai": "クラウド（MCP接続可）",
    "amplified ai": "クラウド（API／MCP接続可）",
}

# 出展社名 → ベンダー名の対応
ALIAS = {
    "Patsnap": "PatSnap", "クラリベイト": "Clarivate", "レクシスネクシス": "LexisNexis",
    "RWSグループ": "RWS", "Speeda": "ユーザベース", "アナクア": "Anaqua",
    "デンネマイヤー": "Dennemeyer", "IPACTRY": "アイパクトリ", "マークビジョン": "MarqVision",
}

EVENT = "2026 知財・情報フェア＆コンファレンス"
EVENT_YEAR = 2026
EVENT_VENUE = "東京ビッグサイト 東3ホール"
EVENT_PERIOD = "2026-09-16/2026-09-18"


def w(name, header, rows):
    p = DATA / name
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        cw = csv.writer(f)
        cw.writerow(header)
        cw.writerows(rows)
    print(f"  {name}: {len(rows)}行")


def main():
    # --- categories ---
    cats = [(c["no"], PHASE[c["row"]], c["title"], c["sub"], i + 1)
            for i, c in enumerate(D.UNIFIED)]
    w("categories.csv", ["cat_id", "phase", "title", "subtitle", "sort"], cats)

    # --- vendors / vendor_categories ---
    vend, links = {}, []
    for c in D.UNIFIED:
        for it in c["items"]:
            n = it["n"]
            if n not in vend:
                region, country = REGION.get(it.get("c"), ("その他", ""))
                url, desc = V.INFO.get(n, ("", ""))
                vend[n] = {
                    "vendor_id": "", "name": n, "region": region, "country": country,
                    "url": url, "description": desc, "deployment": DEPLOY.get(n, ""),
                    "is_mcp": 0, "is_new_2026": 0, "status": "active",
                    "first_listed": "2026-09", "updated_at": "2026-09-17", "note": "",
                }
            if "MCP" in it.get("f", []):
                vend[n]["is_mcp"] = 1
            if "NEW" in it.get("f", []):
                vend[n]["is_new_2026"] = 1
            links.append((n, c["no"]))

    # カオスマップ未掲載だが2026年フェアに出展していた1社
    if "SciTech Patent Art" not in vend:
        vend["SciTech Patent Art"] = {
            "vendor_id": "", "name": "SciTech Patent Art", "region": "アジア・他",
            "country": "インド", "url": "https://www.patentart.com/",
            "description": "2002年設立、100名超の科学者を擁する調査会社。文書に基づいてのみ回答し出典を示すAIアシスタント「Verbatim」と、要素単位のクレームマッピングを行うBridgeSuiteを提供する。",
            "deployment": "", "is_mcp": 0, "is_new_2026": 1, "status": "active",
            "first_listed": "2026-09", "updated_at": "2026-09-17",
            "note": "カオスマップ2026.9版には未掲載",
        }
        links += [("SciTech Patent Art", "01"), ("SciTech Patent Art", "12")]

    for i, n in enumerate(sorted(vend), start=1):
        vend[n]["vendor_id"] = f"V{i:03d}"

    cols = ["vendor_id", "name", "region", "country", "url", "description", "deployment",
            "is_mcp", "is_new_2026", "status", "first_listed", "updated_at", "note"]
    w("vendors.csv", cols, [[vend[n][c] for c in cols] for n in sorted(vend)])

    seen = set()
    rows = []
    for n, cid in links:
        if (n, cid) in seen:
            continue
        seen.add((n, cid))
        rows.append((vend[n]["vendor_id"], cid))
    rows.sort()
    w("vendor_categories.csv", ["vendor_id", "cat_id"], rows)

    # --- exhibitions ---
    ex = []
    for no, _t, _s in X.CATS:
        for name, booth, prod, note in X.E[no]:
            key = ALIAS.get(name, name)
            if key not in vend:
                print(f"  [警告] 未突合: {name}")
                continue
            ex.append((f"E{len(ex)+1:03d}", EVENT, EVENT_YEAR, EVENT_VENUE, EVENT_PERIOD,
                       vend[key]["vendor_id"], key,
                       "" if booth == "—" else booth, prod, note))
    w("exhibitions.csv",
      ["exh_id", "event", "year", "venue", "period", "vendor_id", "vendor_name",
       "booth", "exhibit_name", "exhibit_note"], ex)

    # --- excluded（マップ対象外だが知財エコシステム上重要） ---
    exc = [(f"N{i:03d}", n, kind, why, "2026-09-17")
           for i, (n, (kind, why)) in enumerate(sorted(D.EXCLUDED.items()), start=1)]
    w("excluded.csv", ["excluded_id", "name", "kind", "reason", "checked_at"], exc)

    print(f"\n完了: ベンダー{len(vend)}社 / カテゴリ{len(cats)} / 出展{len(ex)} / 対象外{len(exc)}")


if __name__ == "__main__":
    main()
