# Anime Game Stats

Anime Game Stats is a Python script that retrieves statistics and information from anime games, specifically Genshin Impact and a game called HSR. It utilizes the genshin library to interact with the Hoyolab API and retrieve data such as user stats, achievements, rewards, and character showcases. The retrieved data is then rendered using a Jinja2 template to generate an HTML report.

## Features

- Retrieves Genshin Impact user stats including full stats, Spiral Abyss progress, diary, daily rewards, and character showcases.
- Retrieves HSR (Star Rail) user stats including user stats, character details, diary, forgotten hall challenge, daily rewards, and character showcases (todo).
- Claims daily rewards for both games and redeems codes for extra rewards.
- Generates an HTML report using a Jinja2 template.

## Getting Started

To use Anime Game Stats, you can follow these steps:

### Fork this repository by clicking the "Fork" button on the top right corner of this page. This will create a copy of the repository in your GitHub account.
#### Copy your cookies

Log in at [hoyolab](https://hoyolab.com), open the developer console by pressing F12 on your keyboard and navigate to the console tab. Finally, paste the following in the console to copy your cookies to your clipboard

`copy(document.cookie)`

![image](https://github.com/MhankBarBar/anime-game-stats/assets/55822959/5b098540-b3f4-4dd8-b74b-fdb3284e2d99)

After that, make it cookie into json format, for example
```json
{"ltuid": "...", "ltoken": "....", "account_id": "...", "cookie_token": "..."}
```
### Create a repository secret

![image](https://github.com/MhankBarBar/anime-game-stats/assets/55822959/5fd34244-bca2-4c9a-afad-c12fca91134d)

### Paste your json format cookie in the repository secret

![image](https://github.com/MhankBarBar/anime-game-stats/assets/55822959/08b7aa56-f60c-482c-9425-4db52b199e97)

For now the cookie is just supported for genshin and hsr at the same account.

### Give Action Write Permissoion

![image](https://github.com/MhankBarBar/anime-game-stats/assets/55822959/152ee424-6db1-4933-9fa9-26fe0327eac7)

![image](https://github.com/MhankBarBar/anime-game-stats/assets/55822959/6ee01665-903d-4337-9b47-591a5dc693d5)

### Run the action manually

![image](https://github.com/MhankBarBar/anime-game-stats/assets/55822959/dae0ea7f-3386-467a-9fd5-fb12d5878022)


And you're set! From now on the repo will claim any new codes and redeem the daily check-in rewards at Hoyolab for you every 6 hours!

## Costumization
You can customize the `template.html` file to modify the appearance and layout of the generated HTML report.

## Acknowledgments
- [genshin](https://github.com/thesadru/genshin.py) library by thesadru for Genshin Impact, HSR and Honkai Impact 3rd API integration.
