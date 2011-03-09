target=swipe
pyjunk=Swipe.pyc
prefix=/usr/local

all: swipe

swipe: swipe.c vector.c	
	$(CC) $(CFLAGS) -o $(target) swipe.c vector.c -lm -lc -lblas -llapack -lfftw3 -lsndfile

install: swipe
	install swipe $(prefix)/bin

clean: swipe
	rm $(target) $(pyjunk)
