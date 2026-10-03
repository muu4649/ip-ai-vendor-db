# -*- coding: utf-8 -*-
"""
2026年10月3日の更新（前回 2026-09-27 以降の調査結果を反映する）。

    python3 scripts/03_update_20261003.py
    python3 scripts/build.py

内容
  1. 新規追加 6社（トヨタテクニカルディベロップメント、ClaimHit、PatentWatch、BlackBox IP、
     Black Hills IP、Evalueserve）
  2. 社名・地域・URLの修正（NLPatent→Clerq、IPdash Intelligence→IPdash東京特許事務所、
     アイパクトリの地域、AI特許翻訳のURL、AI Samuraiの親会社、FoundationIPの統合扱い）
  3. 上記に伴う工程・導入条件・出展記録の追加と修正
すべての変更は logs/20261003_review.csv に根拠つきで残す。二度流しても同じ結果になる。
"""
import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TODAY = "2026-10-03"


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
    dict(vendor_id="V154", name="トヨタテクニカルディベロップメント", region="日本", country="日本",
         url="https://www.toyota-td.jp/business/ip/service/",
         description="生成AIの知財業務支援ツール「AI Ninja」（旧swimy）を提供。検索式の自動生成から母集合づくり、"
                     "分類・可視化、発明検討の整理までを扱い、子会社AI Samuraiの明細書作成・中間対応とつなぐ。"
                     "特許調査・解析の受託も行う。",
         deployment="", is_mcp="0", is_new_2026="0",
         note="2025年6月にAI Samuraiを完全子会社化",
         source="toyota-td.jp/business/ip/service（知財サービス一覧）、news/files/2025_083.pdf（AI Ninja発表 2025-11）"),
    dict(vendor_id="V155", name="ClaimHit", region="北米", country="米国",
         url="https://www.claimhit.com/",
         description="特許を使っている企業・製品をAIで洗い出し、侵害の証拠とクレームチャートを作る。"
                     "ライセンス交渉の下調べ向けで、1特許99ドルの試用とクレジット制をとる。",
         deployment="クラウド", is_mcp="0", is_new_2026="0", note="",
         source="claimhit.com（Patent-to-Market Intelligence）"),
    dict(vendor_id="V156", name="PatentWatch", region="北米", country="カナダ",
         url="https://www.patentwatch.ai/",
         description="トロント発、Y Combinator出身。特許と製品資料から根拠つきのクレームチャートを作り、"
                     "侵害製品の特定、標準必須特許の対応付け、有効性の確認を行う。シードで280万ドルを調達した（累計320万ドル）。",
         deployment="", is_mcp="0", is_new_2026="0", note="",
         source="patentwatch.ai、legaltech.ca 2026-05-28、dealroom（シード280万ドル）"),
    dict(vendor_id="V157", name="BlackBox IP", region="北米", country="米国",
         url="https://blackboxip.com/",
         description="ニューヨーク拠点。IDS（情報開示陳述書）の文献管理、拒絶理由通知への応答の雛形、"
                     "特許期間調整の計算などの特許事務を、AI・機械学習で自動化する。",
         deployment="", is_mcp="0", is_new_2026="0", note="",
         source="blackboxip.com、ipwatchdog.com ウェビナー告知（2026-10-20）"),
    dict(vendor_id="V158", name="Black Hills IP", region="北米", country="米国",
         url="https://blackhills.ai/",
         description="ミネアポリス拠点で、Black Hills AIの名でも展開する。期限管理・年金更新・IDS管理を、"
                     "自社のAIツールOtto IPと決定論的な自動化で処理し、パラリーガル業務も受託する。",
         deployment="", is_mcp="0", is_new_2026="0", note="Black Hills AI の名称でも展開",
         source="blackhills.ai（Otto IP）、所在地は公開企業情報（Minneapolis, MN）"),
    dict(vendor_id="V159", name="Evalueserve", region="欧州", country="スイス",
         url="https://www.evalueserve.com/product/patent-research-platform-insightloupe/",
         description="スイスに本社を置く調査・分析会社。特許調査の受託で大手の一角を占め、"
                     "AIを使った特許・非特許のランドスケープ分析基盤Insightloupeを提供する。",
         deployment="", is_mcp="0", is_new_2026="0", note="",
         source="evalueserve.com（Insightloupe、IP and R&D solutions）"),
]

