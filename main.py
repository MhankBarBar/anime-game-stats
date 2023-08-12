import argparse
import asyncio
import json
import logging
import os
import pathlib
from datetime import datetime
from typing import List, Optional, Tuple

import genshin
import jinja2
import pytz
import requests
from dotenv import load_dotenv

from lib.codes import GetCodes

logger = logging.getLogger()
load_dotenv()

# Constants
MBB_API = "https://api.mhankbarbar.tech"
DEFAULT_TEMPLATE_PATH = "template.html"
DEFAULT_OUTPUT_PATH = "stats.html"


class GenshinRes:
    user: genshin.models.FullGenshinUserStats
    abyss: genshin.models.SpiralAbyss
    diary: genshin.models.Diary
    reward: genshin.models.ClaimedDailyReward
    reward_info: genshin.models.DailyRewardInfo
    showcase: List[str]
    profile: str

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class HsrRes:
    user: genshin.models.StarRailUserStats
    characters: List[genshin.models.StarRailDetailCharacter]
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


def clear_and_save_images(urls: List[str] | str, _type: str="showcase") -> List[str] | str:
    if _type not in ("showcase", "profile"):
        raise ValueError("_type must be either showcase or profile")
    path = f"images/{_type}"
    if os.path.exists(path):
        for filename in os.listdir(path):
            os.unlink(os.path.join(path, filename))
    os.makedirs(path, exist_ok=True)
    saved_files = []
    urls = [urls] if isinstance(urls, str) else urls
    for url in urls:
        response = requests.get(url)
        if response.status_code == 200:
            filename = os.path.join(path, url.split("/")[-1])
            with open(filename, "wb") as f:
                f.write(response.content)
            saved_files.append(filename)
    return saved_files if _type == "showcase" else saved_files[0]


class AnimeGame(genshin.Client):

    def __init__(self, args: argparse.Namespace, codes: GetCodes):
        self.args = args
        self.codes = codes
        _c = self.args.cookies or os.getenv("COOKIES")
        cookies = json.loads(_c)
        super().__init__(cookies, debug=False, game=genshin.Game.GENSHIN)

    async def _claim_daily(self, game: Optional[genshin.Game] = None) -> Tuple[
        genshin.models.ClaimedDailyReward, genshin.models.DailyRewardInfo
    ]:
        """Claim the daily reward and retrieve reward information."""
        try:
            await self.claim_daily_reward(game=game, lang=self.args.lang, reward=False)
        except (genshin.AlreadyClaimed, genshin.GeetestTriggered):
            pass
        finally:
            reward = await self.claimed_rewards(game=game, lang=self.args.lang).next()
            reward_info = await self.get_reward_info(game=game, lang=self.args.lang)
        return reward, reward_info

    def _get_character_showcase(self, game: str, uid: int) -> Optional[List[str]]:
        if game == "genshin":
            res = requests.get(f"{MBB_API}/genshin_card?uid={uid}")
        else:
            return None  # TODO: add HSR implementation
        if res.status_code == 200:
            return clear_and_save_images(res.json()["result"])
        return None

    def _get_user_profile(self, uid: int) -> Optional[str]:
        res = requests.get(f"{MBB_API}/genshin_profile?uid={uid}")
        if res.status_code == 200:
            return clear_and_save_images(res.json()["result"], _type="profile")
        return None

    async def get_genshin_res(self) -> GenshinRes:
        user = await self.get_full_genshin_user(0, lang=self.args.lang)
        abyss = user.abyss.current if user.abyss.current.floors else user.abyss.previous
        diary = await self.get_genshin_diary()
        reward, reward_info = await self._claim_daily()
        showcase = self._get_character_showcase("genshin", self.uids.get(genshin.Game.GENSHIN))
        profile = self._get_user_profile(self.uids.get(genshin.Game.GENSHIN))
        codes = self.codes.get_codes()
        await self.codes.redeem_codes(self, codes)
        return GenshinRes(
            user=user,
            abyss=abyss,
            diary=diary,
            reward=reward,
            reward_info=reward_info,
            showcase=showcase,
            profile=profile
        )

    async def get_hsr_res(self) -> HsrRes:
        user = await self.get_starrail_user()
        diary = await self.get_starrail_diary()
        forgotten_hall = await self.get_starrail_challenge()
        characters = await self.get_starrail_characters()
        reward, reward_info = await self._claim_daily(genshin.Game.STARRAIL)
        codes = self.codes.get_codes(genshin.Game.STARRAIL)
        await self.codes.redeem_codes(self, codes, genshin.Game.STARRAIL)
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
            _enumerate=enumerate,
            updated_at=format_date(_hsr.reward.time)
        )
        self.args.output.write_text(rendered)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--template", default=DEFAULT_TEMPLATE_PATH, type=pathlib.Path)
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT_PATH, type=pathlib.Path)
    parser.add_argument("-c", "--cookies", default=None)
    parser.add_argument("-l", "--lang", "--language", choices=genshin.LANGS, default="en-us")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    asyncio.run(AnimeGame(args, GetCodes()).main())
