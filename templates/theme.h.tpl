#ifndef THEME_{{THEME_NAME_UPPERCASE}}_H
#define THEME_{{THEME_NAME_UPPERCASE}}_H

#ifdef __cplusplus
extern "C" {
#endif

#include <lv_theme.h>

/**
 * Initialize the theme
 * @param disp pointer to display
 * @param font pointer to a font to use.
 * @return a pointer to reference this theme later
 */
lv_theme_t* lv_theme_{{THEME_NAME_LOWERCASE}}_init(
    lv_display_t* disp,
    const lv_font_t* font
);

#ifdef __cplusplus
extern "}"
#endif

#endif // THEME_{{THEME_NAME_UPPERCASE}}_H