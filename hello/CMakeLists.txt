project("hello")

set(HELLO_SOURCES
  hi.cxx  hi.h
)

add_library(hello ${HELLO_SOURCES})
# target_link_libraries(hello vnl)

enable_testing()

add_subdirectory(tests)
