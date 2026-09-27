# -*- coding: utf-8 -*-
"""
知財AIベンダー名鑑（Streamlit版）

データの正本は data/*.csv。起動時に読み込み、scripts/build.py と同じ検査を通してから表示する。
CSVを直して push すれば、Streamlit Community Cloud 上の表示もそのまま更新される。

ローカルで動かす:
    pip install -r requirements.txt
    streamlit run streamlit_app.py
"""

import glob
import importlib.util
import io
import json
import pathlib

import altair as alt
import pandas as pd
import streamlit as st

APP_NAME = "知財AIベンダー名鑑 2026.9"          # 名称を変えるときはここだけ
REPO_URL = "https://github.com/muu4649/ip-ai-vendor-db"
ROOT = pathlib.Path(__file__).parent


def grid_height(n, cap=560):
    """行数に合わせた表の高さ（少ないときに空行を残さない）"""
    return min(cap, 38 + 35 * max(n, 1) + 2)
REGIONS = ["日本", "北米", "欧州", "アジア・他"]
ONPREM_WORDS = ("オンプレ", "ローカル", "国内サーバー")

# グラフの配色（dataviz参照パレットの青。代表/対応の2段は --ordinal 検証済み）
C_PRIMARY = "#256abf"       # 代表的な工程
C_SECONDARY = "#86b6ef"     # 対応している工程
SURFACE = "#fcfcfb"
SEQ_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

st.set_page_config(page_title=APP_NAME, page_icon=":material/travel_explore:",
                   layout="wide", initial_sidebar_state="expanded")


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
    title = dict(zip(C.cat_id, C.title))
    order = dict(zip(C.cat_id, C["sort"]))

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
    V["cats"] = V.vendor_id.map(all_c).apply(as_list)
    V["primary"] = V.vendor_id.map(pri_c).apply(as_list)
    V["代表工程"] = V["primary"].apply(lambda cs: " / ".join(title[c] for c in cs))
    V["対応工程"] = V.apply(
        lambda r: " / ".join(title[c] for c in r["cats"] if c not in r["primary"]), axis=1)
    V["工程数"] = V["cats"].apply(len)
    V["ブース"] = V.vendor_id.map(ex["booth"]).fillna("")
    V["展示"] = V.vendor_id.map(ex["exhibit_name"]).fillna("")
    V["展示内容"] = V.vendor_id.map(ex["exhibit_note"]).fillna("")
    V["フェア出展"] = V.vendor_id.isin(ex.index)
    V["MCP"] = V.is_mcp.astype(str) == "1"
    V["2026年更新"] = V.is_new_2026.astype(str) == "1"
    V["オンプレ"] = V.deployment.fillna("").apply(lambda d: any(w in d for w in ONPREM_WORDS))
    V["_first"] = V["cats"].apply(lambda cs: min((order[c] for c in cs), default=99))
    V["_hay"] = (V.name + " " + V.description + " " + V["展示"] + " " + V["展示内容"] + " "
                 + V.deployment.fillna("") + " " + V["ブース"] + " "
                 + V["cats"].apply(lambda cs: " ".join(title[c] for c in cs))).str.lower()
    return V.sort_values(["_first", "name"]).reset_index(drop=True), C, vc, title


frames, errs, warns = load_data()
if errs:
    st.error("データに不整合があるため表示を止めています。`data/*.csv` を修正してください。")
    for e in errs:
        st.write("・", e)
    st.stop()

V, C, VC, TITLE = build_view(frames)
CAT_IDS = C.cat_id.tolist()


# ---------------------------------------------------------------------------
# 絞り込み（サイドバーの条件はすべてのタブに効く）
# ---------------------------------------------------------------------------
DEFAULTS = {"q": "", "fair": False, "mcp": False, "new": False, "onprem": False,
            "regions": [], "cats": [], "scope": "対応している工程も含める"}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


def reset_filters():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


with st.sidebar:
    st.text_input("検索", key="q",
                  placeholder="社名・製品・特徴（例：オンプレミス、MCP、明細書）")
    st.markdown("**属性**")
    st.checkbox(f"知財・情報フェア2026に出展（{int(V['フェア出展'].sum())}）", key="fair")
    st.checkbox(f"MCP／AIエージェント連携（{int(V['MCP'].sum())}）", key="mcp")
    st.checkbox(f"2026年の新規・大型更新（{int(V['2026年更新'].sum())}）", key="new")
    st.checkbox(f"オンプレミス・ローカル実行（{int(V['オンプレ'].sum())}）", key="onprem")
    st.multiselect("地域", REGIONS, key="regions", placeholder="すべての地域")
    st.multiselect("業務工程", CAT_IDS, key="cats", placeholder="すべての工程",
                   format_func=lambda c: f"{c}  {TITLE[c]}")
    st.radio("工程の数え方", ["対応している工程も含める", "代表的な工程のみ"], key="scope",
             help="代表的な工程＝カオスマップ上の配置。対応している工程＝公式情報で提供を確認できたもの。")
    st.button("絞り込みを解除", on_click=reset_filters, width="stretch")

