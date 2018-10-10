#include "pyhello.h"

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

namespace pyproj { namespace hello
{

  // template <typename T, typename Buff>
  // T type_from_buffer(py::array_t<Buff> b)
  // {
  //   py::buffer_info info = b.request();
  //   if(info.format != py::format_descriptor<Buff>::format()){
  //     throw std::runtime_error("Incompatible scalar type");
  //   }
  //   if(info.ndim != 1){
  //     throw std::runtime_error("Expecting a 1-dimensional vector");
  //   }
  //   if(info.shape[0] != 3){
  //     throw std::runtime_error("Expecting a 3-d input vector");
  //   }

  //   const Buff* data_ptr = static_cast<Buff*>(info.ptr);
  //   const size_t stride = info.strides[0] / sizeof(Buff);
  //   Buff x = *data_ptr;
  //   Buff y = *(data_ptr + stride);
  //   Buff z = *(data_ptr + 2*stride);

  //   return T(x,y,z);
  // }

  // template <typename B1, typename B2>
  // Plane createPlane(py::array_t<B1> pos, py::array_t<B2> normal){
  //   return Plane(type_from_buffer<Vec3f>(pos),
  //                type_from_buffer<Vec3f>(normal));
  // }

  void wrap_pfit(py::module &m)
  {

    // py::class_<Plane> (m, "Plane")
    //   .def(py::init<>())
    //   .def(py::init(&createPlane<float, float>))
    //   .def("normal", [](const Plane& p) -> py::tuple{
    //       const Vec3f& n = p.getNormal();
    //       return py::make_tuple(n[0], n[1], n[2]);})
    //   .def("position", [](const Plane& p) -> py::tuple{
    //       const Vec3f& pos = p.getPosition();
    //       return py::make_tuple(pos[0], pos[1], pos[2]);})
    //   .def("signedDistToOrigin", &Plane::SignedDistToOrigin);

  }
}}
