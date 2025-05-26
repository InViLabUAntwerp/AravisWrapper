#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyMethodDef methods[] = {
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "_platform_tag",
    NULL,
    -1,
    methods
};

PyMODINIT_FUNC PyInit__platform_tag(void) {
    return PyModule_Create(&module);
}
