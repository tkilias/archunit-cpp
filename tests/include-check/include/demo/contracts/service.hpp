#pragma once

namespace demo::contracts {
class Service {
public:
    virtual ~Service();
    virtual int run() const = 0;
};
}
