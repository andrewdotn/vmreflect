CFLAGS = -W -Wall -Wextra

-include Makefile.local

all: socketclient socketclient.exe

# get your cross-compiler here:
# http://crossgcc.rts-software.org/doku.php#compiling_for_win32_on_mac_os_x

%.exe: %.c
	i386-mingw32-gcc $< $(CFLAGS) -o $@ -lws2_32
	i386-mingw32-strip -s -v $@

clean::
	rm -f socketclient.exe socketclient
