# -*- coding: utf-8 -*-
"""
2026年11月9日の更新（2026-10-03 以降の調査結果を反映する）。

    python3 scripts/04_update_20261109.py
    python3 scripts/build.py

内容
  1. 新規追加 1社（Juristat）
  2. 既存の社の更新（Edge の URL、IPRally の明細書作成と MCP、日立製作所の Shareresearch の生成AI機能）
  3. 上記に伴う工程・導入条件の追加と修正
すべての変更は logs/20261109_review.csv に根拠つきで残す。二度流しても同じ結果になる。
"""
import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TODAY = "2026-11-09"


def read(name):
    with (DATA / f"{name}.csv").open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        return r.fieldnames, list(r)


def write(name, cols, rows):
    with (DATA / f"{name}.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


LOG = []


def log(vendor, action, cat_id, note):
    LOG.append({"vendor": vendor, "action": action, "cat_id": cat_id, "source_or_note": note})


# ---------------------------------------------------------------------------
# 1. 新規追加
# ---------------------------------------------------------------------------
NEW_VENDORS = [
    dict(vendor_id="V160", name="Juristat", region="北米", country="米国",
         url="https://juristat.com/",
         description="米国特許庁の20年以上の審査データを使う審査分析の会社。審査官・審査部門ごとの登録や拒絶の傾向を分析し、"
                     "審査経過から拒絶理由通知への応答とIDS（情報開示陳述書）の準備を自動化する。"
                     "審査データをMCPで生成AIに渡すData Layerも提供する。",
         deployment="クラウド（MCP接続可）", is_mcp="1", is_new_2026="1",
         note="セントルイスで創業。成長投資を受けてコネチカット州ニューヘイブンへの本社移転を発表（移転の完了は未検証）",
         source="juristat.com（Analytics／Workflow automation／Data layer (MCP)）、"
                "help.juristat.com 14668917（Data Layer MCP）、ipwatchdog.com 2026-11-05（Xsensus が Data Layer を採用）"),
]

NEW_CATEGORIES = {
    # vendor_id: [(cat_id, role, source)]
    "V160": [("05", "主", "juristat.com：Office action responses ... built from the prosecution record"),
             ("07", "主", "juristat.com：examiners, portfolios, prosecution trends, and competitors の分析"),
             ("09", "副", "juristat.com：IDS preparation の自動化")],
}

NEW_ATTRIBUTES = [
    # vendor_id, attr_id, value, source, note
    ("V160", "trial", "あり", "https://resources.juristat.com/juristat-data-layer-trial",
     "Data Layer（MCP）の14日間無料トライアル（年25件以上の特許出願がある個人が対象）"),
    ("V160", "pricing", "未確認", "https://juristat.com/",
     "個人向けのSolo tierを案内しているが、金額は公式サイトで確認できなかった"),
]

# ---------------------------------------------------------------------------
# 2. 既存の社の更新
# ---------------------------------------------------------------------------
VENDOR_FIXES = {
    "V030": dict(url="https://www.withedge.com/",
                 description="AIの特許明細書作成ツールIngeniaと、AIの商標調査ツールCertusを提供。"
                             "Ingeniaは特許向けの図面エディタを備え、図面と本文をそろえながら書ける。",
                 note="運営はEdge Innovations, Inc.。tryedge.io は同名の決済サービスのサイトで別会社",
                 _log=("Edge", "URL修正・紹介文更新",
                       "withedge.com：Ingenia（AI patent drafting）・Certus（AI trademark clearance）。"
                       "tryedge.io は Edge Payment Technologies（決済サービス）")),
    "V042": dict(deployment="クラウド（API／MCP接続可）", is_mcp="1",
                 description="フィンランド発。特許を知識グラフに変換して探す検索を中心に、競合・ポートフォリオ分析（Intelligence）と、"
                             "先行技術を踏まえた明細書作成（Protection）を提供する。MCPとAPIで外部のAIや自社システムからも使える。",
                 _log=("IPRally", "紹介文更新・MCP対応",
                       "iprally.com：Protection（Patent Drafting、New）、MCP & API。"
                       "news 2026-11-02：IPRally MCP がコレクション・検索ケース・エージェントの実行結果を読めるようになった")),
    "V143": dict(url="https://www.hitachi.co.jp/Prod/comp/app/tokkyo/sr/index.html", is_new_2026="1",
                 description="特許情報提供サービスShareresearchを提供。2026年10月に生成AIの「AI要約」（技術分野・対象技術・課題・解決手段の"
                             "4観点で整理）と「AI検索」（チャットで検索条件を整理し、一致度の順に示す）を加えた。"
                             "知的財産管理システムPALNET/MC6も持つ。",
                 _log=("日立製作所", "紹介文更新・URL変更（Shareresearch の製品ページ）",
                       "cloud.watch.impress.co.jp/docs/news/2140633.html：AI要約・AI検索を2026年10月5日から提供（9月15日発表）")),
}

CATEGORY_ADDS = {
    "V030": [("10", "副", "withedge.com：Certus（AI trademark clearance and search）")],
    "V042": [("04", "副", "iprally.com：Protection（Patent Drafting、prior-art-aware drafting）")],
    "V143": [("03", "副", "cloud.watch.impress.co.jp 2140633：AI検索（チャットで検索条件を整理し、一致度順に提示）")],
}

CATEGORY_SOURCE_FIXES = {
    # (vendor_id, cat_id): source
    ("V030", "06"): "withedge.com：Ingenia の Figures（patent-focused figure editor）",
    ("V042", "07"): "iprally.com：Intelligence（Competitive Intelligence、Portfolio Analysis）",
    ("V143", "07"): "cloud.watch.impress.co.jp 2140633：Shareresearch の AI要約（技術分野・対象技術・課題・解決手段）",
}

ATTRIBUTE_FIXES = [
    # vendor_id, attr_id, value, source, note
    ("V030", "no_training", "あり", "https://www.withedge.com/", "「No training on your data, period.」と明記"),
    ("V143", "trial", "あり", "https://www.hitachi.co.jp/Prod/comp/app/tokkyo/sr/index.html",
     "Shareresearch の無料で試せるIDを発行"),
]


def main():
    vcols, vendors = read("vendors")
    by_id = {v["vendor_id"]: v for v in vendors}

    for nv in NEW_VENDORS:
        if nv["vendor_id"] in by_id:
            continue
        row = {c: "" for c in vcols}
        row.update({k: v for k, v in nv.items() if k in vcols})
        row.update(status="active", first_listed="2026-11", updated_at=TODAY)
        vendors.append(row)
        by_id[row["vendor_id"]] = row
        log(row["name"], "新規追加", "", nv["source"])

    for vid, fix in VENDOR_FIXES.items():
        row = by_id[vid]
        who, action, note = fix["_log"]
        changed = False
        for k, v in fix.items():
            if k.startswith("_"):
                continue
            if row[k] != v:
                row[k] = v
                changed = True
        if changed:
            row["updated_at"] = TODAY
            log(who, action, "", note)
    write("vendors", vcols, vendors)

    ccols, cats = read("vendor_categories")
    have = {(c["vendor_id"], c["cat_id"]): c for c in cats}
    for vid, items in {**NEW_CATEGORIES, **CATEGORY_ADDS}.items():
        for cat_id, role, src in items:
            if (vid, cat_id) in have:
                continue
            row = dict(vendor_id=vid, cat_id=cat_id, role=role, source=src, checked_at=TODAY)
            cats.append(row)
            have[(vid, cat_id)] = row
            log(by_id[vid]["name"], "追加" if vid in CATEGORY_ADDS else "追加（新規社）", cat_id, src)
    for (vid, cat_id), src in CATEGORY_SOURCE_FIXES.items():
        row = have[(vid, cat_id)]
        if row["source"] != src:
            row.update(source=src, checked_at=TODAY)
            log(by_id[vid]["name"], "根拠の更新", cat_id, src)
    write("vendor_categories", ccols, cats)

    acols, attrs = read("vendor_attributes")
    index = {(a["vendor_id"], a["attr_id"]): a for a in attrs}
    for vid, attr, value, src, note in NEW_ATTRIBUTES + ATTRIBUTE_FIXES:
        new = dict(vendor_id=vid, attr_id=attr, value=value, source=src, checked_at=TODAY, note=note)
        old = index.get((vid, attr))
        if old and all(old[k] == new[k] for k in ("value", "source", "note")):
            continue
        if old:
            old.update(new)
            log(by_id[vid]["name"], f"導入条件の修正（{attr}）", "", f"{value}：{note}")
        else:
            attrs.append(new)
            index[(vid, attr)] = new
            log(by_id[vid]["name"], f"導入条件の追加（{attr}）", "", f"{value}：{note}")
    _, adef = read("attributes")
    order = {a["attr_id"]: int(a["sort"]) for a in adef}
    attrs.sort(key=lambda a: (a["vendor_id"], order[a["attr_id"]]))
    write("vendor_attributes", acols, attrs)

    path = ROOT / "logs" / "20261109_review.csv"
    if LOG:
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["vendor", "action", "cat_id", "source_or_note"])
            w.writeheader()
            w.writerows(LOG)
    print(f"変更 {len(LOG)} 件 → {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
