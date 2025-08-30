from uuid import uuid4

from nonebot import get_driver, get_plugin_config, on_command, on_message
from nonebot.adapters.telegram.event import PrivateMessageEvent, GroupMessageEvent
from nonebot.adapters.telegram.message import Message
from nonebot.adapters.telegram.bot import Bot
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.rule import to_me

from .config import Config
from .database import (
    AlipayUser,
    Device,
    TgUser,
    init_db,
    AsyncSessionLocal,
    AsyncGenerator,
)
from .msg import guide_msg

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nonebot.params import Depends


__author__ = "byseven"
__plugin_meta__ = PluginMetadata(
    name="sesame",
    description="获取芝麻粒-TK授权码",
    usage=("通过TG Bot获取芝麻粒-TK授权码"),
    type="application",
    config=Config,
)
c = get_driver().config
config = get_plugin_config(Config)

logger.info(f"{c.database_uri}")
logger.info(f"调试模式：{config.debug}")

# 🤖机器人响应指令
help_cmd = on_command("help", rule=to_me(), priority=5)
bu_cmd = on_command("sync", rule=to_me(), priority=5)
bd_cmd = on_command("bd", rule=to_me(), priority=5)
ba_cmd = on_command("ba", rule=to_me(), priority=5)
da_cmd = on_command("da", rule=to_me(), priority=5)
auto_leave = on_message(priority=10, block=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    await init_db()
    async with AsyncSessionLocal() as session:
        yield session


@auto_leave.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if isinstance(event, GroupMessageEvent):
        chat_id = event.chat.id
        chat_type = event.chat.type
        logger.debug(f"{chat_id} {chat_type}")
        if chat_type in ("group", "supergroup"):  # and chat_id not in ALLOWED_GROUPS:
            await bot.call_api("leaveChat", chat_id=chat_id)
            logger.success(f"退群成功 {event}")
            return


@help_cmd.handle()
async def _(event: PrivateMessageEvent):
    if isinstance(event, PrivateMessageEvent):
        await help_cmd.finish(guide_msg, parse_mode="MarkdownV2")


@bu_cmd.handle()
async def _(
    event: PrivateMessageEvent,
    db: AsyncSession = Depends(get_db_session),
):
    if not isinstance(event, PrivateMessageEvent):
        return

    tk = uuid4().hex
    tg_id = event.chat.id
    _username = event.chat.username or ""
    _first_name = event.chat.first_name or ""
    _last_name = event.chat.last_name or ""

    # 查询用户
    result = await db.execute(select(TgUser).where(TgUser.tg_id == tg_id))
    user = result.scalar_one_or_none()

    if user:
        updated_fields = {}
        if not user.token:
            user.token = tk
            updated_fields["token"] = tk
        if user.username != _username:
            user.username = _username
            updated_fields["username"] = _username
        if user.first_name != _first_name:
            user.first_name = _first_name
            updated_fields["first_name"] = _first_name
        if user.last_name != _last_name:
            user.last_name = _last_name
            updated_fields["last_name"] = _last_name

        if updated_fields:
            await db.commit()
            await bu_cmd.finish(f"生成授权成功 🔑 请妥善保管授权 {user.token}")
        else:
            await bu_cmd.finish("无需更新，信息未发生变化 ✅")
    else:
        user = TgUser(
            tg_id=tg_id,
            token=tk,
            username=_username,
            first_name=_first_name,
            last_name=_last_name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        await bu_cmd.finish(f"注册成功 🔑 请妥善保管授权 {user.token}")


# 绑定 Verify ID
@bd_cmd.handle()
async def _(
    event: PrivateMessageEvent,
    args: Message = CommandArg(),
    db: AsyncSession = Depends(get_db_session),
):
    if not isinstance(event, PrivateMessageEvent):
        return

    message_text = args.extract_plain_text().strip()
    if not message_text:
        await bd_cmd.finish("请提供 Verfiy ID。用法: /bd [verify_id]")

    target_msg = message_text
    if len(target_msg) != 32 or not target_msg.isalnum():
        await bd_cmd.finish(
            "❌ 格式错误：应为32位长度的 Verify ID，请在模块主页长按复制"
        )

    # 检查是否已有这个 device_id 被其他人绑定
    result = await db.execute(select(Device).where(Device.device_id == target_msg))
    existing = result.scalars().first()
    if existing and existing.tg_id != event.chat.id:
        await bd_cmd.finish("⚠️ 此 Verify ID 已被他人绑定，无法重复使用")

    # 当前用户是否已有记录
    result = await db.execute(select(Device).where(Device.tg_id == event.chat.id))
    device = result.scalars().first()

    if device:
        if device.device_id == target_msg:
            await bd_cmd.finish("✅ 你已绑定该 Verify ID，无需重复提交")
        else:
            device.device_id = target_msg
            await db.commit()
            await bd_cmd.finish(
                f"📱更新 Verify ID 成功：{target_msg[:4]}********{target_msg[-4:]}"
            )
    else:
        new_device = Device(device_id=target_msg, tg_id=event.chat.id)
        db.add(new_device)
        await db.commit()
        await bd_cmd.finish(
            f"📱Verify ID 绑定成功：{target_msg[:4]}********{target_msg[-4:]}"
        )


# 绑定 alipay userId
@ba_cmd.handle()
async def _(
    event: PrivateMessageEvent,
    args: Message = CommandArg(),
    db: AsyncSession = Depends(get_db_session),
):
    if isinstance(event, PrivateMessageEvent):
        message_text = args.extract_plain_text()
        if not message_text:
            await ba_cmd.finish("📔 请提供要绑定的 userId。用法: /ba [userId]")

        target_msg = message_text.strip()
        if len(target_msg) != 16 or not target_msg.isdigit():
            await ba_cmd.finish("请检查输入的格式是否正确：必须是16位数字ID")

        # 检查该 alipay_id 是否已经被绑定
        result = await db.execute(
            select(AlipayUser).where(AlipayUser.alipay_id == target_msg)
        )
        existing = result.scalars().first()

        if existing:
            if existing.tg_id == event.chat.id:
                await ba_cmd.finish("你已绑定该账号，请勿重复绑定")
            else:
                await ba_cmd.finish("该ID已经被其他用户绑定")

        # 检查该 Telegram 用户绑定了几个账号
        result = await db.execute(
            select(AlipayUser).where(AlipayUser.tg_id == event.chat.id)
        )
        count = len(result.scalars().all())
        if count >= 20:
            await ba_cmd.finish("别鸡巴绑了这么多个账号了💢")

        # 插入新记录
        alipay = AlipayUser(alipay_id=target_msg, tg_id=event.chat.id)
        db.add(alipay)
        await db.commit()
        await db.refresh(alipay)
        await ba_cmd.finish(f"账号绑定成功 {target_msg[:3]}********{target_msg[-3:]}")


# 删除绑定的 alipay userId
@da_cmd.handle()
async def _(
    event: PrivateMessageEvent,
    args: Message = CommandArg(),
    db: AsyncSession = Depends(get_db_session),
):
    if not isinstance(event, PrivateMessageEvent):
        return

    message_text = args.extract_plain_text().strip()
    if not message_text:
        await da_cmd.finish("请提供要删除的 userId ID。用法: /da [userId]")

    target_msg = message_text
    if len(target_msg) != 16 or not target_msg.isdigit():
        await da_cmd.finish("请检查输入的格式是否正确：必须是16位数字ID")

    result = await db.execute(
        select(AlipayUser).where(
            AlipayUser.tg_id == event.chat.id, AlipayUser.alipay_id == target_msg
        )
    )
    alipay_user = result.scalars().first()

    if not alipay_user:
        await da_cmd.finish(f"你并没有绑定: {target_msg}")

    await db.delete(alipay_user)
    await db.commit()
    await da_cmd.finish(f"成功解绑: {target_msg[:3]}********{target_msg[-3:]}")
