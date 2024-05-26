import "./Base.spec";

methods {
    function _.isHookTarget() external => NONDET;

    function Base.initOperation(uint32 operation, address accountToCheck) internal returns (GovernanceHarness.VaultCache memory, address) with(env e) => CVLInitOperation(e, operation, accountToCheck);
}

function CVLInitOperation(env e, uint32 operation, address accountToCheck) returns (GovernanceHarness.VaultCache, address) {
    GovernanceHarness.VaultCache cache;
    address out;

    return (cache, out);
}

// used to test running time
use builtin rule sanity;