
add_test(NAME pyterra COMMAND python3 -m unittest discover ${CMAKE_SOURCE_DIR}/pyterra/tests)
set_property(TEST pyterra
      APPEND PROPERTY ENVIRONMENT PYTHONPATH=${CMAKE_BINARY_DIR}/pyterra-build:${CMAKE_BINARY_DIR}/pyvxl-build:$ENV{PYTHONPATH}
      )
