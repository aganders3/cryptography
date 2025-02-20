# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.


INCLUDES = """
#include <openssl/crypto.h>
"""

TYPES = """
static const long Cryptography_HAS_MEM_FUNCTIONS;
static const long Cryptography_HAS_OPENSSL_CLEANUP;

static const int SSLEAY_VERSION;
static const int SSLEAY_CFLAGS;
static const int SSLEAY_PLATFORM;
static const int SSLEAY_DIR;
static const int SSLEAY_BUILT_ON;
static const int OPENSSL_VERSION;
static const int OPENSSL_CFLAGS;
static const int OPENSSL_BUILT_ON;
static const int OPENSSL_PLATFORM;
static const int OPENSSL_DIR;
"""

FUNCTIONS = """
void OPENSSL_cleanup(void);

/* SSLeay was removed in 1.1.0 */
unsigned long SSLeay(void);
const char *SSLeay_version(int);
/* these functions were added to replace the SSLeay functions in 1.1.0 */
unsigned long OpenSSL_version_num(void);
const char *OpenSSL_version(int);

/* this is a macro in 1.1.0 */
void *OPENSSL_malloc(size_t);
void OPENSSL_free(void *);


/* Signature changed significantly in 1.1.0, only expose there for sanity */
int Cryptography_CRYPTO_set_mem_functions(
    void *(*)(size_t, const char *, int),
    void *(*)(void *, size_t, const char *, int),
    void (*)(void *, const char *, int));

void *Cryptography_malloc_wrapper(size_t, const char *, int);
void *Cryptography_realloc_wrapper(void *, size_t, const char *, int);
void Cryptography_free_wrapper(void *, const char *, int);
"""

CUSTOMIZATIONS = """
/* In 1.1.0 SSLeay has finally been retired. We bidirectionally define the
   values so you can use either one. This is so we can use the new function
   names no matter what OpenSSL we're running on, but users on older pyOpenSSL
   releases won't see issues if they're running OpenSSL 1.1.0 */
#if !defined(SSLEAY_VERSION)
# define SSLeay                  OpenSSL_version_num
# define SSLeay_version          OpenSSL_version
# define SSLEAY_VERSION_NUMBER   OPENSSL_VERSION_NUMBER
# define SSLEAY_VERSION          OPENSSL_VERSION
# define SSLEAY_CFLAGS           OPENSSL_CFLAGS
# define SSLEAY_BUILT_ON         OPENSSL_BUILT_ON
# define SSLEAY_PLATFORM         OPENSSL_PLATFORM
# define SSLEAY_DIR              OPENSSL_DIR
#endif
#if !defined(OPENSSL_VERSION)
# define OpenSSL_version_num     SSLeay
# define OpenSSL_version         SSLeay_version
# define OPENSSL_VERSION         SSLEAY_VERSION
# define OPENSSL_CFLAGS          SSLEAY_CFLAGS
# define OPENSSL_BUILT_ON        SSLEAY_BUILT_ON
# define OPENSSL_PLATFORM        SSLEAY_PLATFORM
# define OPENSSL_DIR             SSLEAY_DIR
#endif

#if CRYPTOGRAPHY_IS_LIBRESSL
static const long Cryptography_HAS_OPENSSL_CLEANUP = 0;
void (*OPENSSL_cleanup)(void) = NULL;
#else
static const long Cryptography_HAS_OPENSSL_CLEANUP = 1;
#endif

#if CRYPTOGRAPHY_IS_LIBRESSL || CRYPTOGRAPHY_IS_BORINGSSL
static const long Cryptography_HAS_MEM_FUNCTIONS = 0;
int (*Cryptography_CRYPTO_set_mem_functions)(
    void *(*)(size_t, const char *, int),
    void *(*)(void *, size_t, const char *, int),
    void (*)(void *, const char *, int)) = NULL;

#else
static const long Cryptography_HAS_MEM_FUNCTIONS = 1;

int Cryptography_CRYPTO_set_mem_functions(
    void *(*m)(size_t, const char *, int),
    void *(*r)(void *, size_t, const char *, int),
    void (*f)(void *, const char *, int)
) {
    return CRYPTO_set_mem_functions(m, r, f);
}
#endif

void *Cryptography_malloc_wrapper(size_t size, const char *path, int line) {
    return malloc(size);
}

void *Cryptography_realloc_wrapper(void *ptr, size_t size, const char *path,
                                   int line) {
    return realloc(ptr, size);
}

void Cryptography_free_wrapper(void *ptr, const char *path, int line) {
    free(ptr);
}
"""