NEW_CATEGORIES = {
    # vendor_id: [(cat_id, role, source)]
    "V154": [("02", "主", "prtimes 000000039.000070679：AI Ninja Innovation（発明検討支援・提案書）"),
             ("07", "主", "toyota-td.jp：AI Ninja LandScape（政策・論文・特許の定量分析）"),
             ("17", "主", "toyota-td.jp：特許調査・解析（IPランドスケープ、技術動向調査）の受託"),
             ("01", "副", "prtimes 000000039.000070679：アイデア整理・作用効果整理"),
             ("03", "副", "prtimes 000000039.000070679：検索式の自動生成・従来技術検索")],
    "V155": [("12", "主", "claimhit.com：侵害検知・実施の証拠・クレームチャート"),
             ("14", "副", "claimhit.com：ライセンス交渉向けの侵害企業の特定")],
    "V156": [("12", "主", "patentwatch.ai：根拠つきクレームチャート"),
             ("16", "副", "patentwatch.ai：標準必須特許（SEP）の対応付け"),
             ("03", "副", "patentwatch.ai：先行技術・有効性の分析"),
             ("14", "副", "dealroom：侵害検知から収益化（ライセンス）まで")],
    "V157": [("09", "主", "blackboxip.com：IDS管理・特許期間調整・米国特許庁とのやりとりの自動化"),
             ("05", "副", "blackboxip.com：拒絶理由通知への応答の雛形（rSHELL）")],
    "V158": [("09", "主", "blackhills.ai：期限管理・年金更新・IDS管理の自動化（Otto IP）"),
             ("05", "副", "blackhills.ai：拒絶理由通知の分析")],
    "V159": [("17", "主", "evalueserve.com：特許調査の受託（IP and R&D solutions）"),
             ("07", "主", "evalueserve.com：Insightloupe（特許・非特許のランドスケープ分析）"),
             ("03", "副", "evalueserve.com：AIを調整した特許検索")],
}

NEW_ATTRIBUTES = [
    # vendor_id, attr_id, value, source, note
    ("V154", "ja", "あり", "https://www.toyota-td.jp/business/ip/service/", "国内企業"),
    ("V154", "trial", "未確認", "https://prtimes.jp/main/html/rd/p/000000039.000070679.html",
     "2026年3月末まで期間限定の無料トライアル（2週間・5名まで）を実施（終了）"),
    ("V155", "no_training", "あり", "https://www.claimhit.com/security",
     "AIモデル提供元はゼロデータリテンション、またはAPI経由の学習なしと明記"),
    ("V155", "pricing", "あり", "https://www.claimhit.com/", "1特許のパイロット99ドル（30日返金保証）、以降はクレジット制"),
    ("V155", "trial", "未確認", "https://www.claimhit.com/", "試用は有料（99ドル・返金保証つき）"),
    ("V155", "ja", "未確認", "https://www.claimhit.com/faq", "日本・中国・韓国の特許にはEPOの翻訳経由で対応。日本語の窓口は未確認"),
    ("V158", "no_training", "あり", "https://blackhills.ai/security-center/",
     "閉じたAI環境とゼロデータリテンションで、機密情報を公開AIモデルの学習に使わないと明記"),
    ("V158", "trial", "あり", "https://blackhills.ai/otto-ip/free-demo/", "Otto IPの無料トライアル"),
]

NEW_EXHIBITIONS = [
    dict(exh_id="E087", event="2026 知財・情報フェア＆コンファレンス", year="2026", venue="東京ビッグサイト 東3ホール",
         period="2026-09-16/2026-09-18", vendor_id="V154", vendor_name="トヨタテクニカルディベロップメント",
         booth="3-E14", exhibit_name="AI Ninja／知財総合コンサルティングサービス",
         exhibit_note="子会社AI Samuraiと共同出展。生成AIを使った知財業務支援システムを紹介（response.jp 2026-08-28）"),
]

