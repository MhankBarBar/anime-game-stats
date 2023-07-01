import argparse
import asyncio
import json
import logging
import os
import pathlib
import typing
from datetime import datetime

import genshin
import jinja2
import pytz
from dotenv import load_dotenv
from requests import get

logger = logging.getLogger()
load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--template", default="template.html", type=pathlib.Path)
parser.add_argument("-o", "--output", default="stats.html", type=pathlib.Path)
parser.add_argument("-c", "--cookies", default=None)
parser.add_argument("-l", "--lang", "--language", choices=genshin.LANGS, default="en-us")


class GenshinRes:
    user: genshin.models.FullGenshinUserStats
    abyss: genshin.models.SpiralAbyss
    diary: genshin.models.Diary
    reward: genshin.models.ClaimedDailyReward
    reward_info: genshin.models.DailyRewardInfo
    showcase: list[str]

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class HsrRes:
    user: genshin.models.StarRailUserStats
    characters: list[genshin.models.StarRailDetailCharacter]
    diary: genshin.models.Diary
    forgotten_hall: genshin.models.StarRailChallenge
    reward: genshin.models.ClaimedDailyReward
    reward_info: genshin.models.DailyRewardInfo

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def format_date(date: datetime) -> str:
    tz = pytz.timezone("Asia/Jakarta")
    now = date.now(tz=tz)
    return f"{now.strftime('%b')} {now.strftime('%d')}, {now.strftime('%Y')} {now.strftime('%H:%M %z')}"


class AnimeGame(genshin.Client):
    args: argparse.Namespace
    mbb_api: str = "https://api.mhankbarbar.tech"

    def __init__(self):
        self.args = parser.parse_args()
        _c = self.args.cookies or os.getenv("COOKIES")
        cookies = json.loads(_c)
        super().__init__(cookies, debug=False, game=genshin.Game.GENSHIN)

    async def _claim_daily(self, game: typing.Optional[genshin.types.Game] = None):
        try:
            await self.claim_daily_reward(game=game, lang=self.args.lang, reward=False)
        except (genshin.AlreadyClaimed, genshin.GeetestTriggered):
            pass
        finally:
            reward = await self.claimed_rewards(game=game, lang=self.args.lang).next()
            reward_info = await self.get_reward_info(game=game, lang=self.args.lang)
        return reward, reward_info

    def _get_character_showcase(self, game: str, uid: int):
        if game == "genshin":
            res = get(f"{self.mbb_api}/genshin_card?uid={uid}")
        else:
            pass  # TODO: add hsr
        if res.status_code == 200:
            return res.json()["result"]

    async def get_genshin_res(self):
        user = await self.get_full_genshin_user(0, lang=self.args.lang)
        abyss = user.abyss.current if user.abyss.current.floors else user.abyss.previous
        diary = await self.get_genshin_diary()

        reward, reward_info = await self._claim_daily()
        showcase = self._get_character_showcase("genshin", self.uids.get(genshin.Game.GENSHIN))

        return GenshinRes(
            user=user,
            abyss=abyss,
            diary=diary,
            reward=reward,
            reward_info=reward_info,
            showcase=showcase
        )

    async def get_hsr_res(self):
        user = await self.get_starrail_user()
        diary = None  # await self.get_starrail_diary()  # skip this sh1t for now bcz error, idk why
        forgotten_hall = await self.get_starrail_challenge(previous=True)
        characters = await self.get_starrail_characters()

        reward, reward_info = await self._claim_daily(genshin.Game.STARRAIL)

        return HsrRes(
            user=user,
            characters=characters.avatar_list,
            diary=diary,
            forgotten_hall=forgotten_hall,
            reward=reward,
            reward_info=reward_info
        )

    async def main(self):
        _genshin, _hsr = await asyncio.gather(*[
            self.get_genshin_res(),
            self.get_hsr_res()
        ])
        template: jinja2.Template = jinja2.Template(self.args.template.read_text())
        rendered = template.render(
            genshin=_genshin,
            hsr=_hsr,
            _int=int,
            updated_at=format_date(_hsr.reward.time)
        )
        self.args.output.write_text(rendered)


if __name__ == "__main__":
    asyncio.run(AnimeGame().main())
