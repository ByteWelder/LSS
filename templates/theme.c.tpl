#define LV_USE_PRIVATE_API 1 // for _lv_theme_t

#include "theme.h"
#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

{{DEFINE_CONSTANTS}}

typedef theme_{{THEME_NAME_LOWER}}_styles theme_t;

typedef struct {
{{STYLE_DECLARATIONS}}
} theme_t;

static void style_init(theme_t* theme) {
{{STYLE_INIT}}
}

lv_theme_t* lv_theme_{{THEME_NAME_LOWER}}_init(
    lv_display_t* disp,
    const lv_font_t* font
) {
    {{INIT_FUNCTION_BODY}}
}

#ifdef __cplusplus
extern "}"
#endif
