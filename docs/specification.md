# ファイルの￹仕様￺しよう￻と￹応用￺おうよう￻

## ファイルの￹仕様￺しよう￻

　「ふりがなパッド」は、UTF-8でエンコードされたテキストファイルのよみかきができます。
　ふりがなは、[ユニコードのルビ￹用￺よう￻のコードポイントU+FFF9からU+FFFB](https://www.unicode.org/charts/nameslist/n_FFF0.html)をつかって￹保存￺ほぞん￻しています。

## ￹応用￺おうよう￻

　ユニコードのルビをHTMLのrubyタグに￹変換￺へんかん￻したりするのはかんたんです。
つぎの￹例￺れい￻では、「ふりがなパッド」でかいたREADME.txtを、スクリプトをつかって、README.mdに￹変換￺へんかん￻しています。
```
$ tools/convert_to_tag.py README.txt README.md
```
[convert_to_tag.py](https://github.com/esrille/furiganapad/blob/master/tools/convert_to_tag.py)スクリプトも「ふりがなパッド」のレポジトリのなかにおいてあります。
