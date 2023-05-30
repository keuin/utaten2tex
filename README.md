utaten2tex: convert lyrics from `utaten.com` to LaTeX

Usage: <main.py> [path_to_html_file]

If HTML file is not specified, the program will read HTML text from STDIN.

Example:

```shell
curl https://utaten.com/lyric/sa16080309/ | python3 main.py
```

Make sure you have `beautifulsoup` and `html5lib` installed.