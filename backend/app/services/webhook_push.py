import httpx

from app.config import settings


async def push_to_dingtalk(
    candidate_codename: str,
    position_title: str,
    recommendation: str,
    summary_text: str,
    summary_url: str = "",
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
    if summary_url:
        content += f"\n[查看完整总结]({summary_url})\n"

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
    summary_url: str = "",
) -> bool:
    if not settings.feishu_webhook_url:
        return False

    rec_color = {"推荐": "green", "待定": "yellow", "不推荐": "red"}.get(
        recommendation, "blue"
    )

    elements: list[dict] = [
        {
            "tag": "div",
            "fields": [
                {"is_short": True, "text": {"tag": "lark_md", "content": f"**候选人**\n{candidate_codename}"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": f"**岗位**\n{position_title}"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": f"**推荐等级**\n{recommendation}"}},
            ],
        },
        {"tag": "hr"},
        {
            "tag": "markdown",
            "content": summary_text,
        },
    ]

    if summary_url:
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "查看完整总结"},
                    "type": "primary",
                    "url": summary_url,
                },
            ],
        })

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"面试结果 - {candidate_codename}",
                },
                "template": rec_color,
            },
            "elements": elements,
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
    summary_url: str = "",
) -> dict:
    results = {"dingtalk": False, "feishu": False}

    if settings.dingtalk_webhook_url:
        results["dingtalk"] = await push_to_dingtalk(
            candidate_codename, position_title, recommendation, summary_text,
            summary_url=summary_url,
        )

    if settings.feishu_webhook_url:
        results["feishu"] = await push_to_feishu(
            candidate_codename, position_title, recommendation, summary_text,
            summary_url=summary_url,
        )

    return results
