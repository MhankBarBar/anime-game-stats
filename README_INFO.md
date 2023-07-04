# Anime Game Stats

Anime Game Stats is a Python script that retrieves and displays statistics and information from different anime games, such as Genshin Impact and HSR. The script makes use of various APIs to fetch data and provides a customizable HTML template for rendering the output.

## Features

- Retrieves user stats, abyss information, diary entries, rewards, and character showcases from the Genshin Impact and HSR games.
- Supports customization through command-line arguments.
- Claims daily rewards and provides reward information.
- Downloads and saves character showcase images.
- Claim codes and redeem automatically
- Generates an HTML report using a customizable template.

## Getting Started

To use Anime Game Stats, you can follow these steps:

- Fork this repository by clicking the "Fork" button on the top right corner of this page. This will create a copy of the repository in your GitHub account.
- Copy your cookies

Log in at [hoyolab](https://hoyolab.com), open the developer console by pressing F12 on your keyboard and navigate to the console tab. Finally, paste the following in the console to copy your cookies to your clipboard

`copy(document.cookie)`

![image](https://github.com/MhankBarBar/anime-game-stats/assets/55822959/5b098540-b3f4-4dd8-b74b-fdb3284e2d99)

After that, make it cookie into json format, for example
```json
{"ltuid": "...", "ltoken": "....", "account_id": "...", "cookie_token": "..."}
```
- Create a repository secret

![image](https://github.com/MhankBarBar/anime-game-stats/assets/55822959/5fd34244-bca2-4c9a-afad-c12fca91134d)

- Paste your json format cookie in the repository secret

![image](https://github.com/MhankBarBar/anime-game-stats/assets/55822959/08b7aa56-f60c-482c-9425-4db52b199e97)

For now the cookie is just supported for genshin and hsr at the same account.

And you're set! From now on the repo will claim any new codes and redeem the daily check-in rewards at Hoyolab for you every 6 hours!

## Costumization
HTML Template: You can customize the HTML template (`template.html`) to change the look and feel of the generated report. Modify the template file according to your requirements, including placeholders for the data

## Acknowledgments
- [genshin.py](https://github.com/thesadru/genshin.py) library by thesadru for Genshin Impact, HSR and Honkai Impact 3rd API integration.

Feel free to modify the README file according to your needs, adding more details or instructions if necessary.
