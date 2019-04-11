cmake_minimum_required(VERSION 3.0)
project("Terra")

# Pybind 11 for pyvxl
set(BUILD_PYBIND ON)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_POSITION_INDEPENDENT_CODE on)

# Set some defaults that should be set by a super project. Great for debugging
set(TERRA_EXTERNAL_DIR ${CMAKE_SOURCE_DIR}/external)
set(TERRA_TOP_LEVEL_DIR ${CMAKE_SOURCE_DIR})

# Some defaults for the external dirs to be added
set(PYVXL_CONTRIB_MAKE_ALL TRUE CACHE BOOL "Default pyvxl build all")
set(VXL_BUILD_CONTRIB TRUE CACHE BOOL "Default build contrib")
set(VXL_BUILD_BRL TRUE CACHE BOOL "Default build BRL")
# Neede for bpgl
set(VXL_BUILD_CORE_VIDEO TRUE CACHE BOOL "Default build core video")
# Ease of debugging compile errors
set(CMAKE_CXX_FLAGS -fdiagnostics-color=always CACHE STRING "Color flags")
set(CMAKE_C_FLAGS -fdiagnostics-color=always CACHE STRING "Color flags")

# Include the base directory, so include files can be found, like "hello/hi.h"
include_directories(${CMAKE_SOURCE_DIR})

# This must come before add_subdir for vxl, or else ctest doesn't work right
include(CTest)

### basic dependencies

find_package(OpenMP)
if (OpenMP_FOUND)
  message("${PROJECT_NAME} FIND OpenMP")
  string(APPEND CMAKE_C_FLAGS " ${OpenMP_C_FLAGS}")
  string(APPEND CMAKE_CXX_FLAGS " ${OpenMP_CXX_FLAGS}")
else()
  message("${PROJECT_NAME} OpenMP not found.")
endif()

### VXL
set(VXL_SOURCE_DIR ${TERRA_EXTERNAL_DIR}/vxl)
set(VXL_BINARY_DIR ${CMAKE_BINARY_DIR}/vxl-build)

set(BUILD_CONTRIB "TRUE" CACHE BOOL "BUILD CONTRIB")
set(BUILD_BRL "TRUE" CACHE BOOL "BUILD BRL")

add_subdirectory(${VXL_SOURCE_DIR} ${VXL_BINARY_DIR} EXCLUDE_FROM_ALL)

include_directories(${VXL_SOURCE_DIR})
include_directories(${VXL_SOURCE_DIR}/core)
include_directories(${VXL_SOURCE_DIR}/vcl)
include_directories(${VXL_SOURCE_DIR}/contrib/brl)
include_directories(${VXL_SOURCE_DIR}/contrib/brl/bseg)
include_directories(${VXL_SOURCE_DIR}/contrib/brl/bbas)
include_directories(${VXL_SOURCE_DIR}/contrib/gel)
include_directories(${VXL_BINARY_DIR}/core)
include_directories(${VXL_BINARY_DIR}/vcl)
include_directories(${VXL_BINARY_DIR}/contrib)

### pybind11, pyvxl, py project
if(BUILD_PYBIND)
  set(PYBIND11_DIR "${TERRA_EXTERNAL_DIR}/pybind11" CACHE PATH "Location of Pybind11 source directory")
  find_package(PythonLibs 3 REQUIRED)
  add_subdirectory(${PYBIND11_DIR} ${CMAKE_BINARY_DIR}/pybind11-build)
  add_subdirectory(${TERRA_EXTERNAL_DIR}/pyvxl ${CMAKE_BINARY_DIR}/pyvxl-build)
  # Optional, project specific python bindings
  add_subdirectory(${TERRA_TOP_LEVEL_DIR}/pyterra ${CMAKE_BINARY_DIR}/pyterra-build)
endif(BUILD_PYBIND)

### Project directories

# Hello
add_subdirectory(${TERRA_TOP_LEVEL_DIR}/hello ${CMAKE_BINARY_DIR}/hello-build)
include_directories(${TERRA_TOP_LEVEL_DIR}/hello)

# Optionally exclude VXL tests
configure_file(${CMAKE_SOURCE_DIR}/CTestCustom.cmake ${CMAKE_BINARY_DIR})
execute_process(COMMAND sh -c "echo 'set(CTEST_CUSTOM_TESTS_IGNORE'; find '${CMAKE_SOURCE_DIR}/external/vxl' -path '*tests/CMakeLists.txt' -exec sed -nE '/add_test.*NAME/{s|.*NAME *([^ ]+).*|\\1|; p}' {} +; echo ')'"
                OUTPUT_FILE ${CMAKE_BINARY_DIR}/CTestCustom2.cmake)
