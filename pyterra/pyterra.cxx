#include <pybind11/pybind11.h>

#include "pyhello.h"

namespace py = pybind11;

// helper function to check if py::module import exists
bool import_exists(std::string const& library_name)
{
  py::module importlib = py::module::import("importlib");
  return (!importlib.attr("find_loader")(library_name.c_str()).is_none());
}


PYBIND11_MODULE(_terra, m)
{
  m.doc() =  "Python bindings for Terra";

  py::module mod = m.def_submodule("hello");
  pyterra::hello::wrap_hello(mod);

  if (import_exists("vxl"))
    py::module::import("vxl");
}
