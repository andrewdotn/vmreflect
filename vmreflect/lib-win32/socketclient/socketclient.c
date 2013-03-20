/* socketclient - a utility that connects to a tcp port, sends a string, and
 * prints the response */

#include <errno.h>
#include <libgen.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#if (__APPLE__ && __MACH__)
#include <netdb.h>
#include <sys/socket.h>
#include <sysexits.h>
#endif

static const char* program_name;

#ifdef _WIN32
#define WINVER 0x0501
#include <winsock2.h>
#include <ws2tcpip.h>
#define SHUT_WR SD_SEND

/* from sysexits.h */
#define EX_USAGE	64	/* command line usage error */
#define EX_NOHOST	68	/* host name unknown */
#define EX_UNAVAILABLE	69	/* service unavailable */
#define EX_SOFTWARE	70	/* internal software error */
#define EX_IOERR        74      /* input/output error */

#endif

/* API similar to err.h */

static void vmerrc(int eval, const char* msg, const char *fmt, va_list arg_list)
{
    fprintf(stderr, "%s", program_name);
    if (fmt != NULL) {
        fprintf(stderr, ": ");
        vfprintf(stderr, fmt, arg_list);
    }
    fprintf(stderr, ": %s\n", msg);
    exit(eval);
}

#ifdef _WIN32
static void err(int eval, const char *fmt, ...) {
    va_list arg_list;
    va_start(arg_list, fmt);
    vmerrc(eval, strerror(errno), fmt, arg_list);
}
#endif

/* Like err(), but uses Winsock’s WSAGetLastError() for the error code */
static void wserr(int eval, const char *fmt, ...) {
    va_list arg_list;
    va_start(arg_list, fmt);
#ifdef _WIN32
    int code = WSAGetLastError();
    LPTSTR out_buffer;
    int bytes_written = FormatMessage(
        FORMAT_MESSAGE_ALLOCATE_BUFFER
        | FORMAT_MESSAGE_FROM_SYSTEM,   /* flags */
        0,                              /* lpSource */
        code,                           /* dwMessageId */
        0,                              /* dwLanguageId */
        (LPTSTR)&out_buffer, 0, NULL);
    if (!bytes_written) {
        fprintf(stderr, "%s: ", program_name);
        vfprintf(stderr, fmt, arg_list);
        fprintf(stderr, "\n");
        err(EX_SOFTWARE, "FormatMessage(%d) failed with Windows error code %d",
            code, GetLastError());
    }
    vmerrc(eval, (char*)out_buffer, fmt, arg_list);
#else
    vmerrc(eval, strerror(errno), fmt, arg_list);
#endif
}

static void usage() {
    printf("usage: %s host port string\n", program_name);
    printf("\n");
    printf("Makes TCP connection to HOST:PORT, sends STRING,"
        " and prints response.\n\n");
    printf("example: %s localhost 80 $'GET /\\n\\n'\n", program_name);
    printf("         <html><body><h1>It works!</h1></body></html>\n");
    printf("\n");
    return;
}

int main(int argc, char** argv) {
    int error;

#ifdef _WIN32
    WSADATA wsaData;

    error = WSAStartup(MAKEWORD(2,2), &wsaData);
    if (error) {
        err(EX_UNAVAILABLE, "Unable to start Winsock");
    }
#endif

    program_name = basename(argv[0]);

    if (argc != 4) {
        usage();
        exit(EX_USAGE);
    }
    struct addrinfo *res, hints;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = PF_INET;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_protocol = IPPROTO_TCP;

    error = getaddrinfo(argv[1], argv[2], &hints, &res);
    if (error) {
        wserr(EX_NOHOST, "getaddrinfo(%s, %s) failed", argv[1], argv[2]);
    }

    int fd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (-1 == fd) {
        wserr(EX_UNAVAILABLE, "Unable to create socket");
    }

    error = connect(fd, res->ai_addr, res->ai_addrlen);
    if (error) {
        wserr(EX_UNAVAILABLE, "connect() failed");
    }

    char* msg = argv[3];
    int msglen = strlen(msg);

    int bytes_written = send(fd, msg, msglen, 0);
    if (bytes_written < 0) {
        wserr(EX_IOERR, "send() failed");
    } else if (bytes_written < msglen) {
        wserr(EX_IOERR, "send() only wrote %d of %d bytes",
            bytes_written, msglen);
    }

    /* Unfortunately, half-closing the socket crashes the tcpr server. */

    /*
    error = shutdown(fd, SHUT_WR);
    if (error) {
        wserr(EX_IOERR, "shutdown socket for writing failed");
    }
    */

    char buffer[1024];
    int bytes_read;
    while ((bytes_read = recv(fd, buffer, sizeof(buffer), 0)) > 0) {
        int i;
        for (i = 0 ; i < bytes_read; i++)
            putchar(buffer[i]);
    }
    if (bytes_read < 0) {
        wserr(EX_IOERR, "recv() failed");
    }

    return 0;
}
