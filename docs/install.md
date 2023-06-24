# インストール￹方法￺ほうほう￻

　つかっているOSがFedoraかUbuntuであれば、かんたんに「ふりがなパッド」をインストールすることができます。

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
sudo apt update
```

　あとは、aptコマンドで「ふりがなパッド」をインストールできます。

```
sudo apt install furiganapad
```

### ソースコードからインストールする￹方法￺ほうほう￻

　「ふりがなパッド」をソースコードからインストールしたいときは、つぎの￹手順￺てじゅん￻でインストールできます。

```
git clone https://github.com/esrille/furiganapad.git
./autogen.sh --prefix=/usr
make
sudo make install
```

　ソースコードからビルドした「ふりがなパッド」をアンインストールするには、つぎのようにします:

```
$ sudo make uninstall
```
