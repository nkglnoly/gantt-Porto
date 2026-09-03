import streamlit as st
import streamlit.components.v1 as components
import json
from datetime import datetime, timedelta

st.set_page_config(page_title="ガントチャート プロトタイプ", layout="wide")
st.title("🏭 設備別ガントチャート プロトタイプ")
st.caption("タスク登録フォーム＋完了実績処理版（後続タスク自動追従はまだ未実装）")


def ceil_to_hour(dt: datetime) -> datetime:
    """1時間単位で切り上げ（例：16:36→17:00、16:00→16:00）"""
    if dt.minute == 0 and dt.second == 0 and dt.microsecond == 0:
        return dt.replace(minute=0, second=0, microsecond=0)
    return (dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))

# =========================================================
# ---- マスタデータ：設備一覧 ----
# =========================================================
EQUIPMENTS = [
    {"id": "EQ01", "content": "設備A（プレス機）"},
    {"id": "EQ02", "content": "設備B（溶接機）"},
    {"id": "EQ03", "content": "設備C（検査機）"},
]

# ---- マスタデータ：作業マスタ（作業名 → 標準所要時間[分]） ----
if "work_master" not in st.session_state:
    st.session_state.work_master = [
        {"work_name": "プレス加工", "duration_min": 180},
        {"work_name": "バリ取り", "duration_min": 120},
        {"work_name": "溶接", "duration_min": 300},
        {"work_name": "外観検査", "duration_min": 90},
        {"work_name": "梱包", "duration_min": 60},
    ]

# =========================================================
# ---- タスクデータ（session_stateで管理） ----
# =========================================================
base = datetime(2026, 9, 3, 8, 0)

if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {
            "id": 1, "group": "EQ01",
            "lot_no": "L001", "design_no": "D101", "work_name": "プレス加工",
            "start": base, "end": base + timedelta(hours=3),
            "priority": "高", "memo": "",
            "status": "予定", "actual_start": None, "actual_end": None, "result_comment": "",
        },
        {
            "id": 2, "group": "EQ01",
            "lot_no": "L002", "design_no": "D102", "work_name": "バリ取り",
            "start": base + timedelta(hours=3), "end": base + timedelta(hours=5),
            "priority": "中", "memo": "",
            "status": "予定", "actual_start": None, "actual_end": None, "result_comment": "",
        },
        {
            "id": 3, "group": "EQ02",
            "lot_no": "L003", "design_no": "D103", "work_name": "溶接",
            "start": base + timedelta(hours=1), "end": base + timedelta(hours=6),
            "priority": "高", "memo": "",
            "status": "予定", "actual_start": None, "actual_end": None, "result_comment": "",
        },
        {
            "id": 4, "group": "EQ03",
            "lot_no": "L004", "design_no": "D104", "work_name": "外観検査",
            "start": base + timedelta(hours=2), "end": base + timedelta(hours=4),
            "priority": "低", "memo": "",
            "status": "予定", "actual_start": None, "actual_end": None, "result_comment": "",
        },
    ]

if "next_task_id" not in st.session_state:
    st.session_state.next_task_id = max(t["id"] for t in st.session_state.tasks) + 1


def get_work_duration(work_name: str) -> int:
    """作業マスタから所要時間[分]を取得"""
    for w in st.session_state.work_master:
        if w["work_name"] == work_name:
            return w["duration_min"]
    return 60  # フォールバック


