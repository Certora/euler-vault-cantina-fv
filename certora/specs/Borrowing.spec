import "./Base.spec";

methods {
    // dispatch and use MockFlashBorrow if more detailed implementation is required
    function _.onFlashLoan(bytes) external => NONDET;
}

// used to test running time
use builtin rule sanity;