# -*- coding: utf-8 -*-
"""
2026-09-27 レビュー: 工程カテゴリの網羅化とURLの全件検証

契機: サマリアが「03 特許検索」の1工程にしか登録されていなかった（実際は9工程）。
      初版はカオスマップ上の配置＝代表機能1〜2個で登録しており、
      プラットフォーム型ベンダーの機能が大きく欠落していた。

方針:
  - vendor_categories に role 列を追加
      主 = カオスマップに配置した代表機能（既存の登録をそのまま移行）
      副 = 公式情報・出展社情報で提供を確認できた機能（今回追加）
  - 追加・削除はすべて根拠（source）を記録する
  - URLは全件の到達を確認し、存在しないドメインを差し替える

このスクリプトは1回だけ実行する。実行後は data/*.csv がマスター。
"""

import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LOG = ROOT / "logs"
TODAY = "2026-09-27"

PIFC = "2026知財・情報フェア出展社情報"

# ---------------------------------------------------------------------------
# 工程の追加（vendor名, [cat_id...], 根拠）
# ---------------------------------------------------------------------------
ADD = [
    # --- 日本：プラットフォーム型で大きく欠落していたもの ---
    ("パテント・インテグレーション", ["01", "02", "04", "05", "07", "08", "12", "13"],
     "patent-i.com/summaria：先行技術調査・発明届出・新規出願・拒絶理由対応・クリアランス・係争対応・権利維持判断・特許解析を支援。明細書作成支援（2024）、スクリーニング、SDIを搭載"),
    ("Patentfield", ["07", "08"],
     "product.patentfield.com：AI分類・課題/用途ラベル・IPランドスケープ・レポート生成（Patentfield AIR）。事業内容に特許情報を活用したマッチング支援"),
    ("パナソニック デジタル", ["07"],
     "panasonic.com/jp/business/its/patentsquare：AI自動分類、知財BIダッシュボード（最大100万件の可視化）"),
    ("発明通信社", ["09", "17"],
     f"{PIFC}：HYPAT-i2（検索）、IPeakMS（知財管理）、特許調査"),
    ("日立製作所", ["09"],
     "hitachi.co.jp/Prod/comp/app/tokkyo/mc6：知的財産管理システムPALNET/MC6を提供"),
    ("日立社会情報サービス", ["07"],
     "hitachi-sis.co.jp：ShareresearchはPALNET/MC6と連携し競合特許戦略の分析・侵害チェックを支援"),
    ("東芝", ["07", "08"],
     f"{PIFC}：IPeakMSに特許価値評価と知財ROICによる無形資産の可視化を参考出展"),
    ("アクロソフト", ["07"],
     f"{PIFC}：知財データ分析とIPランドスケープによる経営戦略支援"),
    ("VALUENEX", ["01"],
     f"{PIFC}：ビッグデータ俯瞰解析で戦略立案や新製品開発に資する示唆を導く"),
    ("パテント・リザルト", ["01", "08"],
     f"{PIFC}：技術内容の理解から競合分析・アイデア創出まで支援。Biz Cruncherは特許の注目度スコアを算出"),
    ("ユーザベース", ["01"],
     f"{PIFC}：経営企画・新規事業開発・研究開発領域の調査・分析を効率化"),
    ("アイ・ピー・ファイン", ["01"],
     f"{PIFC}：革新的な発明・事業の創出のための情報革新。R&Dランドスケープ「IIC」"),
    ("NTTデータ", ["02", "18"],
     "nttdata.com 2026/081900：発明相談から発明提案書作成までを支援。AI活用の着手から組織への定着まで支援"),
    ("アスタミューゼ", ["07"],
     "astamuse.co.jp：特許・論文・スタートアップ・助成金を統合したデータで技術DDを支援"),
    ("TechnoProducer", ["07"],
     "IPランドスケープ支援・生成AI×特許分析"),
    ("ユアサポ", ["02", "06"],
     "prtimes 000000008.000049990：構造化された発明提案書作成支援、請求項・明細書生成。出展社情報：図面生成と品質チェック"),
    ("アイビーリサーチ", ["06"],
     f"{PIFC}：明細書作成・チェック・出願支援。サポライター（文書作成支援）"),
    ("aiip", ["03", "13"],
     f"{PIFC}：FTO調査、情報提供・異議申立・無効審判による他社牽制"),
    ("AI Samurai", ["02", "07"],
     "prtimes 000000300.000021559：知財AIエージェントが発明提案書作成・競合分析・ポートフォリオ分析・知財戦略立案を支援"),
    ("Genzo AI", ["03", "05", "06", "12", "14"],
     "shimadzu.co.jp/news/2026：明細書作成・特許翻訳・中間処理・先行技術調査・侵害予防・契約書レビュー"),
    ("AIVisor", ["05", "07"],
     f"{PIFC}：拒絶対応・公報分類まで一貫"),
    ("エムニ", ["03", "18"],
     f"{PIFC}：検索式の自動生成・先行技術調査。業務に合わせたオーダーメイドAI開発"),
    ("日本特許情報機構", ["06", "17"],
     f"{PIFC}：Japio-GPG/FXの高精度AI翻訳、意匠権調査サービス"),
    ("日本パテントデータサービス", ["17"],
     f"{PIFC}：特許調査・研修サービス"),
    ("リーガルテック", ["07"],
     f"{PIFC}：MyTokkyo.Aiで文献の要約・比較・分析"),
    ("ASU", ["03", "07", "09", "12"],
     "asu.co.jp/solution/ip_legal/ip_dept/aicrea：Aicreaは発明構成要素の自動抽出・構成要素ごとの類似度算出・根拠付き対比表・社内未公開情報の可視化。DBBOY/uniを販売"),
    ("プロパティ", ["03", "06", "14"],
     "property.ne.jp：特許意匠商標調査・解析・翻訳・ライセンス・データベース（ORBIT.com、WIPS Global）"),
    ("日本アイアール", ["07", "18"],
     "nihon-ir.jp：技術動向調査、知財担当者向け生成AI活用セミナー"),
    ("パソナナレッジパートナー", ["07", "09"],
     f"{PIFC}：知財ポートフォリオ分析・競合分析、管理事務まで対応"),
    ("電通総研", ["09"],
     f"{PIFC}：知財管理システム導入を含む組織全体の運用支援"),
    ("知財戦略ラボラトリー", ["07"],
     f"{PIFC}：事業の急所を特許ポートフォリオで守る構造戦略論"),
    ("IPTech弁理士法人", ["04"],
     f"{PIFC}：生成AIを活用した明細書作成・先行技術調査・中間対応"),
    ("スズエ国際特許事務所", ["04"],
     f"{PIFC}：AIが構造化した明細書ドラフトを弁理士が精査しJPO提出まで対応"),
    ("鷲田国際特許事務所", ["04"],
     f"{PIFC}：最新のAIモデルを実務に投入し特許権取得を支援"),
    ("川村インターナショナル", ["07"],
     f"{PIFC}：StructFlowでスクリーニング・要約・データ構造化を支援"),
    ("サン・フレア", ["17"],
     f"{PIFC}：先行技術・クリアランス・無効資料・技術動向の特許調査"),
    ("知財コーポレーション", ["04", "05", "17"],
     f"{PIFC}：発明発掘・出願サポート、先行技術調査、OAサポート（AIと専門家の融合）"),
    ("AIBS", ["07", "17"],
     f"{PIFC}：AI分析×専門家の知財戦略コンサルティング、特許調査"),
    ("RWS", ["03", "09", "11", "17"],
     f"{PIFC}：AI活用型特許データベース、特許年金管理、ブランド保護、170か国以上の特許調査"),
    ("中央光学出版", ["03", "07", "17"],
     "cks.co.jp：国内外特許のインターネット検索、特許調査、PatSnap Analyticsの国内販売"),
    ("GMOブランドセキュリティ", ["10"],
     "brandsecurity.gmo：商標管理ツールBRANTECT byGMO"),
    ("IPリッチ", ["14"],
     f"{PIFC}：PatentRevenueで売買・ライセンスの成約まで支援"),
    ("イノベーションリサーチ", ["07", "08", "18"],
     "innovation-r.com：技術動向分析「イノベーションレポート」。特許庁の知財ビジネス評価書作成会社（令和2年度）。知財分析の内製化支援"),
    ("テスコ", ["07", "10", "12"],
     "tesco-search.com：技術テーマ別の特許マップ、侵害チェック、意匠・商標調査"),
    ("テクノリサーチ", ["07"],
     f"{PIFC}：IPランドスケープ、パテントマップ作成"),
    ("ベーステクノロジー", ["14"],
     "info-dooup.base.co.jp：Dooupで契約管理に対応"),
    ("AIDAO", ["06"],
     "prtimes 000000013.000124450：トヨタテクニカルディベロップメントと生成AIによる特許図面生成プロジェクト"),
    # --- グローバル ---
    ("PatSnap", ["04", "12"],
     "eureka.patsnap.com：特許調査・FTO・明細書作成・意匠クリアランスのAIエージェント"),
    ("Anaqua", ["07", "10", "11"],
     f"{PIFC}：分析ソリューションAcclaimIP、ドメイン名管理・模倣品対策のブランド保護"),
    ("Dennemeyer", ["07"],
     f"{PIFC}：知財ポートフォリオの可視化から洞察を導く"),
    ("Patlytics", ["08"],
     "businesswire 20260408：transactional due diligence、ポートフォリオ分析から収益化まで"),
    ("DeepIP", ["07", "13"],
     "deepip.ai：portfolio intelligence、competitive analysis、litigation readiness"),
    ("Solve Intelligence", ["06"],
     "solveintelligence.com：figure generation（図面生成）"),
    ("Questel", ["07"],
     "questel.com：Orbit Intelligenceの分析機能"),
    ("Clarivate", ["12"],
     "clarivate.com：Derwentのデザイン特許侵害検出"),
    ("WIPS", ["09"],
     "Questelとのグローバル年金管理提携（2025年6月）、年金管理サービス"),
    ("Elevate Services", ["04", "05", "10", "17"],
     "elevate.law/intellectual-property：Patent Preparation and Prosecution、Trademark Portfolio Management、Global Patent/Trademark Information Searching（Sagacious IP）"),
    ("Dolcera", ["03", "16"],
     "web.dolcera.com：PCSによるAI特許検索。SEP保有者の大半が同社データを利用"),
    ("XLSCOUT", ["01"],
     "xlscout.ai：PatDigger LLMによるアイデア創出"),
    ("GreyB", ["17"],
     "greyb.com：特許調査・分析サービス"),
    ("IP.com", ["03"],
     "ip.com：InnovationQによる特許・非特許文献検索"),
    ("Ankar AI", ["05", "12"],
     "ankar.ai：発明可能性の検証から明細書・中間対応・侵害検出まで"),
    ("Lightbringer", ["09"],
     "law360 2490114：patent strategy, filing, and portfolio management through a single platform"),
    ("MarqVision", ["10"],
     f"{PIFC}：知財の作成・管理・保護をワンストップ、商標管理の自動化"),
    ("ArcPrime", ["09", "14"],
     "arcprime.com/solutions：AI IP Management System、Licensing Intelligence"),
    ("yet2", ["14"],
     "yet2.com：技術移転・ライセンシングの仲介"),
]

