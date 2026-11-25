#pragma once

namespace demo::implementations {
class BadService {
public:
    virtual int run() const = 0;
    int helper() const;
    int state;
};

inline int BadService::helper() const {
    return 1;
}

class ConcreteService {
public:
    int run() const;
};
}
