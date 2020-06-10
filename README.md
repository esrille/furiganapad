# ふりがなパッド (ベータ<ruby>版<rp>(</rp><rt>ばん</rt><rp>)</rp></ruby>)
　「ふりがなパッド」は、<ruby>総<rp>(</rp><rt>そう</rt><rp>)</rp></ruby>ふりがなをうった<ruby>文章<rp>(</rp><rt>ぶんしょう</rt><rp>)</rp></ruby>をかんたんにつくれるテキストエディターです。「[ひらがなIME](https://github.com/esrille/ibus-hiragana)」といっしょにつかうと、<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>に<ruby>自動的<rp>(</rp><rt>じどうてき</rt><rp>)</rp></ruby>にふりがなをふっていきます。

## つかいかた
　プログラムのファイル名は"furiganapad"です。
　GUIで起動するときは、アプリケーションの一覧から[ふりがなパッド]を選択してください。
　コマンド ラインから<ruby>起動<rp>(</rp><rt>きどう</rt><rp>)</rp></ruby>するときは、つぎのようにタイプします。
```
$ furiganapad [ファイル名...]
```
　ファイル<ruby>名<rp>(</rp><rt>めい</rt><rp>)</rp></ruby>の<ruby>部分<rp>(</rp><rt>ぶぶん</rt><rp>)</rp></ruby>には、ひらきたいファイルのなまえをタイプします。あたらしいファイルをつくるときは、ファイル<ruby>名<rp>(</rp><rt>めい</rt><rp>)</rp></ruby>は<ruby>指定<rp>(</rp><rt>してい</rt><rp>)</rp></ruby>しなくてもかまいません。

## スクリーン ショット
![「ふりがなパッド」のスクリーンショット](screenshot.png)

## ふりがなパッドのインストール<ruby>方法<rp>(</rp><rt>ほうほう</rt><rp>)</rp></ruby>
　つかっているOSがFedora, Ubuntu, Raspberry Pi OSのどれかなら、インストール<ruby>用<rp>(</rp><rt>よう</rt><rp>)</rp></ruby>のソフトウェア パッケージを、[Releases](https://github.com/esrille/furiganapad/releases)ページからダウンロードできます。

　「ふりがなパッド」をじぶんでビルドしてインストールしたいときは、つぎの<ruby>手順<rp>(</rp><rt>てじゅん</rt><rp>)</rp></ruby>でインストールできます。
```
$ git clone https://github.com/esrille/furiganapad.git
$ ./autogen.sh
$ make
$ sudo make install
```
　じぶんでビルドした「ふりがなパッド」をアンインストールするときは、つぎのようにします:
```
$ sudo make uninstall
```
　じぶんでソースコードを<ruby>改造<rp>(</rp><rt>かいぞう</rt><rp>)</rp></ruby>して<ruby>実験<rp>(</rp><rt>じっけん</rt><rp>)</rp></ruby>したいときもあるかもしれません。そういうときは、「ふりがなパッド」をインストールしないで、ソースコードをちょくせつ<ruby>実行<rp>(</rp><rt>じっこう</rt><rp>)</rp></ruby>することもできます。
```
$ src/furiganapad
```

## ふりがなについて
　こども<ruby>用<rp>(</rp><rt>よう</rt><rp>)</rp></ruby>の<ruby>本<rp>(</rp><rt>ほん</rt><rp>)</rp></ruby>には、すべての<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>にふりがながふってある<ruby>本<rp>(</rp><rt>ほん</rt><rp>)</rp></ruby>もすくなくありません。そうしたふりがなのつけかたを「<ruby>総<rp>(</rp><rt>そう</rt><rp>)</rp></ruby>ふりがな」とか「<ruby>総<rp>(</rp><rt>そう</rt><rp>)</rp></ruby>ルビ」といいます。

　さいきんでは、「やさしい<ruby>日本語<rp>(</rp><rt>にほんご</rt><rp>)</rp></ruby>」でかいた<ruby>文章<rp>(</rp><rt>ぶんしょう</rt><rp>)</rp></ruby>をみたり、かいたりする<ruby>機会<rp>(</rp><rt>きかい</rt><rp>)</rp></ruby>がふえてきました。「やさしい<ruby>日本語<rp>(</rp><rt>にほんご</rt><rp>)</rp></ruby>」の<ruby>文章<rp>(</rp><rt>ぶんしょう</rt><rp>)</rp></ruby>も<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>にふりがながふってあります。

　いまではウェブブラウザも、ふりがなを<ruby>表示<rp>(</rp><rt>ひょうじ</rt><rp>)</rp></ruby>できるようになっています。「ふりがなパッド」は、<ruby>総<rp>(</rp><rt>そう</rt><rp>)</rp></ruby>ルビの<ruby>文章<rp>(</rp><rt>ぶんしょう</rt><rp>)</rp></ruby>をかんたんに<ruby>作成<rp>(</rp><rt>さくせい</rt><rp>)</rp></ruby>したり<ruby>編集<rp>(</rp><rt>へんしゅう</rt><rp>)</rp></ruby>したりできるようにかんがえてあります。

## とくべつな<ruby>機能<rp>(</rp><rt>きのう</rt><rp>)</rp></ruby>
　「ふりがなパッド」には、テキストエディターの<ruby>基本的<rp>(</rp><rt>きほんてき</rt><rp>)</rp></ruby>な<ruby>機能<rp>(</rp><rt>きのう</rt><rp>)</rp></ruby>のほかに、つぎのような<ruby>機能<rp>(</rp><rt>きのう</rt><rp>)</rp></ruby>があります。

### <ruby>編集<rp>(</rp><rt>へんしゅう</rt><rp>)</rp></ruby>メニュー

#### ふりがなをふる...
　えらんだ<ruby>字句<rp>(</rp><rt>じく</rt><rp>)</rp></ruby>に、べつのふりがなをふったり、ふりがなをとりけしたりできます。ふりがなをふりたい<ruby>字句<rp>(</rp><rt>じく</rt><rp>)</rp></ruby>を<ruby>選択<rp>(</rp><rt>せんたく</rt><rp>)</rp></ruby>してから、「ふりがなをふる...」を<ruby>実行<rp>(</rp><rt>じっこう</rt><rp>)</rp></ruby>します。ふりがな<ruby>用<rp>(</rp><rt>よう</rt><rp>)</rp></ruby>のテキストボックスにふりがなを<ruby>入力<rp>(</rp><rt>にゅうりょく</rt><rp>)</rp></ruby>したら、[Enter]キーをおしてふりがなをふります。

#### ひらがなにもどす...
　ふりがなのふられた<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>をひらがなにもどします。ふりがなのふられている<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>のおわりにカーソルを<ruby>移動<rp>(</rp><rt>いどう</rt><rp>)</rp></ruby>してから、「ひらがなにもどす...」を<ruby>実行<rp>(</rp><rt>じっこう</rt><rp>)</rp></ruby>します。

### <ruby>設定<rp>(</rp><rt>せってい</rt><rp>)</rp></ruby>メニュー

#### ふりがな
　メニューの「ふりがな」にチェックをつけておくと、<ruby>入力<rp>(</rp><rt>にゅうりょく</rt><rp>)</rp></ruby>された<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>に<ruby>自動的<rp>(</rp><rt>じどうてき</rt><rp>)</rp></ruby>にふりがなをふっていきます。チェックがついていないと、ふりがなをつけずに<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>を<ruby>入力<rp>(</rp><rt>にゅうりょく</rt><rp>)</rp></ruby>できます。

#### ながい<ruby>文<rp>(</rp><rt>ぶん</rt><rp>)</rp></ruby>をめだたせる
　メニューの「ながい<ruby>文<rp>(</rp><rt>ぶん</rt><rp>)</rp></ruby>をめだたせる」にチェックをつけておくと、ながい<ruby>文<rp>(</rp><rt>ぶん</rt><rp>)</rp></ruby>を<ruby>色<rp>(</rp><rt>いろ</rt><rp>)</rp></ruby>づけして<ruby>表示<rp>(</rp><rt>ひょうじ</rt><rp>)</rp></ruby>します。一<ruby>文<rp>(</rp><rt>ぶん</rt><rp>)</rp></ruby>のながさが５０<ruby>字<rp>(</rp><rt>じ</rt><rp>)</rp></ruby>をこえると、<ruby>文<rp>(</rp><rt>ぶん</rt><rp>)</rp></ruby>の<ruby>背景<rp>(</rp><rt>はいけい</rt><rp>)</rp></ruby>が<ruby>黄<rp>(</rp><rt>き</rt><rp>)</rp></ruby><ruby>色<rp>(</rp><rt>いろ</rt><rp>)</rp></ruby>になります。さらに、６０<ruby>字<rp>(</rp><rt>じ</rt><rp>)</rp></ruby>をこえると、<ruby>文<rp>(</rp><rt>ぶん</rt><rp>)</rp></ruby>の<ruby>背景<rp>(</rp><rt>はいけい</rt><rp>)</rp></ruby>が<ruby>赤色<rp>(</rp><rt> あかいろ</rt><rp>)</rp></ruby>になります。

※　ながい<ruby>文<rp>(</rp><rt>ぶん</rt><rp>)</rp></ruby>はみじかくきって、かきなおすと、よみやすくなります。

## ファイル<ruby>形式<rp>(</rp><rt>けいしき</rt><rp>)</rp></ruby>と<ruby>応用<rp>(</rp><rt>おうよう</rt><rp>)</rp></ruby>のしかた
　「ふりがなパッド」は、UTF-8でエンコードされたテキストファイルのよみかきができます。

　ふりがなは、ユニコードのルビ<ruby>用<rp>(</rp><rt>よう</rt><rp>)</rp></ruby>のコードポイントU+FFF9からU+FFFBをつかって<ruby>保存<rp>(</rp><rt>ほぞん</rt><rp>)</rp></ruby>しています。ただし、このコードポイントに<ruby>対応<rp>(</rp><rt>たいおう</rt><rp>)</rp></ruby>しているソフトウェアはあまりおおくありません。

　それでも、ユニコードのルビをHTMLのrubyタグに<ruby>変換<rp>(</rp><rt>へんかん</rt><rp>)</rp></ruby>したりするのはかんたんです。つぎの<ruby>例<rp>(</rp><rt>れい</rt><rp>)</rp></ruby>では、「ふりがなパッド」でかいたREADME.txtを、スクリプトをつかって、README.mdに<ruby>変換<rp>(</rp><rt>へんかん</rt><rp>)</rp></ruby>しています。
```
$ tools/convert_to_tag.py README.txt README.md
```
convert_to_tag.pyスクリプトもこのレポジトリのなかにおいてあります。

## ふりがなパッドのプログラム
　「ふりがなパッド」は、<ruby>Python<rp>(</rp><rt>パイソン</rt><rp>)</rp></ruby>でかいたGTKのプログラムです。<ruby>標準<rp>(</rp><rt>ひょうじゅん</rt><rp>)</rp></ruby>の[Gtk.TextView](https://lazka.github.io/pgi-docs/index.html#Gtk-3.0/classes/TextView.html)のかわりに、ふりがなに<ruby>対応<rp>(</rp><rt>たいおう</rt><rp>)</rp></ruby>したTextViewを[Gtk.DrawingArea](https://lazka.github.io/pgi-docs/index.html#Gtk-3.0/classes/DrawingArea.html)をつかってつくっています。<ruby>文字<rp>(</rp><rt>もじ</rt><rp>)</rp></ruby>の<ruby>描画<rp>(</rp><rt>びょうが</rt><rp>)</rp></ruby>には、[Pango](https://lazka.github.io/pgi-docs/index.html#Pango-1.0)をつかっています。ぜんたいでは2,400<ruby>行<rp>(</rp><rt>ぎょう</rt><rp>)</rp></ruby>ほどのプログラムです(2020<ruby>年<rp>(</rp><rt>ねん</rt><rp>)</rp></ruby>6<ruby>月<rp>(</rp><rt>がつ</rt><rp>)</rp></ruby><ruby>現在<rp>(</rp><rt>げんざい</rt><rp>)</rp></ruby>)。