# ---------------------------------------------------------------------------
# 2. 既存の社の修正
# ---------------------------------------------------------------------------
VENDOR_FIXES = {
    "V058": dict(name="Clerq", url="https://www.clerq-ip.com/", is_new_2026="1",
                 description="トロント発。2026年8月にNLPatentから社名を変え、発明届出の一次評価と、"
                             "引用文献つきの特許性調査報告を約10分でまとめるエージェント型のワークフローを始めた。",
                 note="2026年8月にNLPatentから社名変更",
                 _log=("NLPatent→Clerq", "社名変更・紹介文更新",
                       "betakit.com：NLPatent rebrands to Clerq（2026-08-18）")),
    "V044": dict(name="IPdash東京特許事務所", url="https://ipdash.tokyo/rivalseeker/",
                 description="他社分析AI「Rival Seeker」を、ソフトウェアブランドIPdash Intelligenceで提供する特許事務所。"
                             "企業を開発チーム単位まで分解して技術動向を追う。",
                 note="IPdash Intelligence は同所のソフトウェアサービスのブランド名",
                 _log=("IPdash Intelligence→IPdash東京特許事務所", "名称修正（ブランド名→事業者名）・URL更新",
                       "prtimes 000000001.000188218：IPdash IntelligenceはIPdash東京特許事務所のソフトウェアサービスブランド")),
    "V105": dict(region="アジア・他", country="韓国", url="https://www.ipactory.com/",
                 description="韓国ソウル発（2020年設立）。生成AIとRAGを使い、特許明細書の作成を支えるIPEDIT draftと、"
                             "翻訳のIPEDIT translateを提供する。2025年7月にサムスン電子とAI特許文書作成支援システムの開発契約を結んだ。",
                 note="初版で国内企業としていたのは誤り（本社は韓国ソウル）",
                 _log=("アイパクトリ", "地域修正（日本→アジア・他／韓国）・URL登録・紹介文更新",
                       "pr-free.jp/2024/109134：株式会社アイパクトリ（本社：韓国ソウル、代表取締役：ユ・ジャンヒョン）")),
    "V005": dict(url="https://iptrans.jp/",
                 description="特許翻訳株式会社から社名を変え、生成AIの一次訳を熟練の特許翻訳者が一文ずつ校正する"
                             "特許翻訳サービスを展開する。",
                 _log=("AI特許翻訳", "URL登録・紹介文更新",
                       "ipforce.jp 2026-02-18：AI翻訳×熟練翻訳者の校正による特許翻訳サービスを本格展開")),
    "V001": dict(note="2025年6月にトヨタテクニカルディベロップメントの完全子会社。同社のAI Ninjaと連携",
                 _log=("AI Samurai", "補記（親会社）",
                       "toyota-td.jp/news/files/2025_032.pdf：AI Samuraiの完全子会社化（2025-06-03）")),
    "V031": dict(status="merged",
                 note="Clarivate の知財管理製品の一つ。社名で掲載する方針により Clarivate に統合扱い（2026-10-03）",
                 _log=("FoundationIP", "統合扱い（Clarivate の製品）",
                       "clarivate.com/intellectual-property：FoundationIP（Cloud based IP practice management）を自社製品として掲載")),
}

CATEGORY_ADDS = {
    "V058": [("02", "副", "betakit.com：発明届出の一次評価（triage of invention disclosures）")],
    "V105": [("06", "副", "pr-free.jp/2024/109134：IPEDIT translate（特許翻訳）"),
             ("02", "副", "pr-free.jp/2024/109134：発明提案書の作成から明細書・請求項の生成まで")],
}

ATTRIBUTE_FIXES = [
    # vendor_id, attr_id, value, source, note
    ("V105", "ja", "未確認", "https://pr-free.jp/2024/109134/",
     "日本語の発表資料はある（本社は韓国ソウル）。日本語の窓口・日本法人は未確認"),
    ("V005", "ja", "あり", "https://iptrans.jp/", "国内企業"),
    ("V044", "ja", "あり", "https://ipdash.tokyo/rivalseeker/", "国内企業"),
]


def main():
    vcols, vendors = read("vendors")
    by_id = {v["vendor_id"]: v for v in vendors}

    for nv in NEW_VENDORS:
        if nv["vendor_id"] in by_id:
            continue
        row = {c: "" for c in vcols}
        row.update({k: v for k, v in nv.items() if k in vcols})
        row.update(status="active", first_listed="2026-10", updated_at=TODAY)
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
    have = {(c["vendor_id"], c["cat_id"]) for c in cats}
    for vid, items in {**NEW_CATEGORIES, **CATEGORY_ADDS}.items():
        for cat_id, role, src in items:
            if (vid, cat_id) in have:
                continue
            cats.append(dict(vendor_id=vid, cat_id=cat_id, role=role, source=src, checked_at=TODAY))
            have.add((vid, cat_id))
            log(by_id[vid]["name"], "追加" if vid in CATEGORY_ADDS else "追加（新規社）", cat_id, src)
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
            log(by_id[vid]["name"], f"導入条件の修正（{attr}）", "", f"{old.get('value')}：{note}")
        else:
            attrs.append(new)
            index[(vid, attr)] = new
            log(by_id[vid]["name"], f"導入条件の追加（{attr}）", "", f"{value}：{note}")
    _, adef = read("attributes")
    order = {a["attr_id"]: int(a["sort"]) for a in adef}
    attrs.sort(key=lambda a: (a["vendor_id"], order[a["attr_id"]]))
    write("vendor_attributes", acols, attrs)

    ecols, exhs = read("exhibitions")
    have_e = {e["exh_id"] for e in exhs}
    for e in NEW_EXHIBITIONS:
        if e["exh_id"] not in have_e:
            exhs.append(e)
            log(e["vendor_name"], "出展記録の追加", "", e["exhibit_note"])
    for e in exhs:  # 社名を直した社は出展記録の表記もそろえる
        if e["vendor_id"] in by_id and e["vendor_name"] != by_id[e["vendor_id"]]["name"]:
            e["vendor_name"] = by_id[e["vendor_id"]]["name"]
    write("exhibitions", ecols, exhs)

    path = ROOT / "logs" / "20261003_review.csv"
    if LOG:
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["vendor", "action", "cat_id", "source_or_note"])
            w.writeheader()
            w.writerows(LOG)
    print(f"変更 {len(LOG)} 件 → {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
