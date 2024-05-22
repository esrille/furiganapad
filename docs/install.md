# インストール￹方法￺ほうほう￻

　つかっているOSがFedoraかUbuntuであれば、かんたんに「ふりがなパッド」をインストールすることができます。
また、Linuxのアプリストア「[Flathub](https://flathub.org/ja)」から「ふりがなパッド」をインストールすることもできます。

### Fedoraのばあい

　Fedora￹用￺よう￻のソフトウェア パッケージはCoprプロジェクト「[@esrille/releases](https://copr.fedorainfracloud.org/coprs/g/esrille/releases/)」から￹提供￺ていきょう￻しています。
このCoprプロジェクトを￹有効￺ゆうこう￻にするには、いちど、コマンドラインからつぎのように￹実行￺じっこう￻します。

```
sudo dnf copr enable @esrille/releases
```

　あとは、dnfコマンドで「ふりがなパッド」をインストールできます。

```
sudo dnf install furiganapad
```

### Ubuntuのばあい

　Ubuntu￹用￺よう￻のソフトウェア パッケージはPPAレポジトリ「[esrille/releases](https://launchpad.net/~esrille/+archive/ubuntu/releases)」から￹提供￺ていきょう￻しています。
このPPAレポジトリを￹有効￺ゆうこう￻にするには、いちど、コマンドラインからつぎのように￹実行￺じっこう￻します。

```
sudo add-apt-repository ppa:esrille/releases
```

　あとは、aptコマンドで「ふりがなパッド」をインストールできます。

```
sudo apt update
sudo apt install furiganapad
```

### Flathubからインストールする￹方法￺ほうほう￻

　Flathubからインストールするときは、[GNOME Software](https://apps.gnome.org/Software/)を￹利用￺りよう￻するのがかんたんです。
GNOME Softwareが￹起動￺きどう￻したら、ルーペのアイコンをクリックして、「ふりがなパッド」をさがします。
￹英語￺えいご￻￹環境￺かんきょう￻のときは、「furiganapad」と￹入力￺にゅうりょく￻してさがしてください。
￹一覧￺いちらん￻から「ふりがなパッド」を￹選択￺せんたく￻すると、インストールすることができます。

![GNOME Software](furiganapad.flathub.png)

　Flathubからインストールしたソフトウェアは、それぞれ￹専用￺せんよう￻のサンドボックスのなかで￹実行￺じっこう￻されます。
サンドボックスは、インストールしたソフトウェアが￹不正￺ふせい￻なことをおこなえないようにします。
ふりがなパッドのばあいは、ユーザーが￹指定￺してい￻したファイル￹以外￺いがい￻にはアクセスできなくなります。
そのため、￹以前￺いぜん￻ひらいていたファイルを￹自動￺じどう￻でひらく￹機能￺きのう￻などは￹一部￺いちぶ￻、￹制限￺せいげん￻されます。

<br>
**ヒント**: UbuntuでFlathubを￹利用￺りよう￻したいときは、いちどコマンドラインからつぎのように￹実行￺じっこう￻してください。
Fedoraでは、GNOME Softwareがはじめからインストールされています。

```
sudo apt install flatpak gnome-software-plugin-flatpak
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

### ソースコードからインストールする￹方法￺ほうほう￻

　「ふりがなパッド」をソースコードからインストールしたいときは、つぎの￹手順￺てじゅん￻でインストールできます。

```
git clone https://github.com/esrille/furiganapad.git
cd furiganapad/
meson setup --prefix /usr _build
ninja -C _build
sudo ninja -C _build install
```

　ビルドするときに￹必要￺ひつよう￻なパッケージについては、debian/controlのBuild-Depends、あるいは、ibus-hiragana.specのBuildRequiresを￹参考￺さんこう￻にしてください。
　Fedoraであれば、つぎのコマンドでビルドに￹必要￺ひつよう￻なパッケージをインストールできます。

```
sudo yum-builddep ibus-hiragana.spec
```

　Ubuntuであれば、つぎのコマンドでビルドに￹必要￺ひつよう￻なパッケージをインストールできます。
```
sudo apt build-dep .
```

　ソースコードからビルドした「ふりがなパッド」をアンインストールするには、つぎのようにします。

```
sudo ninja -C _build uninstall
```
