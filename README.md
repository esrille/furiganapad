# ふりがなパッド
　「ふりがなパッド」は、ふりがなをうった<ruby>文章<rp>(</rp><rt>ぶんしょう</rt><rp>)</rp></ruby>をかんたんにつくれるテキストエディターです。「[ひらがなIME](https://github.com/esrille/ibus-hiragana)」といっしょにつかうと、<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>に<ruby>自動的<rp>(</rp><rt>じどうてき</rt><rp>)</rp></ruby>にふりがなをふっていきます。

![「ふりがなパッド」のスクリーンショット](screenshot.png)

## ふりがなについて
　こども<ruby>用<rp>(</rp><rt>よう</rt><rp>)</rp></ruby>の<ruby>本<rp>(</rp><rt>ほん</rt><rp>)</rp></ruby>には、すべての<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>にふりがなをふってある<ruby>本<rp>(</rp><rt>ほん</rt><rp>)</rp></ruby>もすくなくありません。そうしたふりがなのつけかたを「<ruby>総<rp>(</rp><rt>そう</rt><rp>)</rp></ruby>ふりがな」とか「<ruby>総<rp>(</rp><rt>そう</rt><rp>)</rp></ruby>ルビ」といいます。

　さいきんでは、「やさしい<ruby>日本語<rp>(</rp><rt>にほんご</rt><rp>)</rp></ruby>」でかいた<ruby>文章<rp>(</rp><rt>ぶんしょう</rt><rp>)</rp></ruby>をみたり、かいたりする<ruby>機会<rp>(</rp><rt>きかい</rt><rp>)</rp></ruby>がふえてきました。「やさしい<ruby>日本語<rp>(</rp><rt>にほんご</rt><rp>)</rp></ruby>」の<ruby>文章<rp>(</rp><rt>ぶんしょう</rt><rp>)</rp></ruby>も<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>にふりがながふってあります。

　いまではウェブブラウザも、ふりがなを<ruby>表示<rp>(</rp><rt>ひょうじ</rt><rp>)</rp></ruby>できるようになっています。「ふりがなパッド」は、<ruby>総<rp>(</rp><rt>そう</rt><rp>)</rp></ruby>ルビの<ruby>文章<rp>(</rp><rt>ぶんしょう</rt><rp>)</rp></ruby>をかんたんに<ruby>作成<rp>(</rp><rt>さくせい</rt><rp>)</rp></ruby>したり<ruby>編集<rp>(</rp><rt>へんしゅう</rt><rp>)</rp></ruby>したりできるようにつくられています。

## ふりがなパッドのプログラム
　「ふりがなパッド」は、<ruby>Python<rp>(</rp><rt>パイソン</rt><rp>)</rp></ruby>でかいたGTKのプログラムです。<ruby>標準<rp>(</rp><rt>ひょうじゅん</rt><rp>)</rp></ruby>の[Gtk.TextView](https://lazka.github.io/pgi-docs/index.html#Gtk-3.0/classes/TextView.html)のかわりに、ふりがなに<ruby>対応<rp>(</rp><rt>たいおう</rt><rp>)</rp></ruby>したFuriganaViewを[Gtk.DrawingArea](https://lazka.github.io/pgi-docs/index.html#Gtk-3.0/classes/DrawingArea.html)をつかってつくっています。<ruby>文字<rp>(</rp><rt>もじ</rt><rp>)</rp></ruby>の<ruby>描画<rp>(</rp><rt>びょうが</rt><rp>)</rp></ruby>には、[Pango](https://lazka.github.io/pgi-docs/index.html#Pango-1.0)をつかっています。

## <ruby>資料<rp>(</rp><rt>しりょう</rt><rp>)</rp></ruby>

　つかいかたについては、「ふりがなパッドの<ruby>手<rp>(</rp><rt>て</rt><rp>)</rp></ruby>びき」をみてください。

- [ふりがなパッドの<ruby>手<rp>(</rp><rt>て</rt><rp>)</rp></ruby>びき](https://esrille.github.io/furiganapad/)
- [ふりがなパッドの<ruby>開発<rp>(</rp><rt>かいはつ</rt><rp>)</rp></ruby>について](https://github.com/esrille/furiganapad/blob/master/CONTRIBUTING.md)
