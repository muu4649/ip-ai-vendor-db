# -*- coding: utf-8 -*-
"""アプリがエラーなく動き、探す・比べるの流れが壊れていないことを確かめる。

手元の環境と Streamlit Community Cloud では Python や依存パッケージの版が違うので、
CI（.github/workflows/test.yml）から公開環境と同じ Python でも実行する。
"""
import csv
import pathlib
import re

import pytest
from streamlit.testing.v1 import AppTest

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = str(ROOT / "streamlit_app.py")
ATTRS = ["ja", "onprem", "no_training", "trial", "pricing"]
TABS = ["探す", "比較する", "市場の全体像", "知財・情報フェア2026", "掲載基準・データ"]


def run_app():
    return AppTest.from_file(APP, default_timeout=120).run()


def assert_clean(at):
    assert not at.exception, [e.value for e in at.exception]
    # グラフが描けなかったときは警告を出して続行する作りなので、警告も失敗として扱う
    assert not at.warning, [w.value for w in at.warning]


def result_count(at):
    """見出しの「N社 ／ 全M社」から N を取り出す"""
    for m in at.markdown:
        hit = re.search(r'class="count">(\d+)<small>', m.value)
        if hit:
            return int(hit.group(1))
    raise AssertionError("件数の表示が見つからない")


def open_tab(at, label):
    at.session_state["tab"] = label
    return at.run()


def card_keys(at):
    return [c.key for c in at.checkbox if c.key and c.key.startswith("cmp_")]


def expected_yes(attr):
    rows = csv.DictReader(open(ROOT / "data/vendor_attributes.csv", encoding="utf-8-sig"))
    return sum(1 for r in rows if r["attr_id"] == attr and r["value"] == "あり")


def test_starts_without_error():
    """起動直後は業務の入口とカードを出し、一覧を表（データフレーム）では出さない"""
    at = run_app()
    assert_clean(at)
    assert [b for b in at.button if b.key == "tile_03"], "業務の入口がない"
    assert card_keys(at), "カードがない"
    assert not at.dataframe, "一覧に表が残っている"


def test_task_tile_selects_task():
    """入口の業務ボタンで、主力／対応に分けたカード表示になる"""
    at = run_app()
    at.button(key="tile_03").click().run()
    assert_clean(at)
    assert at.session_state["ph_0"] == ["03"]
    heads = " ".join(m.value for m in at.markdown)
    assert "主力として提供" in heads and "機能の一部として対応" in heads


def test_primary_only_hides_secondary_section():
    at = run_app()
    at.button(key="tile_03").click().run()
    at.toggle(key="primary_only").set_value(True).run()
    assert_clean(at)
    heads = " ".join(m.value for m in at.markdown)
    assert "主力として提供" in heads and "機能の一部として対応" not in heads


@pytest.mark.parametrize("attr", ATTRS)
def test_attribute_filter_counts(attr):
    """導入条件で絞った社数が、data/vendor_attributes.csv の「あり」の件数と一致する"""
    at = run_app()
    at.checkbox(key=f"a_{attr}").check().run()
    assert_clean(at)
    assert result_count(at) == expected_yes(attr)


def test_origin_filter_and_heatmap_caption():
    """海外に絞ると、工程×地域の説明文が残った列だけを並べる"""
    at = run_app()
    at.segmented_control(key="origin").set_value("海外").run()
    open_tab(at, "市場の全体像")
    assert_clean(at)
    assert any(c.value.startswith("列は左から 北米／欧州／アジア・他。") for c in at.caption), \
        [c.value for c in at.caption]


def test_compare_flow():
    """カードから比較に入れ、比較ボード・違いのみ表示・候補の追加・解除まで動く"""
    at = run_app()
    at.button(key="tile_03").click().run()
    keys = card_keys(at)[:3]
    for k in keys:
        at.checkbox(key=k).check().run()
    assert at.session_state["shortlist"] == [k.removeprefix("cmp_") for k in keys]

    open_tab(at, "比較する")
    assert_clean(at)
    assert any('class="cmp-wrap"' in m.value for m in at.markdown)
    sug = [b for b in at.button if b.key and b.key.startswith("sug_")]
    assert sug, "同じ業務の他社の候補が出ない"
    sug[0].click().run()
    assert len(at.session_state["shortlist"]) == 4

    # AppTest では操作のたびにタブが先頭に戻るので、状態を直接入れてから比較タブを開き直す
    at.session_state["cmp_diff"] = True
    open_tab(at, "比較する")
    assert_clean(at)
    assert any('class="cmp-wrap"' in m.value for m in at.markdown)
    clear = [b for b in at.button if b.label == "比較をすべて外す"]
    assert clear
    clear[0].click().run()
    assert at.session_state["shortlist"] == []


def test_compare_limit():
    """比較は5社まで"""
    at = run_app()
    for k in card_keys(at)[:6]:
        at.checkbox(key=k).check().run()
    assert len(at.session_state["shortlist"]) == 5
    assert_clean(at)


@pytest.mark.parametrize("tab", TABS)
def test_each_tab_renders(tab):
    at = run_app()
    open_tab(at, tab)
    assert_clean(at)


def test_no_hits():
    """該当なしのときも例外にならない"""
    at = run_app()
    at.text_input(key="q").input("存在しない語句xyz").run()
    assert not at.exception, [e.value for e in at.exception]
    assert result_count(at) == 0