ss = st.session_state
use_primary = ss.scope == "代表的な工程のみ"
catcol = "primary" if use_primary else "cats"

mask = pd.Series(True, index=V.index)
if ss.fair:
    mask &= V["フェア出展"]
if ss.mcp:
    mask &= V["MCP"]
if ss.new:
    mask &= V["2026年更新"]
if ss.onprem:
    mask &= V["オンプレ"]
if ss.regions:
    mask &= V.region.isin(ss.regions)
if ss.cats:
    want = set(ss.cats)
    mask &= V[catcol].apply(lambda cs: bool(want & set(cs)))
for term in ss.q.lower().split():
    mask &= V["_hay"].str.contains(term, regex=False)
H = V[mask].reset_index(drop=True)


# ---------------------------------------------------------------------------
# 見出し
# ---------------------------------------------------------------------------
st.title(APP_NAME)
updated = frames["vendors"].updated_at.max()
st.caption(f"生成AI・AIを組み込んだ知財ベンダー {len(V)}社 ・ {len(C)}工程 ・ "
           f"知財・情報フェア2026出展 {int(V['フェア出展'].sum())}社 ・ 更新 {updated}")

active = []
if ss.q:
    active.append(f"「{ss.q}」")
active += [lab for key, lab in [("fair", "フェア出展"), ("mcp", "MCP対応"),
                                ("new", "2026年更新"), ("onprem", "オンプレ・ローカル")] if ss[key]]
active += ss.regions + [TITLE[c] for c in ss.cats]
st.markdown(f"#### 該当 {len(H)} / {len(V)} 社" +
            (f"　<span style='font-size:0.8em;color:#52514e'>条件：{'・'.join(active)}</span>"
             if active else ""), unsafe_allow_html=True)

tab_list, tab_map, tab_fair, tab_data = st.tabs(
    ["一覧", "工程マップ", "知財・情報フェア2026", "データ・掲載基準"])


# ---------------------------------------------------------------------------
# 一覧
# ---------------------------------------------------------------------------
with tab_list:
    if H.empty:
        st.info("該当するベンダーがありません。検索語を外すか、工程・地域の条件を広げてください。")
    else:
        grid = H[["name", "region", "代表工程", "対応工程", "deployment", "ブース",
                  "MCP", "2026年更新", "description", "url"]]
        ev = st.dataframe(
            grid, hide_index=True, width="stretch", height=grid_height(len(grid)),
            on_select="rerun", selection_mode="single-row", key="grid",
            column_config={
                "name": st.column_config.TextColumn("社名", width="medium", pinned=True),
                "region": st.column_config.TextColumn("地域", width="small"),
                "代表工程": st.column_config.TextColumn(width="medium"),
                "対応工程": st.column_config.TextColumn(width="medium"),
                "deployment": st.column_config.TextColumn("提供形態", width="small"),
                "ブース": st.column_config.TextColumn(width="small"),
                "MCP": st.column_config.CheckboxColumn(width="small"),
                "2026年更新": st.column_config.CheckboxColumn("2026", width="small"),
                "description": st.column_config.TextColumn("紹介", width="large"),
                "url": st.column_config.LinkColumn("公式サイト", display_text="開く", width="small"),
            })

        rows = ev.selection.rows if ev and ev.selection else []
        if not rows:
            st.caption("行を選ぶと、その社がどの工程に対応しているかと、その根拠を表示します。")
        else:
            r = H.iloc[rows[0]]
            st.divider()
            head = f"### {r['name']}"
            if r["url"]:
                head += f"　[公式サイト]({r['url']})"
            st.markdown(head)
            m1, m2, m3 = st.columns(3)
            m1.markdown(f"**地域**　{r['region']}（{r['country']}）")
            m2.markdown(f"**提供形態**　{r['deployment'] or '未確認'}")
            m3.markdown(f"**対応工程**　{r['工程数']}")
            st.write(r["description"])
            if r["フェア出展"]:
                booth = r["ブース"] or "番号未取得"
                st.markdown(f"**知財・情報フェア2026**　ブース `{booth}`　{r['展示']}")
                if r["展示内容"]:
                    st.caption(r["展示内容"])
            ev_rows = VC[VC.vendor_id == r["vendor_id"]].copy()
            ev_rows["工程"] = ev_rows.cat_id.map(lambda c: f"{c}  {TITLE[c]}")
            ev_rows["区分"] = ev_rows.role.map({"主": "代表", "副": "対応"})
            st.dataframe(ev_rows[["工程", "区分", "source", "checked_at"]], hide_index=True,
                         width="stretch",
                         column_config={"source": st.column_config.TextColumn("根拠", width="large"),
                                        "checked_at": st.column_config.TextColumn("確認日", width="small")})


