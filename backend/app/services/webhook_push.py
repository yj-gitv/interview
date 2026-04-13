import json

import httpx

from app.config import settings


async def push_to_dingtalk(
    candidate_codename: str,
    position_title: str,
    recommendation: str,
    summary_text: str,
) -> bool:
    if not settings.dingtalk_webhook_url:
        return False

    content = (
        f"**面试结果通知**\n\n"
        f"- 候选人：{candidate_codename}\n"
        f"- 岗位：{position_title}\n"
        f"- 推荐等级：{recommendation}\n"
        f"- 总结：{summary_text}\n"
    )

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"面试结果 - {candidate_codename}",
            "text": content,
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.dingtalk_webhook_url,
                json=payload,
                timeout=10.0,
            )
            return resp.status_code == 200
    except Exception:
        return False


async def push_to_feishu(
    candidate_codename: str,
    position_title: str,
    recommendation: str,
    summary_text: str,
) -> bool:
    if not settings.feishu_webhook_url:
        return False

    content = (
        f"**面试结果通知**\n\n"
        f"候选人：{candidate_codename}\n"
        f"岗位：{position_title}\n"
        f"推荐等级：{recommendation}\n"
        f"总结：{summary_text}"
    )

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"面试结果 - {candidate_codename}",
                },
                "template": "blue",
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": content,
                },
            ],
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.feishu_webhook_url,
                json=payload,
                timeout=10.0,
            )
            return resp.status_code == 200
    except Exception:
        return False


async def push_interview_result(
    candidate_codename: str,
    position_title: str,
    recommendation: str,
    summary_text: str,
) -> dict:
    results = {"dingtalk": False, "feishu": False}

    if settings.dingtalk_webhook_url:
        results["dingtalk"] = await push_to_dingtalk(
            candidate_codename, position_title, recommendation, summary_text
        )

    if settings.feishu_webhook_url:
        results["feishu"] = await push_to_feishu(
            candidate_codename, position_title, recommendation, summary_text
        )

    return results
