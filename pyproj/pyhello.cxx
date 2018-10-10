#include "pyhello.h"

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include <hello/hi.hxx>

namespace py = pybind11;

namespace pyproj { namespace hello
{
  void wrap_hello(py::module &m)
  {
    m.doc() = "This is a python docstring, seen when you run help(module)";

    m.def("foo", &foo, "A Foo Function that returns 1")
     .def("dummy_2_to_3", &dummy_2_to_3<double>);
  }
}}