# ---------------------------------------------------------------------------
# 工程の削除（誤登録）
# ---------------------------------------------------------------------------
REMOVE = [
    ("ASU", "05", "Aicreaは調査・対比ツールで中間対応の機能は確認できず（asu.co.jp）"),
    ("ユアサポ", "05", "中間対応の機能は公表資料で確認できず（発明提案書・請求項・明細書・品質チェックのみ）"),
]

# ---------------------------------------------------------------------------
# URLの差し替え（存在しないドメイン・404を修正）
# ---------------------------------------------------------------------------
URL_FIX = {
    "パテント・インテグレーション": "https://patent-i.com/summaria/",
    "AIBS": "https://korrepet.com/",
    "AIDAO": "https://aidao-pjt.com/",
    "ArcPrime": "https://www.arcprime.com/",
    "GMOブランドセキュリティ": "https://brandsecurity.gmo/",
    "アスタミューゼ": "https://www.astamuse.co.jp/",
    "イノベーションリサーチ": "https://www.innovation-r.com/",
    "サカタブランドソリューションズ": "https://sakatabs.com/",
    "テスコ": "https://www.tesco-search.com/",
    "ネットワークス": "https://www.kempos.co.jp/",
    "プロパティ": "https://www.property.ne.jp/",
    "ベーステクノロジー": "https://info-dooup.base.co.jp/",
    "ミガリオ": "https://www.migalio.com/",
    "中央光学出版": "https://www.cks.co.jp/",
    "知財コーポレーション": "https://www.chizai.jp/",
    "CAS": "https://www.cas.org/solutions/stn-ip-protection-suite/ip-finder",
    "MarqVision": "https://www.marqvision.com/",
    "VALUENEX": "https://www.valuenex.com/",
    "パナソニック デジタル": "https://www.panasonic.com/jp/business/its/patentsquare.html",
    "Genzo AI": "https://www.genzo-ai.co.jp/",
}

