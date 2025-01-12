import argparse
import asyncio
import functools
import logging
import os
import pathlib
import shutil
from datetime import datetime
from typing import List, Optional, Tuple

import genshin
import jinja2
import pytz
import requests
from dotenv import load_dotenv

from lib.codes import GetCodes

logger = logging.getLogger("AnimeGameStats")
load_dotenv()

# Constants
MBB_API = "https://api.mhankbarbar.me"
DEFAULT_TEMPLATE_PATH = "templates/template.html"
DEFAULT_OUTPUT_PATH = "stats.html"
GENSHIN = genshin.Game.GENSHIN
HSR = genshin.Game.STARRAIL
ZZZ = genshin.Game.ZZZ


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
    showcase: List[str]
    showcase_names: List[str]
    profile: str

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class ZZZRes:
    user: genshin.models.ZZZUserStats
    characters: List[genshin.models.ZZZPartialAgent]
    reward: genshin.models.ClaimedDailyReward
    reward_info: genshin.models.DailyRewardInfo

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

def handle_error(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            return None
    return wrapper


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
        super().__init__(_c, debug=False, game=GENSHIN, lang=self.args.lang)

    async def _claim_daily(self, game: Optional[genshin.Game] = None) -> Tuple[
        genshin.models.ClaimedDailyReward, genshin.models.DailyRewardInfo
    ]:
        logger.info("Claiming daily reward")
        """Claim the daily reward and retrieve reward information."""
        try:
            await self.claim_daily_reward(game=game, lang=self.args.lang, reward=False)
        except (genshin.AlreadyClaimed, genshin.DailyGeetestTriggered):
            pass
        finally:
            reward = await self.claimed_rewards(game=game, lang=self.args.lang).next()
            reward_info = await self.get_reward_info(game=game, lang=self.args.lang)
        return reward, reward_info

    def _get_character_showcase(self, game: genshin.Game, uid: int) -> Optional[List[str]]:
        logger.info("Getting character showcase")
        url = f"{MBB_API}/{'genshin' if game == GENSHIN else 'hsr'}_card?uid={uid}"
        res = requests.get(url)
        if res.status_code == 200:
            return save_images(res.json()["result"])
        return None

    def _get_user_profile(self, game: genshin.Game, uid: int) -> Optional[str]:
        logger.info("Getting user profile")
        url = f"{MBB_API}/{'genshin' if game == GENSHIN else 'hsr'}_profile?uid={uid}"
        res = requests.get(url)
        if res.status_code == 200:
            return save_images(res.json()["result"], _type="profile")
        return None

    async def get_genshin_res(self) -> GenshinRes | None:
        logger.info("Executing get_genshin_res")
        try:
            user = await self.get_genshin_user(0)
            abyss = await handle_error(self.get_spiral_abyss)(0, previous=True)
            diary = await handle_error(self.get_genshin_diary)()
            reward, reward_info = await self._claim_daily()
            showcase = None
            profile = None
            if not self.args.skip_images:
                showcase = self._get_character_showcase(GENSHIN, self.uids.get(GENSHIN))
                profile = self._get_user_profile(GENSHIN, self.uids.get(GENSHIN))
            await self.codes.redeem_codes(self, GENSHIN)
            return GenshinRes(
                user=user,
                abyss=abyss,
                diary=diary,
                reward=reward,
                reward_info=reward_info,
                showcase=showcase,
                profile=profile,
            )
        except genshin.AccountNotFound:
            logger.info("Genshin account not found")
            return None

    async def get_hsr_res(self) -> HsrRes | None:
        logger.info("Executing get_hsr_res")
        try:
            user = await self.get_starrail_user(0)
            diary = await handle_error(self.get_starrail_diary)()
            forgotten_hall = await handle_error(self.get_starrail_challenge)()
            characters = await handle_error(self.get_starrail_characters)()
            reward, reward_info = await self._claim_daily(HSR)
            showcase = None
            profile = None
            showcase_names = []
            if not self.args.skip_images:
                showcase = self._get_character_showcase(HSR, self.uids.get(HSR))
                profile = self._get_user_profile(HSR, self.uids.get(HSR))
                if showcase:
                    for s in showcase:
                        showcase_names.append(
                            " ".join(s.split("/")[-1].split("_")[0].split("-"))
                        )
            await self.codes.redeem_codes(self, HSR)
            return HsrRes(
                user=user,
                characters=characters.avatar_list,
                diary=diary,
                forgotten_hall=forgotten_hall,
                reward=reward,
                reward_info=reward_info,
                showcase=showcase,
                profile=profile,
                showcase_names=showcase_names
            )
        except genshin.AccountNotFound:
            logger.info("HSR account not found")
            return None

    async def get_zzz_res(self) -> ZZZRes | None:
        logger.info("Executing get_zzz_res")
        try:
            user = await self.get_zzz_user(0)
            reward, reward_info = await self._claim_daily(ZZZ)
            characters = await self.get_zzz_agents()
            await self.codes.redeem_codes(self, ZZZ)
            return ZZZRes(
                user=user,
                characters=characters,
                reward=reward,
                reward_info=reward_info,
            )
        except genshin.AccountNotFound:
            logger.info("ZZZ account not found")
            return None

    async def main(self):
        _genshin, _hsr, _zzz = await asyncio.gather(*[
            self.get_genshin_res(),
            self.get_hsr_res(),
            self.get_zzz_res(),
        ])
        template: jinja2.Template = jinja2.Template(self.args.template.read_text())
        rendered = template.render(
            genshin=_genshin,
            hsr=_hsr,
            zzz=_zzz,
            lang=self.args.lang,
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
    parser.add_argument("-si", "--skip-images", action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    clear_images()
    args = parse_arguments()
    if args.debug:
        logger.setLevel(logging.INFO)
    asyncio.run(AnimeGame(args, GetCodes()).main())