# =========================================================
# ---- サイドバー：タスク登録フォーム ----
# =========================================================
with st.sidebar:
    st.header("📝 タスク新規登録")

    eq_labels = {e["content"]: e["id"] for e in EQUIPMENTS}
    eq_choice = st.selectbox("設備", list(eq_labels.keys()), key="eq_choice_select")

    work_names = [w["work_name"] for w in st.session_state.work_master]
    if not work_names:
        st.warning("作業マスタが空です。先に作業マスタを登録してください。")
        work_choice = None
        duration_min = 0
    else:
        work_choice = st.selectbox("作業（マスタ選択）", work_names, key="work_choice_select")
        duration_min = get_work_duration(work_choice)
        st.caption(f"⏱ マスタ登録の所要時間：{duration_min}分（{duration_min/60:.1f}時間）")

    with st.form("task_register_form", clear_on_submit=True):
        lot_no = st.text_input("ロットNO", placeholder="例：L005")
        design_no = st.text_input("設計NO", placeholder="例：D105")
        memo = st.text_area("メモ", placeholder="任意")
        priority = st.selectbox("優先度", ["高", "中", "低"], index=1)

        col_d, col_t = st.columns(2)
        with col_d:
            start_date = st.date_input("開始日", value=base.date())
        with col_t:
            start_time = st.time_input("開始時刻", value=base.time())

        submitted = st.form_submit_button("✅ 登録する", use_container_width=True)

        if submitted:
            if not work_choice:
                st.error("作業マスタが未登録のため登録できません。")
            elif not lot_no or not design_no:
                st.error("ロットNOと設計NOは必須です。")
            else:
                start_dt = datetime.combine(start_date, start_time)
                end_dt = start_dt + timedelta(minutes=duration_min)

                new_task = {
                    "id": st.session_state.next_task_id,
                    "group": eq_labels[eq_choice],
                    "lot_no": lot_no,
                    "design_no": design_no,
                    "work_name": work_choice,
                    "start": start_dt,
                    "end": end_dt,
                    "priority": priority,
                    "memo": memo,
                    "status": "予定",
                    "actual_start": None,
                    "actual_end": None,
                    "result_comment": "",
                }
                st.session_state.tasks.append(new_task)
                st.session_state.next_task_id += 1
                st.success(f"登録しました！（{eq_choice} / {work_choice} / {start_dt.strftime('%m/%d %H:%M')}〜{end_dt.strftime('%H:%M')}）")

    st.divider()
    st.subheader("⚙️ 作業マスタ管理")
    with st.expander("作業マスタを編集", expanded=False):
        for i, w in enumerate(st.session_state.work_master):
            c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
            with c1:
                st.text(w["work_name"])
            with c2:
                new_dur = st.number_input(
                    "所要時間(分)", value=w["duration_min"], key=f"dur_{i}",
                    min_value=1, step=10, label_visibility="collapsed"
                )
                st.session_state.work_master[i]["duration_min"] = new_dur
            with c3:
                st.caption(f"{new_dur/60:.1f}h")
            with c4:
                if st.button("🗑", key=f"del_work_{w['work_name']}", use_container_width=True):
                    st.session_state.work_master = [
                        x for x in st.session_state.work_master if x["work_name"] != w["work_name"]
                    ]
                    st.success(f"「{w['work_name']}」を削除しました")
                    st.rerun()

        st.markdown("---")
        new_work_name = st.text_input("新規作業名", key="new_work_name")
        new_work_dur = st.number_input("新規所要時間(分)", min_value=1, value=60, step=10, key="new_work_dur")
        if st.button("➕ マスタに追加", use_container_width=True):
            if new_work_name:
                if any(w["work_name"] == new_work_name for w in st.session_state.work_master):
                    st.error(f"「{new_work_name}」は既に登録されています")
                else:
                    st.session_state.work_master.append(
                        {"work_name": new_work_name, "duration_min": new_work_dur}
                    )
                    st.success(f"「{new_work_name}」を追加しました")
                    st.rerun()
            else:
                st.error("作業名を入力してください")

# =========================================================
# ---- メイン：ガントチャート表示 ----
# =========================================================
col1, col2 = st.columns([1, 3])
with col1:
    st.subheader("表示月")
    st.selectbox("対象月", ["2026年9月"], index=0, disabled=True,
                 help="MVPではダミー固定。実装時は月切替で範囲取得する想定")
    st.info("優先度カラー\n\n🔴 高　🟡 中　🟢 低\n\n⚠️＝実績コメントあり　📝＝メモあり（バーを長押し/タップで内容確認）")
    st.metric("登録タスク数", len(st.session_state.tasks))

with col2:
    st.subheader("設備別タイムライン（ドラッグで開始時刻を移動できます）")

groups_json = json.dumps(EQUIPMENTS, ensure_ascii=False)

items_for_js = [
    {
        "id": t["id"],
        "group": t["group"],
        "content": (
            f"ロットNO:{t['lot_no']}<br>設計NO:{t['design_no']}<br>作業:{t['work_name']}"
            + ("<br>✅完了" if t["status"] == "完了" else "")
            + (" ⚠️" if t.get("result_comment") else "")
            + (" 📝" if t.get("memo") else "")
        ),
        # 完了済みは実績期間、未完了は予定期間をバーとして表示
        "start": (t["actual_start"] or t["start"]).isoformat(),
        "end": (t["actual_end"] or t["end"]).isoformat(),
        "priority": t["priority"],
        "status": t["status"],
        "comment": t.get("result_comment", ""),
        "memo": t.get("memo", ""),
    }
    for t in st.session_state.tasks
]
items_json = json.dumps(items_for_js, ensure_ascii=False)

