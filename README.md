This is a template of how to get started with vxl, pyvxl, and your own pybind11 package

## Getting started

```
source 'setup.env'
just setup
just run vxl
```
## Configuring the template

1. Edit `./CMakeFiles.txt` and change `project` to your project name, and rename `PROJ_` variables to your own `PREFIX_`
1. Rename `hello` to what you want to call it and replace with your own files. (I will reference the new name as `{hello}`, but substitute the actual name when following these instructions)
  1. Update  `./CMakeFiles.txt` and find the `add_subdirectory` line for `hello` and change to `{hello}`
  1. Update `./{hello}/CMakeFiles.txt` to reflect your new files
  1. Update `./{hello}/tests/CMakeFiles.txt` to reflect your new names
1. Rename `./pyproj` to your name (`{pyproj}` refers to the new name)
  1. Update  `./CMakeFiles.txt` and find the `add_subdirectory` line for `pyproj` and change to `{pyproj}`
  1. Rename `./{pyproj}/{pyhello}.*` files
  1. Update `pyproj` and `pyhello` names in `{pyproj}/CMakeList.txt`
  1. Update `pyproj` and `pyhello` names in `{pyproj}/tests/CMakeList.txt`
  1. Update `proj` in `PYBIND11_MODULE` line of `{pyproj}/{pyproj.cxx}`

Clean and rebuild