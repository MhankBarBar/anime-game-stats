from time import sleep
from typing import List

import bs4
import genshin
import requests


class GetCodes:
    BASE_URL: str = "https://www.pockettactics.com/"

    GAME_CODES: dict = {
        "genshin": "genshin-impact",
        "hkrpg": "honkai-star-rail"
    }

    def get_codes(self, game: str = "genshin") -> List[str]:
        url = self._build_url(game)
        response = self._send_request(url)
        soup = self._parse_html(response)
        parsed_codes = self._extract_codes(soup, game)

        active_codes = [code.text.strip() for code in parsed_codes]
        return active_codes

    def _check_codes(self, codes: List[str], game: str = "genshin") -> List[str]:
        file = f"files/redeemed_codes_{game}.txt"
        with open(file, "r") as f:
            codes_redeemed = f.read().splitlines()
        return [x for x in codes if x not in codes_redeemed]

    async def redeem_codes(self, client: genshin.Client, codes: List[str], game: genshin.Game = "genshin") -> None:
        active_codes = self._check_codes(codes, game)
        file = f"files/redeemed_codes_{game}.txt"
        for code in active_codes:
            try:
                await client.redeem_code(code, game=game)
            except (genshin.RedemptionClaimed, genshin.RedemptionInvalid,
                    genshin.RedemptionException, genshin.InvalidCookies):
                pass
            finally:
                with open(file, "a") as f:
                    f.write(f"{code}\n")
            sleep(6)

    def _build_url(self, game: str) -> str:
        game_slug = self.GAME_CODES.get(game, "")
        if not game_slug:
            raise Exception(f"Game {game} is not supported")
        return f"{self.BASE_URL}{game_slug}/codes"

    def _send_request(self, url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def _parse_html(self, html: str) -> bs4.BeautifulSoup:
        soup = bs4.BeautifulSoup(html, "html.parser")
        return soup.find("div", {"class": "entry-content"})

    def _extract_codes(self, soup: bs4.BeautifulSoup, game: str) -> List[bs4.element.Tag]:
        codes = []
        _soup = soup.find_all("ul")
        parsed = _soup[0] if game == "genshin" else _soup[:2]
        for _ in parsed:
            codes.extend(_.find_all("strong"))
        return codes
