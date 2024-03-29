# ふりがなパッド (ベータ￹版￺ばん￻)
　「ふりがなパッド」は、ふりがなをうった￹文章￺ぶんしょう￻をかんたんにつくれるテキストエディターです。「[ひらがなIME](https://github.com/esrille/ibus-hiragana)」といっしょにつかうと、￹漢字￺かんじ￻に￹自動的￺じどうてき￻にふりがなをふっていきます。

![「ふりがなパッド」のスクリーンショット](screenshot.png)

## ふりがなについて
　こども￹用￺よう￻の￹本￺ほん￻には、すべての￹漢字￺かんじ￻にふりがなをふってある￹本￺ほん￻もすくなくありません。そうしたふりがなのつけかたを「￹総￺そう￻ふりがな」とか「￹総￺そう￻ルビ」といいます。

　さいきんでは、「やさしい￹日本語￺にほんご￻」でかいた￹文章￺ぶんしょう￻をみたり、かいたりする￹機会￺きかい￻がふえてきました。「やさしい￹日本語￺にほんご￻」の￹文章￺ぶんしょう￻も￹漢字￺かんじ￻にふりがながふってあります。

　いまではウェブブラウザも、ふりがなを￹表示￺ひょうじ￻できるようになっています。「ふりがなパッド」は、￹総￺そう￻ルビの￹文章￺ぶんしょう￻をかんたんに￹作成￺さくせい￻したり￹編集￺へんしゅう￻したりできるようにつくられています。

## ふりがなパッドのプログラム
　「ふりがなパッド」は、￹Python￺パイソン￻でかいたGTKのプログラムです。￹標準￺ひょうじゅん￻の[Gtk.TextView](https://lazka.github.io/pgi-docs/index.html#Gtk-3.0/classes/TextView.html)のかわりに、ふりがなに￹対応￺たいおう￻したFuriganaViewを[Gtk.DrawingArea](https://lazka.github.io/pgi-docs/index.html#Gtk-3.0/classes/DrawingArea.html)をつかってつくっています。￹文字￺もじ￻の￹描画￺びょうが￻には、[Pango](https://lazka.github.io/pgi-docs/index.html#Pango-1.0)をつかっています。

## ￹資料￺しりょう￻

　つかいかたについては、「ふりがなパッドの￹手￺て￻びき」をみてください。

- [ふりがなパッドの￹手￺て￻びき](https://esrille.github.io/furiganapad/)
- [ふりがなパッドの￹開発￺かいはつ￻について](https://github.com/esrille/furiganapad/blob/master/CONTRIBUTING.md)
