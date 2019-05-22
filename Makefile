all : README.md data/furiganapad.json

src = \
esrille_furiganapad/application.py \
esrille_furiganapad/__init__.py \
esrille_furiganapad/textbuffer.py \
esrille_furiganapad/textview.py \
esrille_furiganapad/window.py

README.md : README.txt
	./convert_to_tag.py README.txt README.md

data/furiganapad.json : $(src)
	./gettext.py $^ -o $@

clean :
	rm -rf __pycache__ esrille_furiganapad/__pycache__

.PHONY: all clean
