import "./Base.spec";

methods {
    function _.isHookTarget() external => NONDET;
}

// used to test running time
use builtin rule sanity;
use rule privilegedOperation;