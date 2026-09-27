# -*- coding: utf-8 -*-
"""
知財AIベンダー名鑑（Streamlit版）

知財部門がAIツールを選ぶときの下調べ用。
「やりたい業務」から候補を探し、導入条件で絞り、気になる社を横に並べて比べる。

データの正本は data/*.csv。起動時に読み込み、scripts/build.py と同じ検査を通してから表示する。
CSVを直して push すれば、Streamlit Community Cloud 上の表示もそのまま更新される。

ローカルで動かす（Python 3.11 以上）:
    pip install -r requirements.txt
    streamlit run streamlit_app.py
"""

import glob
import html
import importlib.util
import io
import json
import pathlib

import altair as alt
import pandas as pd
import streamlit as st

APP_NAME = "知財AIベンダー名鑑"            # 名称を変えるときはここだけ
EDITION = "2026.9"
REPO_URL = "https://github.com/muu4649/ip-ai-vendor-db"
ROOT = pathlib.Path(__file__).parent
REGIONS = ["日本", "北米", "欧州", "アジア・他"]
MAX_COMPARE = 5          # 比較できる社数の上限
PAGE = 24                # 一度に表示するカードの数
SORTS = ["国内の社を先に", "社名順", "ブース順"]
TABS = ["探す", "比較する", "市場の全体像", "知財・情報フェア2026", "掲載基準・データ"]
FAIR = "2026 知財・情報フェア＆コンファレンス（2026年9月16〜18日・東京ビッグサイト東3ホール）"

# グラフの配色（LeXi/Vent の青をもとに、代表/対応の2段を --ordinal で検証済み）
C_PRIMARY = "#1e5a9f"       # 代表的な工程（LeXi/Vent の青）
C_SECONDARY = "#7fa8d6"     # 対応している工程（面 #f8f7f6 に対し 2.32:1）
SURFACE = "#f8f7f6"         # LeXi/Vent の背景色
SEQ_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

st.set_page_config(page_title=f"{APP_NAME} {EDITION}", page_icon=":material/travel_explore:",
                   layout="wide", initial_sidebar_state="auto")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800&display=swap');