html_code = f"""
<div id="visualization" style="width:100%; height:420px;"></div>
<div id="moved-info" style="font-family:sans-serif; font-size:13px; margin-top:8px; color:#333;"></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/vis-timeline/7.7.3/vis-timeline-graph2d.min.js"></script>
<link href="https://cdnjs.cloudflare.com/ajax/libs/vis-timeline/7.7.3/vis-timeline-graph2d.min.css" rel="stylesheet" type="text/css" />

<script>
  const rawGroups = {groups_json};
  const rawItems = {items_json};

  const priorityColor = {{
    "高": "#ffcdd2",
    "中": "#fff9c4",
    "低": "#c8e6c9"
  }};

  const groups = new vis.DataSet(rawGroups);

  const items = new vis.DataSet(rawItems.map(t => {{
    const tooltipParts = [];
    if (t.memo) tooltipParts.push("📝 メモ: " + t.memo);
    if (t.comment) tooltipParts.push("⚠️ 実績コメント: " + t.comment);
    return {{
      id: t.id,
      group: t.group,
      content: t.content,
      start: t.start,
      end: t.end,
      title: tooltipParts.length ? tooltipParts.join("\\n") : null,
      style: "background-color:" + priorityColor[t.priority] + "; border-color:#888;" +
             (t.status === "完了" ? " opacity:0.55; border-style:dashed;" : "") +
             (t.comment ? " box-shadow: 0 0 0 2px #ff9800 inset;" : "")
    }};
  }}));

  const container = document.getElementById('visualization');
  const options = {{
    editable: {{
      updateTime: true,
      updateGroup: false,
      add: false,
      remove: false
    }},
    orientation: 'top',
    stack: false,
    zoomMin: 1000 * 60 * 60 * 2,
    zoomMax: 1000 * 60 * 60 * 24 * 31,
    start: "{base.replace(hour=0).isoformat()}",
    end: "{(base + timedelta(days=1)).replace(hour=0).isoformat()}",
    timeAxis: {{scale: 'hour', step: 1}},
    format: {{
      minorLabels: {{
        hour: 'HH:mm'
      }}
    }},
    onMove: function(item, callback) {{
      document.getElementById('moved-info').innerText =
        "タスクID " + item.id + " を移動: 開始=" + item.start.toLocaleString() + " 終了=" + item.end.toLocaleString() +
        "（※このプロトタイプでは後続タスクへの自動追従・保存はまだ未実装です／画面リロードで元に戻ります）";
      callback(item);
    }}
  }};

  const timeline = new vis.Timeline(container, items, groups, options);
</script>
"""

components.html(html_code, height=480, scrolling=False)

# =========================================================
# ---- タスク明細＋完了処理＋実績コメント＋削除機能 ----
# =========================================================
st.divider()
st.subheader("タスク明細（現在の登録内容）")
st.caption("完了ボタン：押した瞬間(now)を1時間単位で切り上げて実績終了日時を確定します。実績コメントは明細から後追いで入力・編集できます。")

for t in st.session_state.tasks:
    eq_name = next(e["content"] for e in EQUIPMENTS if e["id"] == t["group"])

    with st.container(border=True):
        c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 1, 1, 1.5, 1, 2.2, 1])
        c1.write(eq_name)
        c2.write(t["lot_no"])
        c3.write(t["design_no"])
        c4.write(t["work_name"])
        c5.write(t["priority"])

        if t["status"] == "完了":
            c6.write(
                f"予定: {t['start'].strftime('%m/%d %H:%M')}〜{t['end'].strftime('%H:%M')}\n\n"
                f"実績: {t['actual_start'].strftime('%m/%d %H:%M')}〜{t['actual_end'].strftime('%H:%M')} ✅"
            )
        else:
            c6.write(f"予定: {t['start'].strftime('%m/%d %H:%M')} 〜 {t['end'].strftime('%H:%M')}")

        with c7:
            if t["status"] != "完了":
                if st.button("✅ 完了", key=f"complete_{t['id']}", use_container_width=True):
                    now = datetime.now()
                    actual_end = ceil_to_hour(now)
                    t["status"] = "完了"
                    t["actual_start"] = t["start"]  # 開始確定時刻（今回は予定開始をそのまま使用）
                    t["actual_end"] = actual_end
                    st.success(f"完了しました！（実績終了：{actual_end.strftime('%m/%d %H:%M')}）")
                    st.rerun()
            if st.button("🗑", key=f"del_{t['id']}", use_container_width=True):
                st.session_state.tasks = [x for x in st.session_state.tasks if x["id"] != t["id"]]
                st.rerun()

        # ---- 実績コメント（後から追記・編集可能／タスクにつき1件・上書き） ----
        comment_val = st.text_input(
            "実績コメント（トラブル内容など・後から追記可）",
            value=t.get("result_comment", ""),
            key=f"comment_input_{t['id']}",
            placeholder="例：材料不良のため再加工が発生",
        )
        if comment_val != t.get("result_comment", ""):
            t["result_comment"] = comment_val

st.caption("次ステップ候補：①ドラッグ後の後続タスク自動追従ロジック ②完了による後続タスクの押し/前倒し反映 ③CSVエクスポート")
