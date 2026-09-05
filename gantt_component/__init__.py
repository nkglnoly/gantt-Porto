import os
import streamlit.components.v1 as components

_COMPONENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

_gantt_component = components.declare_component(
    "gantt_component",
    path=_COMPONENT_DIR,
)


def gantt_chart(groups, items, view_start, view_end, height=420, key=None):
    """
    設備別ガントチャートを描画し、ドラッグ操作の結果を辞書で返すカスタムコンポーネント。

    Parameters
    ----------
    groups : list[dict]  vis-timeline の group 定義（id, content）
    items : list[dict]   vis-timeline の item 定義（id, group, content, start, end, priority, status, comment, memo）
    view_start : str     表示開始日時（ISO文字列）
    view_end : str       表示終了日時（ISO文字列）
    height : int         ガント表示エリアの高さ(px)
    key : str            Streamlitのwidgetキー

    Returns
    -------
    dict | None
        ドラッグ操作があった場合: {"action": "move", "task_id": int, "new_start": "ISO文字列"}
        操作がなければ None
    """
    return _gantt_component(
        groups=groups,
        items=items,
        view_start=view_start,
        view_end=view_end,
        height=height,
        key=key,
        default=None,
    )
