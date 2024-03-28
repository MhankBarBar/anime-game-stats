import argparse
import asyncio
import json
import logging
import os
import pathlib
import re
import shutil
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
    notes: genshin.models.Notes
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
    notes: genshin.models.StarRailNote
    showcase: List[str]
    showcase_names: List[str]
    profile: str

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def format_date(date: datetime) -> str:
    tz = pytz.timezone("Asia/Jakarta")
    now = date.now(tz=tz)
    return f"{now.strftime('%b')} {now.strftime('%d')}, {now.strftime('%Y')} {now.strftime('%H:%M %z')}"


def clear_images() -> None:
    for x in ("showcase", "profile"):
        if os.path.exists(f"images/{x}"):
            shutil.rmtree(f"images/{x}")


def save_images(urls: List[str] | str, _type: str = "showcase") -> List[str] | str:
    if _type not in ("showcase", "profile"):
        raise ValueError("_type must be either showcase or profile")
    path = f"images/{_type}"
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
        super().__init__(cookies, debug=False, game="genshin", lang=self.args.lang)

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
        url = f"{MBB_API}/genshin_card?uid={uid}" if game == "genshin" else f"{MBB_API}/hsr_card?uid={uid}"
        res = requests.get(url).json()
        if res["status"] == 200:
            return save_images(res["result"])
        return None

    def _get_user_profile(self, game: str, uid: int) -> Optional[str]:
        url = f"{MBB_API}/genshin_profile?uid={uid}" if game == "genshin" else f"{MBB_API}/hsr_profile?uid={uid}"
        res = requests.get(url).json()
        if res["status"] == 200:
            return save_images(res["result"], _type="profile")
        return None

    async def get_genshin_res(self) -> GenshinRes:
        user = await self.get_full_genshin_user(0, lang=self.args.lang)
        abyss = user.abyss.current if user.abyss.current.floors else user.abyss.previous
        diary = await self.get_genshin_diary()
        reward, reward_info = await self._claim_daily()
        notes = await self.get_genshin_notes()
        showcase = None
        profile = None
        if not self.args.skip_images:
            showcase = self._get_character_showcase("genshin", self.uids.get("genshin"))
            profile = self._get_user_profile("genshin", self.uids.get("genshin"))
        codes = self.codes.get_codes()
        await self.codes.redeem_codes(self, codes)
        return GenshinRes(
            user=user,
            abyss=abyss,
            diary=diary,
            reward=reward,
            reward_info=reward_info,
            showcase=showcase,
            profile=profile,
            notes=notes
        )

    async def get_hsr_res(self) -> HsrRes:
        user = await self.get_starrail_user()
        diary = await self.get_starrail_diary()
        forgotten_hall = await self.get_starrail_challenge()
        characters = await self.get_starrail_characters()
        reward, reward_info = await self._claim_daily("hkrpg")
        notes = await self.get_starrail_notes()
        showcase = None
        profile = None
        showcase_names = []
        if not self.args.skip_images:
            showcase = self._get_character_showcase("hsr", self.uids.get("hkrpg"))
            profile = self._get_user_profile("hsr", self.uids.get("hkrpg"))
            for s in showcase:
                showcase_names.append(
                    " ".join(s.split("/")[-1].split("_"))
                )
        codes = self.codes.get_codes("hkrpg")
        await self.codes.redeem_codes(self, codes, "hkrpg")
        return HsrRes(
            user=user,
            characters=characters.avatar_list,
            diary=diary,
            forgotten_hall=forgotten_hall,
            reward=reward,
            reward_info=reward_info,
            showcase=showcase,
            profile=profile,
            notes=notes,
            showcase_names=showcase_names
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
            _zip=zip,
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
    parser.add_argument("-si", "--skip-images", default=False)
    return parser.parse_args()


if __name__ == "__main__":
    clear_images()
    args = parse_arguments()
    asyncio.run(AnimeGame(args, GetCodes()).main())
