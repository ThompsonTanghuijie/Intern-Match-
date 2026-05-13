import os
from typing import Any

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def api_get(path: str, **params: Any) -> Any:
    response = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def api_post(path: str, payload: dict[str, Any], **params: Any) -> Any:
    response = requests.post(f"{API_BASE_URL}{path}", params=params, json=payload, timeout=180)
    response.raise_for_status()
    return response.json()


def api_delete(path: str) -> Any:
    response = requests.delete(f"{API_BASE_URL}{path}", timeout=30)
    response.raise_for_status()
    return response.json()


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def tracking_payload(status: str, notes: str = "", favorite: bool = True) -> dict[str, Any]:
    return {
        "profile_name": "default",
        "is_favorite": favorite,
        "application_status": status,
        "notes": notes or None,
    }


st.set_page_config(page_title="Intern Match", layout="wide")
st.title("实习岗位爬取与匹配系统")

with st.sidebar:
    st.subheader("用户画像")
    skills = st.text_area("技能", "Python, SQL, FastAPI, PostgreSQL, Docker")
    locations = st.text_input("目标地点", "Remote, New York, San Francisco")
    directions = st.text_input("岗位方向", "backend, data engineering, internship")
    remote_preference = st.selectbox("远程偏好", ["prefer_remote", "remote", "hybrid", "onsite", ""])
    blacklist = st.text_input("关键词黑名单", "unpaid")
    min_score = st.slider("最低匹配分", min_value=0.0, max_value=1.0, value=0.35, step=0.05)
    limit = st.slider("推荐数量", min_value=5, max_value=100, value=30, step=5)
    save_profile = st.button("保存用户画像")
    run_match = st.button("生成推荐", type="primary")
    run_crawl = st.button("强制爬取岗位")

profile_payload = {
    "name": "default",
    "skills": split_csv(skills),
    "target_locations": split_csv(locations),
    "target_directions": split_csv(directions),
    "remote_preference": remote_preference or None,
    "blacklist_keywords": split_csv(blacklist),
}

if save_profile:
    try:
        saved = api_post("/profile", profile_payload)
        st.success(f"已保存画像：{saved['name']}")
    except requests.RequestException as exc:
        st.error(f"保存失败：{exc}")

if run_crawl:
    with st.spinner("正在抓取公开岗位源..."):
        try:
            runs = api_post("/crawl/run", {}, force=True)
            st.success("爬取完成")
            st.dataframe(runs, use_container_width=True)
        except requests.RequestException as exc:
            st.error(f"爬取失败：{exc}")

tab_recommend, tab_jobs, tab_tracking, tab_trends, tab_sources = st.tabs(
    ["推荐岗位", "岗位库", "我的跟踪", "趋势统计", "数据源"]
)

