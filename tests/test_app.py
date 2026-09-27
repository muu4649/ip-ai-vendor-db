# -*- coding: utf-8 -*-
"""アプリがエラーなく動くことを確かめる。

手元の環境と Streamlit Community Cloud では Python や依存パッケージの版が違うので、
CI（.github/workflows/test.yml）から公開環境と同じ Python で実行する。
"""
import pathlib

import pytest
from streamlit.testing.v1 import AppTest

APP = str(pathlib.Path(__file__).resolve().parents[1] / "streamlit_app.py")


def run_app():
    return AppTest.from_file(APP, default_timeout=120).run()


def assert_clean(at):
    assert not at.exception, [e.value for e in at.exception]
    # グラフが描けなかったときは警告を出して続行する作りなので、警告も失敗として扱う
    assert not at.warning, [w.value for w in at.warning]


def test_starts_without_error():
    """起動直後（絞り込みなし）で、例外もグラフの警告も出ない"""
    assert_clean(run_app())


@pytest.mark.parametrize("key", ["fair", "mcp", "new", "onprem"])
def test_attribute_filters(key):
    """属性のチェックボックスで絞り込んでも壊れない"""
    at = run_app()
    at.checkbox(key=key).check().run()
    assert_clean(at)


def test_category_filter_primary_only():
    """工程で絞り、代表的な工程のみに切り替えても壊れない"""
    at = run_app()
    at.multiselect(key="cats").set_value(["04"]).run()
    at.radio(key="scope").set_value("代表的な工程のみ").run()
    assert_clean(at)


def test_region_filter_heatmap_caption():
    """地域で絞ったとき、工程×地域の説明文が、残った列だけを並べる"""
    at = run_app()
    at.multiselect(key="regions").set_value(["欧州", "北米"]).run()
    assert_clean(at)
    assert any(c.value.startswith("列は左から 北米／欧州。") for c in at.caption), \
        [c.value for c in at.caption]


def test_no_hits():
    """該当なしのときも例外にならない"""
    at = run_app()
    at.text_input(key="q").input("存在しない語句xyz").run()
    assert not at.exception, [e.value for e in at.exception]