# ---------------------------------------------------------------------------
# 紹介文・状態の修正
# ---------------------------------------------------------------------------
DESC_FIX = {
    "パテント・インテグレーション":
        "特許読解支援AI「サマリア」を提供。先行技術調査、発明届出、新規出願（明細書作成支援）、拒絶理由対応、クリアランス、係争対応、権利維持判断、特許解析まで幅広い場面を支援する。スクリーニング、SDI（定期監視）を備え、2026年にMCP対応した。代表は弁理士の大瀬佳之氏。",
    "Specifio":
        "クレームから明細書本文と要約を数分で生成する、ソフトウェア関連発明向けの自動ドラフティングの先駆け。2026年2月時点でPaximalに買収され、コードは同社に引き継がれている。",
    "ASU":
        "生成AI連携サービス「Aicrea」は発明の構成要素を自動抽出し、構成要素ごとに先行技術との類似度を算出して根拠付きの対比表を出力する。出願支援ソフトPPW8、知財管理システムDBBOY/uni、契約管理ContractEyesも扱う。",
    "パナソニック デジタル":
        "特許調査支援サービスPatentSQUAREを提供。1992年からの運用実績を持ち、AI検索・AI自動分類・SDIに加え、最大100万件を可視化する知財BIダッシュボードを備える。2026年4月にパナソニック ソリューションテクノロジーから社名変更。",
    "Genzo AI":
        "島津製作所とIP Agentが2026年4月に設立。同社知財部の暗黙知をAIプロンプトに落とし込み、明細書作成、特許翻訳、中間処理、先行技術調査、侵害予防、契約書レビューを支援するSaaSとして外販する。",
    "イノベーションリサーチ":
        "独自の分析システムと生成AIを組み合わせた技術動向分析「イノベーションレポート」を提供。定量・定性分析を手頃な価格で出し、特許庁の知財ビジネス評価書の作成実績も持つ。知財分析の内製化支援にも踏み込む。",
}
STATUS_FIX = {
    "Specifio": ("merged", "2026年2月時点でPaximalに買収。初版の「Spellbook傘下」は誤り（2026-09-27訂正）"),
}


