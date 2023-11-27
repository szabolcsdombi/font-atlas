#include <Python.h>

#define STB_RECT_PACK_IMPLEMENTATION
#define STBRP_STATIC
#include "stb_rect_pack.h"

#define STB_TRUETYPE_IMPLEMENTATION
#define STBTT_STATIC
#include "stb_truetype.h"

struct ModuleState {
};

static PyObject * meth_load_font(PyObject * self, PyObject * args, PyObject * kwargs) {
    const char * keywords[] = {"size", "fonts", "font_sizes", "code_points", "oversampling", "padding", NULL};

    int width, height;
    PyObject * fonts_lst;
    PyObject * font_sizes_lst;
    PyObject * code_points_lst;
    int oversampling = 1;
    int padding = 1;

    int args_ok = PyArg_ParseTupleAndKeywords(
        args, kwargs, "(ii)OOO|ii", (char **)keywords,
        &width,
        &height,
        &fonts_lst,
        &font_sizes_lst,
        &code_points_lst,
        &oversampling,
        &padding
    );

    if (!args_ok) {
        return NULL;
    }

    if (!PyList_Check(fonts_lst) || !PyList_Check(code_points_lst) || !PyList_Check(font_sizes_lst)) {
        return NULL;
    }

    int num_fonts = (int)PyList_Size(fonts_lst);
    int num_glyphs = (int)PyList_Size(code_points_lst);
    int num_sizes = (int)PyList_Size(font_sizes_lst);

    int * glyphs = (int *)malloc(num_glyphs * 4);
    for (int i = 0; i < num_glyphs; ++i) {
        glyphs[i] = PyLong_AsLong(PyList_GetItem(code_points_lst, i));
    }

    float * sizes = (float *)malloc(num_sizes * 4);
    for (int i = 0; i < num_sizes; ++i) {
        sizes[i] = (float)PyFloat_AsDouble(PyList_GetItem(font_sizes_lst, i));
    }

    PyObject * pixels = PyBytes_FromStringAndSize(NULL, width * height * 4);
    PyObject * rects = PyBytes_FromStringAndSize(NULL, sizeof(stbtt_packedchar) * num_fonts * num_glyphs * num_sizes);

    stbtt_pack_context pc;
    stbtt_packedchar * cd = (stbtt_packedchar *)PyBytes_AsString(rects);
    unsigned char * atlas = (unsigned char *)PyBytes_AsString(pixels);
    stbtt_pack_range * ranges = (stbtt_pack_range *)malloc(sizeof(stbtt_pack_range) * num_sizes);

    stbtt_PackBegin(&pc, atlas, width, height, 0, padding, NULL);
    for (int i = 0; i < num_fonts; ++i) {
        unsigned char * font_data = (unsigned char *)PyBytes_AsString(PyList_GetItem(fonts_lst, i));
        stbtt_PackSetOversampling(&pc, oversampling, oversampling);
        for (int j = 0; j < num_sizes; ++j) {
            ranges[j] = {sizes[j], 0, glyphs, num_glyphs, cd + num_glyphs * (num_sizes * i + j)};
        };
        stbtt_PackFontRanges(&pc, font_data, 0, ranges, num_sizes);
    }
    stbtt_PackEnd(&pc);
    free(glyphs);
    free(sizes);
    free(ranges);

    int x = width * height;
    int y = x * 4;
    while (x--) {
        atlas[--y] = atlas[x];
        atlas[--y] = atlas[x];
        atlas[--y] = atlas[x];
        atlas[--y] = atlas[x];
    }

    return Py_BuildValue("(NN)", pixels, rects);
}

static int module_exec(PyObject * self) {
    ModuleState * state = (ModuleState *)PyModule_GetState(self);
    PyModule_AddObject(self, "__version__", PyUnicode_FromString("1.0.0"));
    return 0;
}

static PyMethodDef module_methods[] = {
    {"load_font", (PyCFunction)meth_load_font, METH_VARARGS | METH_KEYWORDS},
    {0},
};

static PyModuleDef_Slot module_slots[] = {
    {Py_mod_exec, (void *)module_exec},
    {0},
};

static PyModuleDef module_def = {
    PyModuleDef_HEAD_INIT, "font_atlas", NULL, sizeof(ModuleState), module_methods, module_slots, NULL, NULL, NULL,
};

extern PyObject * PyInit_font_atlas() {
    return PyModuleDef_Init(&module_def);
}
