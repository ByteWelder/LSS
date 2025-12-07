#define LV_USE_PRIVATE_API 1 // for _lv_theme_t

#include "theme.h"
#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

{{DEFINES}}

typedef struct {
{{STYLE_DECLARATIONS}}
} theme_{{THEME_NAME_LOWERCASE}}_styles;

lv_theme_t* lv_theme_{{THEME_NAME_LOWERCASE}}_init(
    lv_display_t* disp,
    const lv_font_t* font
) {
    {{INIT_FUNCTION_BODY}}
}

#ifdef __cplusplus
extern "}"
#endif
