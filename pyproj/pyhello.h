#ifndef pyhello_h_included_
#define pyhello_h_included_

#include <pybind11/pybind11.h>

namespace pyproj { namespace hello
{

void wrap_hello(pybind11::module &m);

}}

#endif
