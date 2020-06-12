# インストール￹方法￺ほうほう￻

　つかっているOSが、Fedora, Ubuntu, Raspberry Pi OSのどれかであれば、インストール￹用￺よう￻のソフトウェア パッケージを「[Releases](https://github.com/esrille/furiganapad/releases)」ページからダウンロードできます。

## じぶんでビルドする￹方法￺ほうほう￻

　「ふりがなパッド」をじぶんでビルドしてインストールしたいときは、つぎの￹手順￺てじゅん￻でインストールできます。

```
git clone https://github.com/esrille/furiganapad.git
./autogen.sh
make
sudo make install
```

　じぶんでビルドした「ふりがなパッド」をアンインストールするときは、つぎのようにします:
```
$ sudo make uninstall
```
　じぶんでソースコードを￹改造￺かいぞう￻して￹実験￺じっけん￻したいときもあるかもしれません。そういうときは、「ふりがなパッド」をインストールしないで、ソースコードをちょくせつ￹実行￺じっこう￻することもできます。
```
$ src/furiganapad
```
