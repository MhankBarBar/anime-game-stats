from time import sleep
from typing import List

import bs4
import genshin
import requests


def _get_file_path(game: genshin.Game) -> str:
    return f"files/redeemed_codes_{'genshin' if game == genshin.Game.GENSHIN else 'hkrpg'}.txt"


class GetCodes:
    HSR_URL: str = "https://honkai-star-rail.fandom.com/wiki/Redemption_Code"
    GENSHIN_URL: str = "https://genshin-impact.fandom.com/wiki/Promotional_Code"

    def get_codes(self, game: genshin.Game = genshin.Game.GENSHIN) -> List[str]:
        url = self._build_url(game)
        response = self._send_request(url)
        soup = self._parse_html(response)
        parsed_codes = self._extract_codes(soup)

        active_codes = [code.text.strip() for code in parsed_codes]
        return active_codes

    def _check_codes(self, codes: List[str], game: genshin.Game = genshin.Game.GENSHIN) -> List[str]:
        file = _get_file_path(game)
        with open(file, "r") as f:
            codes_redeemed = f.read().splitlines()
        return [x for x in codes if x not in codes_redeemed]

    async def redeem_codes(
            self, client: genshin.Client, codes: List[str], game: genshin.Game = genshin.Game.GENSHIN
    ) -> None:
        active_codes = self._check_codes(codes, game)
        file = _get_file_path(game)
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

    def _build_url(self, game: genshin.Game) -> str:
        return self.GENSHIN_URL if game == genshin.Game.GENSHIN else self.HSR_URL

    def _send_request(self, url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def _parse_html(self, html: str) -> bs4.BeautifulSoup:
        return bs4.BeautifulSoup(html, "html.parser")

    def _extract_codes(self, soup: bs4.BeautifulSoup) -> List[bs4.element.Tag]:
        codes = [code for code in soup.find_all("code")]
        return codes
