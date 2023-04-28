setup:
	pip3 install -r requirements.txt

build:
	pyinstaller --onefile app.py

clean:
	rm -f -r build
	rm -f -r dist
	rm -f app.spec

run:
	./dist/app