import "./Base.spec";

methods {
    function _.emitTransfer(address, address, uint256) external => NONDET;
    // dispatch and use MockFlashBorrow if more detailed implementation is required
    function _.onFlashLoan(address, address, uint256, uint256, bytes) external => NONDET;
}

// used to test running time
use builtin rule sanity;
use rule privilegedOperation;