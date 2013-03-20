CFLAGS = -W -Wall -Wextra

-include Makefile.local

.DELETE_ON_ERROR:
.SECONDARY:

all: socketclient socketclient.exe

# get your cross-compiler here:
# http://crossgcc.rts-software.org/doku.php#compiling_for_win32_on_mac_os_x

%.exe: %.c
	i386-mingw32-gcc $< $(CFLAGS) -o $@ -lws2_32
	i386-mingw32-strip -s -v $@
	./zero_pefile_timedatestamp.py $@

clean::
	rm -f socketclient.exe socketclient
