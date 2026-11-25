# archunit-cpp

## Check interface-only directories

The `assert_interfaces` pytest fixture checks class definitions from headers in a directory. The supplied source file must include the headers being checked and have a compile command in the build directory:

```python
def test_contracts_are_interfaces(assert_interfaces, build_directory, source_file):
    assert_interfaces(build_directory, source_file, "include/project/contracts")
```

Each class must declare at least one pure virtual method. A bodyless virtual destructor declaration is allowed. Other methods must be pure virtual, and method definitions or data members fail the assertion. The check includes out-of-line method definitions found in the parsed translation unit.
