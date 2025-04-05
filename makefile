test: main.cpp
	clang++ main.cpp -o testing

run: test
	./testing