# ---------------------------------------------------------------------------
# 工程マップ
# ---------------------------------------------------------------------------
def counts_by_category(frame):
    ids = set(frame.vendor_id)
    x = VC[VC.vendor_id.isin(ids)].copy()
    x["区分"] = x.role.map({"主": "代表的な工程", "副": "対応している工程"})
    t = x.groupby(["cat_id", "区分"]).size().rename("社数").reset_index()
    t["工程"] = t.cat_id.map(lambda c: f"{c} {TITLE[c]}")
    return t


with tab_map:
    if H.empty:
        st.info("該当するベンダーがないため、グラフを描けません。")
    else:
        st.markdown("##### 工程ごとの社数")
        st.caption("濃い部分は、その工程を代表的な機能としている社。薄い部分は、対応はしているが主力ではない社。")
        t = counts_by_category(H)
        order_labels = [f"{c} {TITLE[c]}" for c in CAT_IDS]
        totals = t.groupby("工程", as_index=False)["社数"].sum()
        base = alt.Chart(t).encode(y=alt.Y("工程:N", sort=order_labels, title=None,
                                          axis=alt.Axis(labelLimit=260, ticks=False, domain=False)))
        bars = base.mark_bar(stroke=SURFACE, strokeWidth=2).encode(
            x=alt.X("sum(社数):Q", title="社数", axis=alt.Axis(tickMinStep=1, grid=True)),
            color=alt.Color("区分:N", scale=alt.Scale(domain=["代表的な工程", "対応している工程"],
                                                      range=[C_PRIMARY, C_SECONDARY]),
                            legend=alt.Legend(orient="top", title=None)),
            order=alt.Order("区分:N", sort="ascending"),
            tooltip=["工程:N", "区分:N", "社数:Q"])
        labels = alt.Chart(totals).mark_text(align="left", dx=6, color="#52514e", fontSize=12).encode(
            y=alt.Y("工程:N", sort=order_labels), x="社数:Q", text="社数:Q")
        st.altair_chart((bars + labels).properties(height=34 * len(CAT_IDS)), use_container_width=True)
        with st.expander("表で見る"):
            pv = t.pivot_table(index="工程", columns="区分", values="社数", aggfunc="sum", fill_value=0)
            pv = pv.reindex([l for l in order_labels if l in pv.index])
            pv["合計"] = pv.sum(axis=1)
            st.dataframe(pv, width="stretch")

        st.markdown("##### 工程 × 地域")
        st.caption("マスの色が濃いほど社数が多い。空白のマスは0社。対応している工程も含めて数えている。")
        x = VC[VC.vendor_id.isin(H.vendor_id)].merge(H[["vendor_id", "region"]], on="vendor_id")
        hm = x.groupby(["cat_id", "region"]).size().rename("社数").reset_index()
        hm["工程"] = hm.cat_id.map(lambda c: f"{c} {TITLE[c]}")
        vmax = int(hm["社数"].max())
        base = alt.Chart(hm).encode(
            y=alt.Y("工程:N", sort=order_labels, title=None,
                    axis=alt.Axis(labelLimit=260, ticks=False, domain=False)),
            x=alt.X("region:N", sort=REGIONS, title=None,
                    axis=alt.Axis(orient="top", labelAngle=0, ticks=False, domain=False)))
        rect = base.mark_rect(stroke=SURFACE, strokeWidth=2, cornerRadius=3).encode(
            color=alt.Color("社数:Q", scale=alt.Scale(range=SEQ_RAMP, domain=[0, vmax]),
                            legend=alt.Legend(title="社数", orient="right", gradientLength=160)),
            tooltip=["工程:N", alt.Tooltip("region:N", title="地域"), "社数:Q"])
        text = base.mark_text(fontSize=12).encode(
            text="社数:Q",
            color=alt.condition(f"datum['社数'] >= {max(2, vmax * 0.55):.1f}",
                                alt.value("#ffffff"), alt.value("#17202c")))
        st.altair_chart((rect + text).properties(height=30 * len(CAT_IDS)), use_container_width=True)
        with st.expander("表で見る"):
            pv2 = hm.pivot_table(index="工程", columns="region", values="社数", fill_value=0)
            pv2 = pv2.reindex(index=[l for l in order_labels if l in pv2.index],
                              columns=[r for r in REGIONS if r in pv2.columns])
            st.dataframe(pv2.astype(int), width="stretch")