/* LeXi/Vent の配色（lexi2vent.com の表示から計測。2026-09-27） */
:root{--ink:#222222;--text:#333333;--muted:#666666;--faint:#8c8c8c;--line:rgba(51,51,51,.12);
--page:#f8f7f6;--card:#ffffff;
--blue:#1e5a9f;--blue-bright:#1168cc;--blue-tint:#e9f0f8;--blue-edge:#c4d5ea;
--indigo:#3739d4;--indigo-tint:#ecebfb;--indigo-edge:#cfcdf6;
--ok-ink:#1d6b2a;--ok-tint:#e8f4ea;--ok-edge:#bcdfc3;--no-ink:#8a4b0f;--no-tint:#fbf1e4;--no-edge:#eed6b5;
--latin:'Montserrat','Hiragino Sans','Hiragino Kaku Gothic ProN','Noto Sans JP',sans-serif}
.block-container{padding-top:3.6rem;max-width:1320px}
.hero{position:relative;overflow:hidden;border-radius:18px;padding:1.7rem 1.9rem 1.5rem;margin:0 0 1.1rem;color:#fff;
background:linear-gradient(118deg,#0e2c4e 0%,#1e5a9f 58%,#3739d4 100%)}
.hero:after{content:"";position:absolute;right:-60px;top:-60px;width:260px;height:260px;border-radius:50%;
background:radial-gradient(circle,rgba(255,255,255,.16),rgba(255,255,255,0) 70%)}
.hero .kicker{font-family:var(--latin);font-size:.74rem;letter-spacing:.24em;font-weight:700;color:rgba(255,255,255,.82)}
.hero .ttl{font-size:2.05rem;line-height:1.25;font-weight:800;margin:.3rem 0 .45rem;color:#fff}
.hero .ttl small{font-family:var(--latin);font-size:1rem;color:rgba(255,255,255,.72);font-weight:600;margin-left:.6rem}
.hero .lead{color:rgba(255,255,255,.9);margin:0 0 1.1rem;max-width:48rem;line-height:1.8}
.stats{display:flex;gap:.7rem;flex-wrap:wrap;position:relative;z-index:1}
.stat{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.24);border-radius:12px;padding:.55rem 1rem;min-width:8rem}
.stat b{display:block;font-family:var(--latin);font-size:1.35rem;font-weight:700;color:#fff;line-height:1.3}
.stat span{font-size:.76rem;color:rgba(255,255,255,.82)}
.resbar{display:flex;align-items:baseline;gap:.2rem .7rem;flex-wrap:wrap}
.resbar .count{font-family:var(--latin);font-size:1.5rem;font-weight:800;color:var(--ink)}
.resbar .count small{font-size:.88rem;color:var(--muted);font-weight:500;margin-left:.2rem}
.fchip{display:inline-block;background:var(--blue-tint);color:var(--blue);border-radius:999px;
padding:.08rem .62rem;font-size:.76rem;margin:.1rem .25rem .1rem 0;font-weight:600}
.legend{font-size:.76rem;color:var(--muted);display:flex;gap:.4rem .9rem;flex-wrap:wrap;align-items:center}
.sec{display:flex;align-items:baseline;gap:.6rem;margin:1.2rem 0 .15rem}
.sec .h{font-size:1.12rem;font-weight:800;color:var(--ink);padding-left:.6rem;border-left:4px solid var(--blue)}
.sec .n{font-family:var(--latin);color:var(--muted);font-size:.9rem}
.note-line{color:var(--muted);font-size:.82rem;margin:.1rem 0 .7rem}
div[class*="st-key-grid_"]{display:grid !important;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));
gap:1rem;align-items:stretch}
div[class*="st-key-grid_"]>div{width:auto !important;min-width:0}
div[class*="st-key-card_"]{height:100%;box-sizing:border-box;background:var(--card);border:1px solid var(--line);
border-top:3px solid var(--blue);border-radius:14px;padding:15px 18px 4px;box-shadow:0 1px 2px rgba(34,34,34,.04);
transition:box-shadow .15s ease,border-color .15s ease}
div[class*="st-key-card_"]:hover{box-shadow:0 10px 26px rgba(30,90,159,.12);border-color:rgba(30,90,159,.35);border-top-color:var(--blue)}
div[class*="st-key-card_"] [data-testid="stCheckbox"] p{font-size:.84rem;color:var(--muted)}
.vc-top{display:flex;justify-content:space-between;align-items:flex-start;gap:.6rem}
.vc-name{font-size:1.06rem;font-weight:800;color:var(--ink);line-height:1.35}
.origin{flex:none;font-size:.72rem;border-radius:999px;padding:.12rem .6rem;white-space:nowrap;font-weight:600}
.origin.jp{background:var(--blue-tint);color:var(--blue)}
.origin.intl{background:#efeeec;color:var(--muted)}
.tags{margin:.4rem 0 0;display:flex;gap:.3rem;flex-wrap:wrap}
.tag{font-size:.72rem;color:var(--muted);background:#f2f1ef;border-radius:6px;padding:.06rem .45rem}
.tag.booth{background:var(--indigo-tint);color:var(--indigo);font-weight:700;font-family:var(--latin)}
.vc-desc{font-size:.88rem;color:var(--text);line-height:1.7;margin:.55rem 0 .5rem;display:-webkit-box;
-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
.chips{display:flex;flex-wrap:wrap;gap:.3rem;margin:.1rem 0 .1rem}
.chip{font-size:.76rem;border-radius:999px;padding:.1rem .6rem;border:1px solid #dcdad6;color:var(--muted);background:#fff}
.chip.main{background:var(--blue);border-color:var(--blue);color:#fff;font-weight:700}
.chip.hit{box-shadow:0 0 0 2px #fff,0 0 0 4px var(--indigo)}
.chip.more{border-style:dashed}
.price{margin:.7rem 0 .35rem;font-size:.84rem;color:var(--ink);display:flex;gap:.55rem;align-items:baseline}
.price .k{flex:none;font-size:.68rem;color:var(--faint);letter-spacing:.08em;border:1px solid var(--line);
border-radius:4px;padding:0 .3rem}
.price .v{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.price.p-yes .v{font-weight:700}
.price.p-no .v{color:var(--no-ink)}
.price.p-unk .v{color:#a0a0a0}
.conds{margin-top:.15rem;min-height:1.2rem}
.cond{display:inline-block;font-size:.74rem;border-radius:6px;padding:.08rem .5rem;border:1px solid transparent;margin:0 .25rem .25rem 0}
.cond.yes{background:var(--ok-tint);border-color:var(--ok-edge);color:var(--ok-ink);font-weight:700}
.cond.no{background:var(--no-tint);border-color:var(--no-edge);color:var(--no-ink)}
.cond.unk{border:1px dashed #d2d0cc;color:#a0a0a0}
.unk-line{font-size:.72rem;color:#a0a0a0;margin-top:.05rem}
.vc-foot{margin:.55rem 0 .1rem;font-size:.84rem}
.vc-foot a,.cmp a,.bc a,.ev a{color:var(--blue-bright);text-decoration:none;font-weight:700}
.vc-foot a:hover,.cmp a:hover,.bc a:hover{text-decoration:underline}
.empty{border:1px dashed #cfccc7;border-radius:14px;padding:1.6rem;color:var(--muted);text-align:center;background:#fff;line-height:1.8}
.st-key-tiles{background:#fff;border:1px solid var(--line);border-radius:14px;padding:.9rem 1.1rem .9rem;gap:.6rem}
.st-key-tiles .ph{font-size:.76rem;font-weight:800;color:var(--blue);letter-spacing:.1em;padding-top:.45rem;white-space:nowrap}
div[class*="st-key-tilerow_"] [data-testid="stButton"] button{border-radius:999px;border:1px solid #dcdad6;
background:#fff;min-height:2rem;padding:.15rem .85rem}
div[class*="st-key-tilerow_"] [data-testid="stButton"] button:hover{background:var(--blue-tint);border-color:var(--blue-edge);color:var(--blue)}
div[class*="st-key-tilerow_"] [data-testid="stButton"] button p{font-size:.88rem}
.ctx{display:flex;gap:.6rem;flex-wrap:wrap;margin:.2rem 0 .1rem}
.ctx-item{background:var(--blue-tint);border:1px solid var(--blue-edge);border-left:4px solid var(--indigo);border-radius:12px;padding:.55rem .95rem}
.ctx-item b{display:block;color:var(--blue)}
.ctx-item span{font-size:.8rem;color:var(--muted)}
.cmp-wrap{overflow-x:auto;margin:.6rem 0 1rem;border:1px solid var(--line);border-radius:14px;background:#fff}
.cmp{display:grid}
.cmp>div{padding:.75rem .95rem;border-bottom:1px solid var(--line);font-size:.86rem;color:var(--ink);line-height:1.65;min-width:0;overflow-wrap:anywhere}
.cmp .rl{color:var(--muted);font-size:.8rem;font-weight:700;background:#faf9f8;position:sticky;left:0;z-index:1;border-right:1px solid var(--line)}
.cmp .vh{background:linear-gradient(180deg,#eef3fa,#f7f9fc);border-bottom:2px solid var(--blue)}
.cmp .vh .nm{font-weight:800;font-size:1.02rem}
.cmp .sub{display:block;color:var(--muted);font-size:.78rem;margin-top:.15rem}
.cmp .src{font-size:.75rem;margin-left:.2rem}
.cmp .chips{gap:.25rem}
.cmp .cmp-sec{background:#f1f5fa;color:var(--blue);font-size:.74rem;font-weight:800;letter-spacing:.1em;padding:.4rem .95rem}
.cmp .cmp-sec span{position:sticky;left:.95rem}
.booths{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:.75rem;margin:.35rem 0 1rem}
.bc{background:#fff;border:1px solid var(--line);border-radius:12px;padding:.8rem .95rem}
.bc .no{font-family:var(--latin);font-size:.84rem;color:var(--indigo);background:var(--indigo-tint);border-radius:6px;
padding:.04rem .45rem;font-weight:800}
.bc .nm{font-weight:800;margin:.45rem 0 .1rem;color:var(--ink)}
.bc .ex{font-size:.8rem;color:var(--blue);margin-bottom:.3rem}
.bc .nt{font-size:.8rem;color:var(--muted);line-height:1.6;display:-webkit-box;-webkit-line-clamp:3;
-webkit-box-orient:vertical;overflow:hidden;margin-bottom:.4rem}
.defs{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:.75rem;margin:.35rem 0 1rem}
.def{background:#fff;border:1px solid var(--line);border-top:3px solid var(--blue);border-radius:12px;padding:.8rem .95rem}
.def b{display:block;margin-bottom:.2rem;color:var(--ink)}
.def p{font-size:.8rem;color:var(--muted);margin:.2rem 0 .45rem;line-height:1.65}
.def .cnt{font-size:.78rem;color:var(--ok-ink);font-weight:700}
.xlist{columns:2 19rem;font-size:.84rem;color:var(--muted)}
.xlist div{break-inside:avoid;margin:0 0 .5rem}
.xlist b{color:var(--ink);font-weight:700}
.ev{font-size:.84rem;color:var(--muted);line-height:1.7}
.ev b{color:var(--ink)}
.ev li{margin-bottom:.2rem}
.foot a{color:var(--blue-bright);text-decoration:none;font-weight:700}
</style>
"""


# ---------------------------------------------------------------------------
# データ
# ---------------------------------------------------------------------------
def _build_module():
    spec = importlib.util.spec_from_file_location("build", ROOT / "scripts" / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@st.cache_data(ttl=600, show_spinner="データを読み込んでいます")
def load_data():
    b = _build_module()
    tbl = {t: b.read(t) for t in b.TABLES}
    errs, warns = b.validate(tbl)
    frames = {t: pd.DataFrame(rows) for t, rows in tbl.items()}
    logs = [pd.read_csv(p, encoding="utf-8-sig", dtype=str).assign(記録=pathlib.Path(p).stem)
            for p in sorted(glob.glob(str(ROOT / "logs" / "*.csv")))]
    frames["logs"] = pd.concat(logs, ignore_index=True) if logs else pd.DataFrame()
    return frames, errs, warns


def build_view(f):
    C = f["categories"].copy()
    C["sort"] = C["sort"].astype(int)
    C = C.sort_values("sort")
    order = dict(zip(C.cat_id, C["sort"]))

    A = f["attributes"].copy()
    A["sort"] = A["sort"].astype(int)
    A = A.sort_values("sort")

    V = f["vendors"]
    V = V[V.status == "active"].copy()
    vc = f["vendor_categories"]
    vc = vc[vc.vendor_id.isin(V.vendor_id)].copy()
    vc["sort"] = vc.cat_id.map(order)
    vc = vc.sort_values(["vendor_id", "sort"])

    all_c = vc.groupby("vendor_id")["cat_id"].apply(list)
    pri_c = vc[vc.role == "主"].groupby("vendor_id")["cat_id"].apply(list)
    ex = f["exhibitions"]
    ex = ex[ex.year.astype(str) == "2026"].drop_duplicates("vendor_id").set_index("vendor_id")

    as_list = lambda x: x if isinstance(x, list) else []
    title = dict(zip(C.cat_id, C.title))
    V["cats"] = V.vendor_id.map(all_c).apply(as_list)
    V["primary"] = V.vendor_id.map(pri_c).apply(as_list)
    V["secondary"] = V.apply(lambda r: [c for c in r["cats"] if c not in r["primary"]], axis=1)
    V["代表工程"] = V["primary"].apply(lambda cs: " / ".join(title[c] for c in cs))
    V["対応工程"] = V["secondary"].apply(lambda cs: " / ".join(title[c] for c in cs))
    V["ブース"] = V.vendor_id.map(ex["booth"]).fillna("")
    V["展示"] = V.vendor_id.map(ex["exhibit_name"]).fillna("")
    V["展示内容"] = V.vendor_id.map(ex["exhibit_note"]).fillna("")
    V["フェア出展"] = V.vendor_id.isin(ex.index)
    V["MCP"] = V.is_mcp.astype(str) == "1"
    V["2026年更新"] = V.is_new_2026.astype(str) == "1"
    V["国内"] = V.region == "日本"

    va = f["vendor_attributes"]
    for a in A.attr_id:
        sub = va[va.attr_id == a].set_index("vendor_id")
        V[a] = V.vendor_id.map(sub["value"]).fillna("未確認")
        V[a + "_note"] = V.vendor_id.map(sub["note"]).fillna("")
        V[a + "_src"] = V.vendor_id.map(sub["source"]).fillna("")

    notes = V[[a + "_note" for a in A.attr_id]].apply(lambda r: " ".join(r), axis=1)
    V["_hay"] = (V.name + " " + V.description + " " + V.country + " " + V["展示"] + " "
                 + V["展示内容"] + " " + V["ブース"] + " " + notes + " "
                 + V["cats"].apply(lambda cs: " ".join(title[c] for c in cs))).str.lower()
    V["_name"] = V.name.str.lower()
    V["_booth"] = V["ブース"].replace("", "ZZZ")
    V["_intl"] = ~V["国内"]
    return V.sort_values(["_intl", "_name"]).reset_index(drop=True), C, A, vc


frames, errs, warns = load_data()
if errs:
    st.error("データに不整合があるため表示を止めています。`data/*.csv` を修正してください。")
    for e in errs:
        st.write("・", e)
    st.stop()

V, C, A, VC = build_view(frames)
CAT_IDS = C.cat_id.tolist()
TITLE = dict(zip(C.cat_id, C.title))
SHORT = dict(zip(C.cat_id, C.short))
SUBTITLE = dict(zip(C.cat_id, C.subtitle))
PHASES = list(dict.fromkeys(C.phase))
CATS_BY_PHASE = {ph: C[C.phase == ph].cat_id.tolist() for ph in PHASES}
ATTR_IDS = A.attr_id.tolist()
ATTR_LABEL = dict(zip(A.attr_id, A.label))
ATTR_SHORT = dict(zip(A.attr_id, A.short))
ATTR_DEF = dict(zip(A.attr_id, A.definition))
NO_LABEL = {"pricing": "料金は問い合わせ"}     # 「なし」をカードでどう書くか
UPDATED = frames["vendors"].updated_at.max()


def esc(s):
    """HTMLに埋め込む文字列の無害化（$ は数式記法として解釈されないよう実体参照にする）"""
    return html.escape(str(s or ""), quote=True).replace("$", "&#36;")


# ---------------------------------------------------------------------------
# 状態と操作
# ---------------------------------------------------------------------------
ss = st.session_state
DEFAULTS = {"q": "", "primary_only": False, "match": "どれかに対応", "origin": "すべて"}
DEFAULTS.update({f"ph_{i}": [] for i in range(len(PHASES))})
DEFAULTS.update({f"a_{a}": False for a in ATTR_IDS})
for k, v in DEFAULTS.items():
    ss.setdefault(k, list(v) if isinstance(v, list) else v)
ss.setdefault("shortlist", [])
ss.setdefault("sort", SORTS[0])


def reset_filters():
    for k, v in DEFAULTS.items():
        ss[k] = list(v) if isinstance(v, list) else v
    for k in [k for k in ss.keys() if str(k).startswith("lim_")]:
        del ss[k]


def toggle_compare(vid):
    on = ss.get(f"cmp_{vid}", False)
    sl = ss.shortlist
    if on and vid not in sl:
        if len(sl) >= MAX_COMPARE:
            st.toast(f"比較できるのは{MAX_COMPARE}社までです。「比較する」タブで外してから追加してください。")
            return
        sl.append(vid)
    elif not on and vid in sl:
        sl.remove(vid)


def sync_pick():
    ss.shortlist = list(ss.cmp_pick)


def add_compare(vid):
    if vid not in ss.shortlist and len(ss.shortlist) < MAX_COMPARE:
        ss.shortlist.append(vid)


def select_task(cid):
    """入口のボタンから業務を1つ選ぶ（サイドバーの業務ボタンと同じ状態を使う）"""
    for i, ph in enumerate(PHASES):
        ss[f"ph_{i}"] = [cid] if cid in CATS_BY_PHASE[ph] else []
    for k in [k for k in ss.keys() if str(k).startswith("lim_")]:
        del ss[k]


def clear_tasks():
    for i in range(len(PHASES)):
        ss[f"ph_{i}"] = []


def clear_compare():
    ss.shortlist = []


def more(key):
    ss[f"lim_{key}"] = ss.get(f"lim_{key}", PAGE) + PAGE


def go_compare():
    ss.tab = "比較する"


# ---------------------------------------------------------------------------
# サイドバー：探し方の条件（すべてのタブに効く）
# ---------------------------------------------------------------------------
with st.sidebar:
    st.text_input("キーワード", key="q", placeholder="社名・製品名・特徴で探す")

    st.markdown("**やりたい業務**")
    for i, ph in enumerate(PHASES):
        st.pills(ph, CATS_BY_PHASE[ph], format_func=SHORT.get, selection_mode="multi", key=f"ph_{i}")
    n_sel = sum(len(ss[f"ph_{i}"] or []) for i in range(len(PHASES)))
    st.toggle("主力として提供している社だけ", key="primary_only",
              help="オフにすると、その業務を機能の一部として持つ社も含めます。")
    if n_sel >= 2:
        st.radio("複数の業務を選んだとき", ["どれかに対応", "すべてに対応"], key="match", horizontal=True)

    st.markdown("**導入条件**")
    for a in ATTR_IDS:
        n = int((V[a] == "あり").sum())
        st.checkbox(f"{ATTR_LABEL[a]}（{n}）", key=f"a_{a}", help=ATTR_DEF[a])
    st.caption("公式情報で確認できた社だけに絞ります。確認できなかった社は「未確認」で、"
               "提供していないとは限りません。")

    st.markdown("**ベンダーの拠点**")
    st.segmented_control("ベンダーの拠点", ["すべて", "国内", "海外"], key="origin",
                         label_visibility="collapsed")
    st.button("条件をすべて解除", on_click=reset_filters, width="stretch")


# ---------------------------------------------------------------------------
# 絞り込み
# ---------------------------------------------------------------------------
SEL = [c for i in range(len(PHASES)) for c in (ss[f"ph_{i}"] or [])]
role_col = "primary" if ss.primary_only else "cats"
mask = pd.Series(True, index=V.index)
if SEL:
    want = set(SEL)
    if len(SEL) > 1 and ss.match == "すべてに対応":
        mask &= V[role_col].apply(lambda cs: want <= set(cs))
    else:
        mask &= V[role_col].apply(lambda cs: bool(want & set(cs)))
for a in ATTR_IDS:
    if ss[f"a_{a}"]:
        mask &= V[a] == "あり"
if ss.origin == "国内":
    mask &= V["国内"]
elif ss.origin == "海外":
    mask &= ~V["国内"]
for term in ss.q.lower().split():
    mask &= V["_hay"].str.contains(term, regex=False)
H = V[mask].reset_index(drop=True)


# ---------------------------------------------------------------------------
# カードと比較の部品
# ---------------------------------------------------------------------------
def task_chips(r, limit_sub=5):
    out = [f'<span class="chip main{" hit" if c in SEL else ""}">{esc(SHORT[c])}</span>' for c in r["primary"]]
    sub = r["secondary"]
    out += [f'<span class="chip{" hit" if c in SEL else ""}">{esc(SHORT[c])}</span>' for c in sub[:limit_sub]]
    if len(sub) > limit_sub:
        out.append(f'<span class="chip more">+{len(sub) - limit_sub}</span>')
    return "".join(out)


def price_text(r):
    """料金の一言（カードと比較の列見出しで使う）"""
    return {"あり": r["pricing_note"] or "料金を公開", "なし": "問い合わせ・個別見積"}.get(r["pricing"], "未確認")


def price_html(r):
    cls = {"あり": "p-yes", "なし": "p-no"}.get(r["pricing"], "p-unk")
    return (f'<div class="price {cls}" title="{esc(r["pricing_note"])}">'
            f'<span class="k">料金</span><span class="v">{esc(price_text(r))}</span></div>')


def cond_line(r):
    """確認できた導入条件は札で、確認できなかったものは1行にまとめる（料金は別の行で出す）"""
    ids = [a for a in ATTR_IDS if a != "pricing"]
    yes = [a for a in ids if r[a] == "あり"]
    unk = [a for a in ids if r[a] != "あり"]
    chips = "".join(f'<span class="cond yes" title="{esc(r[a + "_note"])}">✓ {esc(ATTR_SHORT[a])}</span>'
                    for a in yes)
    rest = (f'<div class="unk-line">未確認：{"／".join(esc(ATTR_SHORT[a]) for a in unk)}</div>' if unk else "")
    return chips + rest


def origin_badge(r):
    if r["国内"]:
        return '<span class="origin jp">国内</span>'
    return f'<span class="origin intl">海外・{esc(r["country"])}</span>'


def card_html(r):
    booth = (f'<span class="tag booth">ブース {esc(r["ブース"])}</span>' if r["ブース"]
             else ('<span class="tag booth">フェア出展</span>' if r["フェア出展"] else ""))
    link = (f'<a href="{esc(r["url"])}" target="_blank" rel="noopener">公式サイト ↗</a>'
            if r["url"] else '<span style="color:#8b95a3">公式サイト未確認</span>')
    return ("<div>"
            f'<div class="vc-top"><div class="vc-name">{esc(r["name"])}</div>{origin_badge(r)}</div>'
            + (f'<div class="tags">{booth}</div>' if booth else "")
            + f'<div class="vc-desc" title="{esc(r["description"])}">{esc(r["description"])}</div>'
            f'<div class="chips">{task_chips(r)}</div>'
            f"{price_html(r)}"
            f'<div class="conds">{cond_line(r)}</div>'
            f'<div class="vc-foot">{link}</div>'
            "</div>")


def card(r):
    vid = r["vendor_id"]
    with st.container(key=f"card_{vid}"):
        st.markdown(card_html(r), unsafe_allow_html=True)
        ss[f"cmp_{vid}"] = vid in ss.shortlist
        st.checkbox("比較に追加", key=f"cmp_{vid}", on_change=toggle_compare, args=(vid,))


def sort_frame(fr):
    s = ss.get("sort") or SORTS[0]
    fr = fr.copy()
    fr["_hit"] = fr["cats"].apply(lambda cs: -len(set(SEL) & set(cs))) if len(SEL) > 1 else 0
    keys = {"社名順": ["_hit", "_name"], "ブース順": ["_hit", "_booth", "_name"]}.get(
        s, ["_hit", "_intl", "_name"])
    return fr.sort_values(keys)


def section(title, note, frame, key):
    frame = sort_frame(frame)
    st.markdown(f'<div class="sec"><span class="h">{esc(title)}</span><span class="n">{len(frame)}社</span></div>'
                + (f'<div class="note-line">{esc(note)}</div>' if note else ""), unsafe_allow_html=True)
    lim = ss.get(f"lim_{key}", PAGE)
    show = frame.head(lim)
    # 列数は画面幅に合わせて変わる（CSSグリッド。1枚の幅が約290pxを下回らないようにする）
    with st.container(key=f"grid_{key}"):
        for _, r in show.iterrows():
            card(r)
    if len(frame) > lim:
        st.button(f"さらに表示（残り{len(frame) - lim}社）", key=f"more_{key}", on_click=more, args=(key,))


def attr_cell(r, a):
    v, note, src = r[a], r[a + "_note"], r[a + "_src"]
    head = {"あり": '<span class="cond yes">✓ あり</span>',
            "なし": f'<span class="cond no">{esc(NO_LABEL.get(a, "なし"))}</span>'}.get(
        v, '<span class="cond unk">未確認</span>')
    link = (f'<a class="src" href="{esc(src)}" target="_blank" rel="noopener">'
            f'{"根拠" if v != "未確認" else "参考"} ↗</a>' if src else "")
    return head + link + (f'<span class="sub">{esc(note)}</span>' if note else "")


DASH = '<span class="sub">—</span>'


def chips_or_dash(cs, cls):
    if not cs:
        return DASH
    return '<div class="chips">' + "".join(f'<span class="chip {cls}">{esc(SHORT[c])}</span>' for c in cs) + "</div>"


def compare_html(P, diff_only=False):
    """列見出しに社名・拠点・料金、行はセクションに分ける。diff_only なら値が全社同じ行を省く"""
    rows = [(None, r) for _, r in P.iterrows()]
    sections = [
        ("概要", [
            ("拠点", lambda r: "国内" if r["国内"] else f"海外（{esc(r['country'])}）"),
            ("紹介", lambda r: esc(r["description"])),
        ]),
        ("業務", [
            ("主力の業務", lambda r: chips_or_dash(r["primary"], "main")),
            ("対応している業務", lambda r: chips_or_dash(r["secondary"], "")),
        ]),
        ("導入条件", [(ATTR_LABEL[a], lambda r, a=a: attr_cell(r, a)) for a in ATTR_IDS]),
        ("知財・情報フェア2026", [
            ("ブース・展示", lambda r: (
                f'<span class="tag booth">ブース {esc(r["ブース"] or "番号未取得")}</span> {esc(r["展示"])}'
                f'<span class="sub">{esc(r["展示内容"])}</span>') if r["フェア出展"] else '<span class="sub">出展なし</span>'),
        ]),
        ("掲載時の記載", [
            ("提供形態", lambda r: esc(r["deployment"]) or DASH),
        ]),
    ]
    cells = ['<div class="rl"></div>']
    for _, r in rows:
        link = (f'<a href="{esc(r["url"])}" target="_blank" rel="noopener">公式サイト ↗</a>'
                if r["url"] else "")
        cells.append(f'<div class="vh"><span class="nm">{esc(r["name"])}</span> {origin_badge(r)}'
                     f'<span class="sub">料金：{esc(price_text(r))}</span><span class="sub">{link}</span></div>')
    hidden = 0
    for sec, items in sections:
        body = []
        for label, fn in items:
            vals = [fn(r) for _, r in rows]
            if diff_only and len(vals) > 1 and len(set(vals)) == 1:
                hidden += 1
                continue
            body.append(f'<div class="rl">{esc(label)}</div>' + "".join(f"<div>{v}</div>" for v in vals))
        if body:
            cells.append(f'<div class="cmp-sec" style="grid-column:1 / -1"><span>{esc(sec)}</span></div>')
            cells += body
    # 列は最小230pxで均等に分ける。文章は列の中で折り返す（最小幅の合計より狭い画面では横にスクロール）
    grid = (f"grid-template-columns:10.5rem repeat({len(rows)}, minmax(230px, 1fr));"
            f"min-width:calc(10.5rem + {len(rows) * 230}px)")
    return f'<div class="cmp-wrap"><div class="cmp" style="{grid}">{"".join(cells)}</div></div>', hidden


def suggestions(P, k=8):
    """比較中の社と主力の業務が重なる社（まだ比較に入れていないもの）"""
    prim = {c for cs in P["primary"] for c in cs}
    cand = V[~V.vendor_id.isin(ss.shortlist)].copy()
    cand["_ov"] = cand["primary"].apply(lambda cs: -len(prim & set(cs)))
    cand = cand[cand["_ov"] < 0]
    return cand.sort_values(["_ov", "_intl", "_name"]).head(k)


def compare_csv(P):
    out = pd.DataFrame({
        "社名": P.name, "拠点": P["国内"].map({True: "国内", False: "海外"}), "国": P.country,
        "主力の業務": P["代表工程"], "対応している業務": P["対応工程"]})
    for a in ATTR_IDS:
        out[ATTR_LABEL[a]] = P[a].values
        out[f"{ATTR_LABEL[a]}（メモ）"] = P[a + "_note"].values
        out[f"{ATTR_LABEL[a]}（根拠）"] = P[a + "_src"].values
    out["提供形態（掲載時の記載）"] = P.deployment.values
    out["知財・情報フェア2026のブース"] = P["ブース"].values
    out["紹介"] = P.description.values
    out["公式サイト"] = P.url.values
    return out.to_csv(index=False).encode("utf-8-sig")


def evidence_html(P):
    parts = []
    for _, r in P.iterrows():
        rows = VC[VC.vendor_id == r["vendor_id"]]
        items = "".join(
            f'<li><b>{esc(TITLE[x.cat_id])}</b>（{"主力" if x.role == "主" else "対応"}）'
            f'　{esc(x.source) or "—"}　<span style="color:#8b95a3">{esc(x.checked_at)}</span></li>'
            for x in rows.itertuples())
        parts.append(f'<div class="ev"><b>{esc(r["name"])}</b><ul>{items}</ul></div>')
    return "".join(parts)


# ---------------------------------------------------------------------------
# 見出し
# ---------------------------------------------------------------------------
st.html(CSS)
st.markdown(
    '<div class="hero"><div class="kicker">LEXI/VENT ・ 生成AI × 知財 ベンダー名鑑</div>'
    f'<div class="ttl">{esc(APP_NAME)}<small>{esc(EDITION)}</small></div>'
    '<p class="lead">知財部門のAIツール選びの下調べに。やりたい業務から候補を探し、'
    '導入条件で絞り込み、気になる社を横に並べて比べられます。</p>'
    '<div class="stats">'
    f'<div class="stat"><b>{len(V)}</b><span>掲載ベンダー</span></div>'
    f'<div class="stat"><b>{len(C)}</b><span>業務工程</span></div>'
    f'<div class="stat"><b>{int(V["フェア出展"].sum())}</b><span>知財・情報フェア2026 出展</span></div>'
    f'<div class="stat"><b>{esc(UPDATED)}</b><span>最終更新</span></div>'
    "</div></div>", unsafe_allow_html=True)

active = []
if ss.q:
    active.append(f"「{ss.q}」")
active += [SHORT[c] for c in SEL]
if SEL and ss.primary_only:
    active.append("主力のみ")
if len(SEL) > 1 and ss.match == "すべてに対応":
    active.append("選んだ業務すべてに対応")
active += [ATTR_SHORT[a] for a in ATTR_IDS if ss[f"a_{a}"]]
if ss.origin in ("国内", "海外"):
    active.append(f"{ss.origin}ベンダー")

with st.container(horizontal=True, vertical_alignment="center", gap="medium", key="resbar"):
    st.markdown(
        f'<div class="resbar"><span class="count">{len(H)}<small>社 ／ 全{len(V)}社</small></span>'
        + "".join(f'<span class="fchip">{esc(x)}</span>' for x in active) + "</div>",
        unsafe_allow_html=True, width="stretch")
    if ss.shortlist:
        st.button(f"比較する（{len(ss.shortlist)}社）", on_click=go_compare, type="primary",
                  icon=":material/compare_arrows:", width="content")

t_find, t_cmp, t_map, t_fair, t_data = st.tabs(TABS, key="tab", on_change="rerun")


# ---------------------------------------------------------------------------
# 探す
# ---------------------------------------------------------------------------
LEGEND = ('<div class="legend"><span><span class="chip main">濃い</span> 主力の業務</span>'
          '<span><span class="chip">薄い</span> 対応している業務</span>'
          '<span><span class="cond yes">✓</span> 公式情報で確認できた導入条件</span></div>')


def task_tiles():
    """業務の入口。押すとその業務で絞り込む（サイドバーの業務ボタンと同じ状態）"""
    st.markdown('<div class="sec"><span class="h">やりたい業務から探す</span></div>'
                '<div class="note-line">業務を選ぶと、その業務を主力にする社と、機能の一部として対応する社に分けて表示します。'
                '数字は、いまの条件に当てはまる社数です。</div>', unsafe_allow_html=True)
    # フェーズごとに見出しを置き、業務のボタンは横に流して折り返す（狭い画面でも文字が縦に割れない）
    with st.container(key="tiles"):
        for i, ph in enumerate(PHASES):
            with st.container(horizontal=True, gap="small", key=f"tilephase_{i}"):
                st.markdown(f'<div class="ph">{esc(ph)}</div>', unsafe_allow_html=True, width=96)
                with st.container(horizontal=True, gap="small", key=f"tilerow_{i}"):
                    for cid in CATS_BY_PHASE[ph]:
                        n = int(H["cats"].apply(lambda cs: cid in cs).sum())
                        st.button(f"{SHORT[cid]} :gray[{n}社]", key=f"tile_{cid}", on_click=select_task,
                                  args=(cid,), help=f"{TITLE[cid]}：{SUBTITLE[cid]}", width="content",
                                  disabled=n == 0)


def task_context():
    items = "".join(f'<div class="ctx-item"><b>{esc(TITLE[c])}</b><span>{esc(SUBTITLE[c])}</span></div>'
                    for c in SEL)
    st.markdown(f'<div class="ctx">{items}</div>', unsafe_allow_html=True)
    st.button("業務の選択を解除", on_click=clear_tasks, type="tertiary", icon=":material/close:")


with t_find:
    if t_find.open:
        if SEL:
            task_context()
        if H.empty:
            st.markdown('<div class="empty">条件に合うベンダーがありません。<br>'
                        '業務や導入条件を減らすか、キーワードを変えてください。</div>', unsafe_allow_html=True)
        else:
            if not SEL:
                task_tiles()
            with st.container(horizontal=True, vertical_alignment="center", gap="medium", key="toolbar"):
                st.markdown(LEGEND, unsafe_allow_html=True, width="stretch")
                st.segmented_control("並び順", SORTS, key="sort", label_visibility="collapsed", width="content")
            if SEL:
                hit = H["primary"].apply(lambda cs: bool(set(SEL) & set(cs)))
                section("主力として提供", "選んだ業務を、その社の代表的な機能として提供している。", H[hit], "main")
                if (~hit).any():
                    section("機能の一部として対応", "選んだ業務にも対応しているが、主力は別の業務。", H[~hit], "sub")
            else:
                section("掲載ベンダー", None, H, "all")


# ---------------------------------------------------------------------------
# 比較する
# ---------------------------------------------------------------------------
with t_cmp:
    if t_cmp.open:
        names = dict(zip(V.vendor_id, V.name))
        ss["cmp_pick"] = list(ss.shortlist)
        st.multiselect(f"比較する社（最大{MAX_COMPARE}社）", V.vendor_id.tolist(), format_func=names.get,
                       key="cmp_pick", max_selections=MAX_COMPARE, on_change=sync_pick,
                       placeholder="社名を入力して追加できます")
        if not ss.shortlist:
            st.markdown('<div class="empty">「探す」タブのカードで「比較に追加」を選ぶと、ここに横並びで表示します。<br>'
                        '上の欄に社名を入力して追加することもできます。</div>', unsafe_allow_html=True)
        else:
            P = V.set_index("vendor_id").loc[ss.shortlist].reset_index()
            diff = st.toggle("違いのある行だけ表示", key="cmp_diff", disabled=len(P) < 2)
            board, hidden = compare_html(P, diff_only=diff)
            st.markdown(board, unsafe_allow_html=True)
            if diff and hidden:
                st.caption(f"全社で同じ内容の {hidden} 行を省いています。")
            sug = suggestions(P)
            if not sug.empty and len(ss.shortlist) < MAX_COMPARE:
                st.markdown('<div class="note-line" style="margin-top:.4rem">同じ業務を主力にしている社を比較に足す</div>',
                            unsafe_allow_html=True)
                with st.container(horizontal=True, gap="small", key="sugs"):
                    for _, r in sug.iterrows():
                        st.button(r["name"], key=f"sug_{r['vendor_id']}", on_click=add_compare,
                                  args=(r["vendor_id"],), icon=":material/add:")
            d1, d2, _ = st.columns([1.4, 1.1, 3])
            d1.download_button("比較をCSVで保存", compare_csv(P), file_name="ipai_compare.csv",
                               mime="text/csv", width="stretch")
            d2.button("比較をすべて外す", on_click=clear_compare, width="stretch")
            st.caption("導入条件の「未確認」は、公式情報で確認できなかったという意味で、提供していないとは限りません。"
                       "根拠のリンク先と確認日（2026年9月27日）をあわせて確かめてください。")
            with st.expander("業務（工程）を割り当てた根拠を見る"):
                st.markdown(evidence_html(P), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 市場の全体像
# ---------------------------------------------------------------------------
def counts_by_category(frame):
    ids = set(frame.vendor_id)
    x = VC[VC.vendor_id.isin(ids)].copy()
    x["区分"] = x.role.map({"主": "代表的な工程", "副": "対応している工程"})
    t = x.groupby(["cat_id", "区分"]).size().rename("社数").reset_index()
    t["工程"] = t.cat_id.map(lambda c: f"{c} {TITLE[c]}")
    return t


def render_maps():
    """工程マップのグラフ2点。サイドバーの絞り込み結果 H を使う"""
    st.markdown(f'<div class="note-line">いまの絞り込み条件に当てはまる {len(H)}社 で集計しています。</div>',
                unsafe_allow_html=True)
    st.markdown("##### 工程ごとの社数")
    st.caption("濃い部分は、その工程を代表的な機能としている社。薄い部分は、対応はしているが主力ではない社。")
    # 凡例はグラフの外に置く（Vegaの上部凡例は、狭い画面だと右端が切れるため）
    st.markdown(
        '<div style="font-size:0.875rem;margin-bottom:0.25rem">'
        f'<span style="color:{C_PRIMARY}">■</span> 代表的な工程&emsp;'
        f'<span style="color:{C_SECONDARY}">■</span> 対応している工程</div>',
        unsafe_allow_html=True)
    t = counts_by_category(H)
    order_labels = [f"{c} {TITLE[c]}" for c in CAT_IDS]
    totals = t.groupby("工程", as_index=False)["社数"].sum()
    base = alt.Chart(t).encode(y=alt.Y("工程:N", sort=order_labels, title=None,
                                      axis=alt.Axis(labelLimit=260, ticks=False, domain=False)))
    bars = base.mark_bar(stroke=SURFACE, strokeWidth=2).encode(
        x=alt.X("sum(社数):Q", title="社数", axis=alt.Axis(tickMinStep=1, grid=True)),
        color=alt.Color("区分:N", scale=alt.Scale(domain=["代表的な工程", "対応している工程"],
                                                  range=[C_PRIMARY, C_SECONDARY]),
                        legend=None),
        order=alt.Order("区分:N", sort="ascending"),
        tooltip=["工程:N", "区分:N", "社数:Q"])
    labels = alt.Chart(totals).mark_text(align="left", dx=6, color="#555555", fontSize=12).encode(
        y=alt.Y("工程:N", sort=order_labels), x="社数:Q", text="社数:Q")
    st.altair_chart((bars + labels).properties(height=34 * len(CAT_IDS)), width="stretch")
    with st.expander("表で見る"):
        pv = t.pivot_table(index="工程", columns="区分", values="社数", aggfunc="sum", fill_value=0)
        pv = pv.reindex([l for l in order_labels if l in pv.index])
        pv["合計"] = pv.sum(axis=1)
        st.dataframe(pv, width="stretch")

    st.markdown("##### 工程 × 地域")
    x = VC[VC.vendor_id.isin(H.vendor_id)].merge(H[["vendor_id", "region"]], on="vendor_id")
    hm = x.groupby(["cat_id", "region"]).size().rename("社数").reset_index()
    hm["工程"] = hm.cat_id.map(lambda c: f"{c} {TITLE[c]}")
    vmax = int(hm["社数"].max())
    # 狭い画面では列見出しが間引かれることがあるので、列の並びを文章でも示す
    cols = [r for r in REGIONS if r in set(hm.region)]
    st.caption(f"列は左から {'／'.join(cols)}。マスの数字が社数で、色が濃いほど多い。"
               "空白のマスは0社。対応している工程も含めて数えている。")
    base = alt.Chart(hm).encode(
        y=alt.Y("工程:N", sort=order_labels, title=None,
                axis=alt.Axis(labelLimit=260, ticks=False, domain=False)),
        # 「アジア・他」だけ長いので2行に折る。幅800px程度でも4列の見出しが収まる
        # （スマホ幅では間引かれるので、上の説明文で列の並びを示している）
        x=alt.X("region:N", sort=REGIONS, title=None,
                axis=alt.Axis(orient="top", labelAngle=0, ticks=False, domain=False,
                              labelFontSize=11,
                              labelExpr="datum.value == 'アジア・他' ? ['アジア・', '他'] : datum.value")))
    # 色の凡例は置かない。各マスに社数を書いているので、凡例の幅をマスに回す（スマホで列が潰れていた）
    rect = base.mark_rect(stroke=SURFACE, strokeWidth=2, cornerRadius=3).encode(
        color=alt.Color("社数:Q", scale=alt.Scale(range=SEQ_RAMP, domain=[0, vmax]), legend=None),
        tooltip=["工程:N", alt.Tooltip("region:N", title="地域"), "社数:Q"])
    text = base.mark_text(fontSize=12).encode(
        text="社数:Q",
        color=alt.condition(f"datum['社数'] >= {max(2, vmax * 0.55):.1f}",
                            alt.value("#ffffff"), alt.value("#222222")))
    st.altair_chart((rect + text).properties(height=30 * len(CAT_IDS)), width="stretch")
    with st.expander("表で見る"):
        pv2 = hm.pivot_table(index="工程", columns="region", values="社数", fill_value=0)
        pv2 = pv2.reindex(index=[l for l in order_labels if l in pv2.index],
                          columns=[r for r in REGIONS if r in pv2.columns])
        st.dataframe(pv2.astype(int), width="stretch")


with t_map:
    if t_map.open:
        if H.empty:
            st.markdown('<div class="empty">該当するベンダーがないため、グラフを描けません。</div>',
                        unsafe_allow_html=True)
        else:
            try:
                render_maps()
            except Exception as exc:  # グラフの不具合で一覧やダウンロードまで止めない
                st.warning(f"グラフを描画できませんでした（{type(exc).__name__}）。"
                           "一覧とダウンロードは引き続き使えます。")


# ---------------------------------------------------------------------------
# 知財・情報フェア2026
# ---------------------------------------------------------------------------
def booth_card(r):
    tasks = "".join(f'<span class="chip main">{esc(SHORT[c])}</span>' for c in r["primary"])
    ok = "".join(f'<span class="cond yes">✓ {esc(ATTR_SHORT[a])}</span>' for a in ATTR_IDS if r[a] == "あり")
    link = f'<a href="{esc(r["url"])}" target="_blank" rel="noopener">公式サイト ↗</a>' if r["url"] else ""
    return (f'<div class="bc"><span class="no">{esc(r["ブース"] or "番号未取得")}</span>'
            f'<div class="nm">{esc(r["name"])}</div>'
            + (f'<div class="ex">{esc(r["展示"])}</div>' if r["展示"] else "")
            + (f'<div class="nt" title="{esc(r["展示内容"])}">{esc(r["展示内容"])}</div>' if r["展示内容"] else "")
            + f'<div class="chips">{tasks}</div>'
            + (f'<div style="margin-top:.4rem">{ok}</div>' if ok else "")
            + f'<div style="margin-top:.35rem;font-size:.82rem">{link}</div></div>')


with t_fair:
    if t_fair.open:
        st.markdown(f'<div class="note-line">{esc(FAIR)}の出展社のうち、AI・生成AIを組み込んだ製品を公表していた社。'
                    'ブース番号順に、会場の列ごとに並べています。サイドバーの条件も効きます。</div>',
                    unsafe_allow_html=True)
        F = H[H["フェア出展"]].copy()
        if F.empty:
            st.markdown('<div class="empty">条件に合う出展社がありません。</div>', unsafe_allow_html=True)
        else:
            F = F.sort_values(["_booth", "_name"])
            F["_zone"] = F["ブース"].str.extract(r"^(\d+-[A-Z]+)", expand=False).fillna("")
            for zone, g in F.groupby("_zone", sort=False):
                head = f"{zone[-1]}列（{zone}）" if zone else "ブース番号を取得できなかった社"
                st.markdown(f'<div class="sec"><span class="h">{esc(head)}</span><span class="n">{len(g)}社</span></div>'
                            f'<div class="booths">{"".join(booth_card(r) for _, r in g.iterrows())}</div>',
                            unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 掲載基準・データ
# ---------------------------------------------------------------------------
def export_frame(frame):
    out = frame[["vendor_id", "name", "region", "country", "代表工程", "対応工程",
                 *ATTR_IDS, "deployment", "MCP", "2026年更新", "フェア出展", "ブース", "展示",
                 "description", "url"]].copy()
    return out.rename(columns={"name": "社名", "region": "地域", "country": "国",
                               "代表工程": "主力の業務", "対応工程": "対応している業務",
                               **{a: ATTR_LABEL[a] for a in ATTR_IDS},
                               "deployment": "提供形態（掲載時の記載）", "description": "紹介",
                               "url": "公式サイト"})


def evidence_frame():
    va = frames["vendor_attributes"].merge(V[["vendor_id", "name"]], on="vendor_id")
    va["attr"] = va.attr_id.map(ATTR_LABEL)
    return va[["name", "attr", "value", "note", "source", "checked_at"]].rename(
        columns={"name": "社名", "attr": "導入条件", "value": "判定", "note": "メモ",
                 "source": "根拠", "checked_at": "確認日"})


with t_data:
    if t_data.open:
        st.markdown('<div class="sec"><span class="h">データを取り出す</span></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.download_button(f"絞り込み結果をCSVで（{len(H)}社）",
                           export_frame(H).to_csv(index=False).encode("utf-8-sig"),
                           file_name="ipai_vendors_filtered.csv", mime="text/csv", width="stretch")
        xbuf = io.BytesIO()
        with pd.ExcelWriter(xbuf, engine="openpyxl") as w:
            export_frame(V).to_excel(w, sheet_name="vendors", index=False)
            evidence_frame().to_excel(w, sheet_name="導入条件の根拠", index=False)
            frames["excluded"].to_excel(w, sheet_name="excluded", index=False)
        c2.download_button(f"全件をExcelで（{len(V)}社）", xbuf.getvalue(),
                           file_name="ipai_vendors.xlsx", width="stretch",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        js = {"updated": UPDATED, "vendors": export_frame(V).to_dict(orient="records")}
        c3.download_button("全件をJSONで", json.dumps(js, ensure_ascii=False, indent=1).encode("utf-8"),
                           file_name="ipai_vendors.json", mime="application/json", width="stretch")
        st.caption(f"元データ（CSV・SQLite）と更新の履歴は [GitHub]({REPO_URL}) で公開しています。"
                   f"掲載漏れや誤りは [Issue で知らせてください]({REPO_URL}/issues/new)。")

        st.markdown('<div class="sec"><span class="h">掲載基準</span></div>', unsafe_allow_html=True)
        st.markdown("AI・生成AIを組み込んだ製品またはサービスを、公開情報で確認できるベンダーに限ります。"
                    "業務（工程）は、カオスマップ上の配置にあたる「主力の業務」と、公式情報で提供を確認できた"
                    "「対応している業務」に分けて登録し、それぞれに根拠を記録しています。")

        st.markdown('<div class="sec"><span class="h">導入条件の定義と調べ方</span></div>', unsafe_allow_html=True)
        defs = "".join(
            f'<div class="def"><b>{esc(ATTR_LABEL[a])}</b><p>{esc(ATTR_DEF[a])}</p>'
            f'<span class="cnt">あり {int((V[a] == "あり").sum())}社</span>'
            + (f'<span style="color:#8a4b0f;font-size:.78rem;margin-left:.6rem">なし {int((V[a] == "なし").sum())}社</span>'
               if (V[a] == "なし").any() else "")
            + "</div>" for a in ATTR_IDS)
        st.markdown(f'<div class="defs">{defs}</div>', unsafe_allow_html=True)
        st.markdown("2026年9月27日に各社の公式サイト（トップページと、料金・セキュリティ・FAQ・トライアルなどの関連ページ）を"
                    "確認し、該当する記載があったものだけを「あり」としました。記載を見つけられなかったものは「未確認」で、"
                    "提供していないという意味ではありません。JavaScriptで描画するサイトや自動取得を拒否しているサイトなど、"
                    "本文を読めなかった社は、ほかの公式情報で確認できた項目を除いて「未確認」です。"
                    "判定ごとの根拠URLと確認日は、Excelの「導入条件の根拠」シートと GitHub の "
                    "`data/vendor_attributes.csv` にあります。")

        X = frames["excluded"]
        with st.expander(f"掲載基準から外した機関・企業（{len(X)}）"):
            st.caption("公的機関、業界団体、教育機関、AI活用を公表していない事業者など。"
                       "除外はAI搭載の有無という一点の判定で、事業の価値や実務上の重要性を評価したものではありません。")
            st.markdown('<div class="xlist">' + "".join(
                f'<div><b>{esc(x.name)}</b>（{esc(x.kind)}）<br>{esc(x.reason)}</div>' for x in X.itertuples())
                + "</div>", unsafe_allow_html=True)

        L = frames["logs"]
        if not L.empty:
            with st.expander(f"更新の履歴（{len(L)}件）"):
                st.dataframe(L, hide_index=True, width="stretch")
        if warns:
            with st.expander(f"確認中の項目（{len(warns)}件）"):
                for w_ in warns:
                    st.write("・", w_)

st.divider()
st.caption("出典：各社公式サイト・プレスリリース、2026 知財・情報フェア＆コンファレンス出展社情報。"
           "機能の実効性は検証していません。紹介文の数値は各社の公表値です。　"
           "整理：上村侑太郎（[LeXi/Vent](https://lexi2vent.com/)）")
