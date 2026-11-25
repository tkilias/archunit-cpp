#include <demo/api.hpp>
#include <demo/contracts/service.hpp>
#include <demo/implementations/bad_service.hpp>

int main() {
    return demo::answer() == 42 ? 0 : 1;
}