# ---------------------------------------------------------------------------
# 知財・情報フェア2026
# ---------------------------------------------------------------------------
with tab_fair:
    st.caption("2026 知財・情報フェア＆コンファレンス（2026年9月16〜18日・東京ビッグサイト東3ホール）の出展社のうち、"
               "AI・生成AIを組み込んだ製品を公表していた社。ブース番号順に並べている。サイドバーの条件も効く。")
    F = H[H["フェア出展"]].copy()
    if F.empty:
        st.info("条件に合う出展社がありません。")
    else:
        F["_b"] = F["ブース"].replace("", "ZZ")
        F = F.sort_values("_b")
        st.dataframe(
            F[["ブース", "name", "展示", "代表工程", "展示内容", "url"]], hide_index=True,
            width="stretch", height=grid_height(len(F)),
            column_config={
                "ブース": st.column_config.TextColumn(width="small"),
                "name": st.column_config.TextColumn("社名", width="medium"),
                "展示": st.column_config.TextColumn(width="medium"),
                "代表工程": st.column_config.TextColumn(width="medium"),
                "展示内容": st.column_config.TextColumn(width="large"),
                "url": st.column_config.LinkColumn("公式サイト", display_text="開く", width="small"),
            })
        st.caption(f"{len(F)}社。ブース番号が空欄の社は、出展は確認できたが番号を取得できなかったもの。")


# ---------------------------------------------------------------------------
# データ・掲載基準
# ---------------------------------------------------------------------------
def export_frame(frame):
    out = frame[["vendor_id", "name", "region", "country", "代表工程", "対応工程", "工程数",
                 "deployment", "MCP", "2026年更新", "フェア出展", "ブース", "展示",
                 "description", "url"]].copy()
    return out.rename(columns={"name": "社名", "region": "地域", "country": "国",
                               "deployment": "提供形態", "description": "紹介", "url": "公式サイト"})


with tab_data:
    st.markdown("##### データを取り出す")
    c1, c2, c3 = st.columns(3)
    c1.download_button(f"絞り込み結果をCSVで（{len(H)}社）",
                       export_frame(H).to_csv(index=False).encode("utf-8-sig"),
                       file_name="ipai_vendors_filtered.csv", mime="text/csv", width="stretch")
    xbuf = io.BytesIO()
    with pd.ExcelWriter(xbuf, engine="openpyxl") as w:
        export_frame(V).to_excel(w, sheet_name="vendors", index=False)
        frames["excluded"].to_excel(w, sheet_name="excluded", index=False)
    c2.download_button(f"全件をExcelで（{len(V)}社）", xbuf.getvalue(),
                       file_name="ipai_vendors.xlsx", width="stretch",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    js = {"updated": updated, "vendors": export_frame(V).to_dict(orient="records")}
    c3.download_button("全件をJSONで", json.dumps(js, ensure_ascii=False, indent=1).encode("utf-8"),
                       file_name="ipai_vendors.json", mime="application/json", width="stretch")
    st.caption(f"元データ（CSV・SQLite）と更新の履歴は [GitHub]({REPO_URL}) で公開している。"
               f"掲載漏れや誤りは [Issue で知らせてほしい]({REPO_URL}/issues/new)。")

    st.markdown("##### 掲載基準")
    st.write("AI・生成AIを組み込んだ製品またはサービスを、公開情報で確認できるベンダーに限る。"
             "工程は、カオスマップ上の配置にあたる「代表的な工程」と、公式情報で提供を確認できた"
             "「対応している工程」に分けて登録し、それぞれに根拠を記録している。")
    X = frames["excluded"]
    with st.expander(f"掲載基準から外した機関・企業（{len(X)}）"):
        st.caption("公的機関、業界団体、教育機関、AI活用を公表していない事業者など。"
                   "除外はAI搭載の有無という一点の判定で、事業の価値や実務上の重要性を評価したものではない。")
        st.dataframe(X[["name", "kind", "reason"]], hide_index=True, width="stretch",
                     column_config={"name": "名称", "kind": "区分",
                                    "reason": st.column_config.TextColumn("理由", width="large")})

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
           "機能の実効性は検証していない。紹介文の数値は各社の公表値。　整理：上村侑太郎（LeXi/Vent）")