with tab_recommend:
    if run_match:
        match_payload = {**profile_payload, "min_score": min_score, "limit": limit}
        try:
            data = api_post("/match", match_payload)
            rows = [
                {
                    "score": item["score"],
                    "company": item["job"]["company"],
                    "title": item["job"]["title"],
                    "location": item["job"]["location"],
                    "job_type": item["job"]["job_type"],
                    "reasons": "；".join(item["reasons"]),
                    "apply_url": item["job"]["apply_url"],
                    "job_id": item["job"]["id"],
                }
                for item in data["items"]
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        except requests.RequestException as exc:
            st.error(f"匹配失败：{exc}")
    else:
        st.info("在左侧填写画像后点击“生成推荐”。")

    with st.form("track_from_recommend"):
        st.subheader("保存推荐岗位")
        job_id = st.number_input("岗位 ID", min_value=1, step=1)
        status = st.selectbox("状态", ["saved", "interested", "applied", "interview", "offer", "rejected", "archived"])
        notes = st.text_input("备注")
        submitted = st.form_submit_button("保存到我的跟踪")
        if submitted:
            try:
                api_post(f"/jobs/{job_id}/tracking", tracking_payload(status, notes))
                st.success("已保存")
            except requests.RequestException as exc:
                st.error(f"保存失败：{exc}")

with tab_jobs:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        q = st.text_input("搜索公司 / 岗位 / 描述")
    with col_b:
        job_location = st.text_input("地点筛选")
    with col_c:
        job_type = st.selectbox("岗位类型", ["", "internship", "new_grad", "coop", "unknown"])
    try:
        jobs = api_get(
            "/jobs",
            limit=100,
            q=q or None,
            location=job_location or None,
            job_type=job_type or None,
        )
        st.caption(f"共 {jobs['total']} 条")
        st.dataframe(jobs["items"], use_container_width=True, hide_index=True)
    except requests.RequestException as exc:
        st.error(f"读取岗位失败：{exc}")

with tab_tracking:
    st.subheader("收藏与投递状态")
    filter_status = st.selectbox("筛选状态", ["", "saved", "interested", "applied", "interview", "offer", "rejected", "archived"])
    favorites_only = st.checkbox("只看收藏", value=False)
    try:
        tracked = api_get(
            "/tracking",
            profile_name="default",
            status=filter_status or None,
            favorites_only=favorites_only,
        )
        rows = [
            {
                "tracking_id": item["id"],
                "status": item["application_status"],
                "favorite": item["is_favorite"],
                "company": item["job"]["company"],
                "title": item["job"]["title"],
                "location": item["job"]["location"],
                "notes": item["notes"],
                "apply_url": item["job"]["apply_url"],
                "job_id": item["job_id"],
            }
            for item in tracked
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
    except requests.RequestException as exc:
        st.error(f"读取跟踪列表失败：{exc}")

    with st.form("update_tracking"):
        st.subheader("更新或移除跟踪")
        edit_job_id = st.number_input("要更新的岗位 ID", min_value=1, step=1, key="edit_job_id")
        edit_status = st.selectbox(
            "新状态", ["saved", "interested", "applied", "interview", "offer", "rejected", "archived"], key="edit_status"
        )
        edit_favorite = st.checkbox("收藏", value=True)
        edit_notes = st.text_input("新备注")
        save_edit = st.form_submit_button("更新状态")
        if save_edit:
            try:
                api_post(f"/jobs/{edit_job_id}/tracking", tracking_payload(edit_status, edit_notes, edit_favorite))
                st.success("已更新")
            except requests.RequestException as exc:
                st.error(f"更新失败：{exc}")

    delete_id = st.number_input("要删除的 tracking ID", min_value=0, step=1)
    if st.button("删除跟踪记录") and delete_id:
        try:
            api_delete(f"/tracking/{delete_id}")
            st.success("已删除")
        except requests.RequestException as exc:
            st.error(f"删除失败：{exc}")

with tab_trends:
    st.subheader("岗位趋势统计")
    try:
        trends = api_get("/analytics/trends", limit=12)
        metric_a, metric_b = st.columns(2)
        metric_a.metric("总岗位数", trends["total_jobs"])
        metric_b.metric("活跃岗位数", trends["active_jobs"])

        chart_cols = st.columns(2)
        with chart_cols[0]:
            st.caption("岗位类型分布")
            st.bar_chart(pd.DataFrame(trends["by_job_type"]).set_index("label"))
            st.caption("热门技能")
            st.bar_chart(pd.DataFrame(trends["top_skills"]).set_index("label"))
        with chart_cols[1]:
            st.caption("热门地点")
            st.bar_chart(pd.DataFrame(trends["top_locations"]).set_index("label"))
            st.caption("我的投递状态")
            status_df = pd.DataFrame(trends["application_status"])
            if not status_df.empty:
                st.bar_chart(status_df.set_index("label"))
            else:
                st.info("还没有投递跟踪数据。")

        st.caption("按首次发现日期")
        day_df = pd.DataFrame(trends["by_day_seen"])
        if not day_df.empty:
            st.line_chart(day_df.set_index("label"))
    except requests.RequestException as exc:
        st.error(f"读取趋势失败：{exc}")

with tab_sources:
    try:
        sources = api_get("/sources")
        st.dataframe(sources, use_container_width=True, hide_index=True)
    except requests.RequestException as exc:
        st.error(f"读取数据源失败：{exc}")
