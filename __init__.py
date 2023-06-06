from nonebot import on_command, get_driver
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import MessageEvent

from .config import Config
from .bupt_rest_classroom import (get_now_free_classrooms as free_classrooms,
                                  get_all_day_free_classrooms as all_day_classrooms,
                                  beautifier)


config = Config.parse_obj(get_driver().config)

get_now_free_classrooms = on_command('空闲教室', rule=to_me(), priority=1)
get_all_day_free_classrooms = on_command('全天教室', rule=to_me(), priority=1, aliases={"全天空闲教室"})


@get_now_free_classrooms.handle()
async def _(_: MessageEvent):
    if not (config.bupt_userno and config.bupt_pwd):
        await get_now_free_classrooms.finish("没有设置账号密码呃呃")
    try:
        rooms = await free_classrooms(config.bupt_userno, config.bupt_pwd)
    except ConnectionError as e:
        await get_now_free_classrooms.finish(f"出错了呃呃\n{e}")
    await get_now_free_classrooms.finish("当前空闲教室有:\n" + beautifier(rooms))


@get_all_day_free_classrooms.handle()
async def _(_: MessageEvent):
    if not (config.bupt_userno and config.bupt_pwd):
        await get_now_free_classrooms.finish("没有设置账号密码呃呃")
    try:
        rooms = await all_day_classrooms(config.bupt_userno, config.bupt_pwd)
    except ConnectionError as e:
        await get_now_free_classrooms.finish(f"出错了呃呃\n{e}")
    await get_now_free_classrooms.finish("全天空闲教室有:\n" + beautifier(rooms))