def read(name):
    with (DATA / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(name, header, rows):
    with (DATA / name).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


def main():
    vendors = read("vendors.csv")
    vid = {v["name"]: v["vendor_id"] for v in vendors}
    vcs = read("vendor_categories.csv")

    # 既存リンクを「主」として移行
    links = {}
    for r in vcs:
        key = (r["vendor_id"], r["cat_id"])
        links[key] = {
            "vendor_id": r["vendor_id"], "cat_id": r["cat_id"],
            "role": r.get("role") or "主",
            "source": r.get("source") or "カオスマップ2026.9の配置",
            "checked_at": r.get("checked_at") or "2026-09-17",
        }

    log = []
    for name, cats, src in ADD:
        if name not in vid:
            raise SystemExit(f"[中止] vendors.csv に {name} がない")
        for c in cats:
            key = (vid[name], c)
            if key in links:
                continue
            links[key] = {"vendor_id": vid[name], "cat_id": c, "role": "副",
                          "source": src, "checked_at": TODAY}
            log.append((name, "追加", c, src))

    for name, c, why in REMOVE:
        key = (vid[name], c)
        if links.pop(key, None):
            log.append((name, "削除", c, why))

    rows = sorted(links.values(), key=lambda r: (r["vendor_id"], r["cat_id"]))
    write("vendor_categories.csv", ["vendor_id", "cat_id", "role", "source", "checked_at"], rows)

    # vendors.csv の修正
    for v in vendors:
        n = v["name"]
        if n in URL_FIX and v["url"] != URL_FIX[n]:
            log.append((n, "URL修正", "", f'{v["url"]} → {URL_FIX[n]}'))
            v["url"] = URL_FIX[n]
            v["updated_at"] = TODAY
        if n in DESC_FIX:
            v["description"] = DESC_FIX[n]
            v["updated_at"] = TODAY
            log.append((n, "紹介文修正", "", ""))
        if n in STATUS_FIX:
            v["status"], v["note"] = STATUS_FIX[n]
            v["updated_at"] = TODAY
            log.append((n, "状態変更", "", STATUS_FIX[n][1]))
    write("vendors.csv", list(vendors[0].keys()), vendors)

    # レビュー記録
    LOG.mkdir(exist_ok=True)
    with (LOG / "20260927_review.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["vendor", "action", "cat_id", "source_or_note"])
        w.writerows(log)

    adds = sum(1 for x in log if x[1] == "追加")
    print(f"工程追加 {adds} / 削除 {sum(1 for x in log if x[1]=='削除')} / "
          f"URL修正 {sum(1 for x in log if x[1]=='URL修正')} / "
          f"紹介文修正 {sum(1 for x in log if x[1]=='紹介文修正')} / "
          f"状態変更 {sum(1 for x in log if x[1]=='状態変更')}")
    print(f"vendor_categories: {len(vcs)}行 → {len(rows)}行")


if __name__ == "__main__":
    main()
