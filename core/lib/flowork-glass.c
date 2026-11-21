/*
 * =============================================================================
 * ⚡ Flowork Sovereign OS — Pure Optical Crystal Glass GDK Visual Interceptor
 * Canonical Path: /opt/floworkos/lib/libflowork-glass.so
 *
 * Ensures all GDK3/GTK3 application windows automatically inherit a 32-bit
 * ARGB visual (Depth 32) instead of legacy 24-bit TrueColor, allowing true
 * optical glass transparency without black/charcoal buffer collapse.
 *
 * Zero external library dependencies (links only against libc/libdl).
 * =============================================================================
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <stddef.h>

typedef void GdkScreen;
typedef void GdkVisual;

GdkVisual *gdk_screen_get_system_visual(GdkScreen *screen) {
    static GdkVisual *(*orig_get_sys)(GdkScreen *) = NULL;
    static GdkVisual *(*orig_get_rgba)(GdkScreen *) = NULL;
    static GdkScreen *(*orig_get_default_screen)(void) = NULL;
    static int initialized = 0;

    if (!initialized) {
        orig_get_sys = (GdkVisual *(*)(GdkScreen *))dlsym(RTLD_NEXT, "gdk_screen_get_system_visual");
        orig_get_rgba = (GdkVisual *(*)(GdkScreen *))dlsym(RTLD_DEFAULT, "gdk_screen_get_rgba_visual");
        orig_get_default_screen = (GdkScreen *(*)(void))dlsym(RTLD_DEFAULT, "gdk_screen_get_default");
        initialized = 1;
    }

    if (!screen && orig_get_default_screen) {
        screen = orig_get_default_screen();
    }

    if (screen && orig_get_rgba) {
        GdkVisual *rgba = orig_get_rgba(screen);
        if (rgba) {
            return rgba;
        }
    }

    return orig_get_sys ? orig_get_sys(screen) : NULL;
}
