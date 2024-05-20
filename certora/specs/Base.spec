import "./Benchmarking.spec";

using DummyERC20A as ERC20a;
using DummyERC20B as ERC20b; 
using EthereumVaultConnector as evc;

methods {
    // envfree
    function getCollateralsExt(address account) external returns (address[] memory) envfree;
    function isCollateralEnabledExt(address account, address market) external returns (bool) envfree;
    function vaultIsOnlyController(address account) external returns (bool) envfree;
    function isAccountStatusCheckDeferredExt(address account) external returns (bool) envfree;
    function vaultIsController(address account) external returns (bool) envfree;

    // IPriceOracle
    function _.getQuote(uint256 amount, address base, address quote) external => CVLGetQuote(amount, base, quote) expect (uint256);
    function _.getQuotes(uint256 amount, address base, address quote) external => CVLGetQuotes(amount, base, quote) expect (uint256, uint256);

    // ProxyUtils    
    function ProxyUtils.metadata() internal returns (address, address, address)=> CVLProxyMetadata();

    /// Unresolved calls
    // These are unresolved calls that havoc contract state.
    // Most of these cause these havocs because of a low-level call 
    // operation and are irrelevant for the rules.
    function _.invokeHookTarget(address caller) internal => NONDET;
    // another unresolved call that havocs all contracts
    function _.requireVaultStatusCheck() external => NONDET;
    function _.requireAccountAndVaultStatusCheck(address account) external => NONDET;
    // trySafeTransferFrom cannot be summarized as NONDET (due to return type
    // that includes bytes memory). So it is summarized as 
    // DummyERC20a.transferFrom
    function _.trySafeTransferFrom(address token, address from, address to, uint256 value) internal with (env e) => CVLTrySafeTransferFrom(e, from, to, value) expect (bool, bytes memory);
    // safeTransferFrom is summarized as transferFrom
    // from DummyERC20a to avoid dealing with the low-level `call`
    function _.safeTransferFrom(address token, address from, address to, uint256 value, address permit2) internal with (env e)=> CVLTrySafeTransferFrom(e, from, to, value) expect (bool, bytes memory);
    function _.tryBalanceTrackerHook(address account, uint256 newAccountBalance, bool forfeitRecentReward) internal => NONDET;
    function _.balanceTrackerHook(address account, uint256 newAccountBalance, bool forfeitRecentReward) external => NONDET;
}

ghost CVLGetQuote(uint256, address, address) returns uint256 {
    // The total value returned by the oracle is assumed < 2**230-1.
    // There will be overflows without an upper bound on this number.
    // (For example, it must be less than 2**242-1 to avoid overflow in
    // LTVConfig.mul)
    axiom forall uint256 x. forall address y. forall address z. 
        CVLGetQuote(x, y, z) < 1725436586697640946858688965569256363112777243042596638790631055949823;
}

function CVLGetQuotes(uint256 amount, address base, address quote) returns (uint256, uint256) {
    return (
        CVLGetQuote(amount, base, quote),
        CVLGetQuote(amount, base, quote)
    );
}

ghost address oracleAddress;
ghost address unitOfAccount;
function CVLProxyMetadata() returns (address, address, address) {
    return (ERC20a, oracleAddress, unitOfAccount);
}

function actualCaller(env e) returns address {
    if(e.msg.sender == evc) {
        address onBehalf;
        bool unused;
        onBehalf, unused = evc.getCurrentOnBehalfOfAccount(e, 0);
        return onBehalf;
    } else {
        return e.msg.sender;
    }
}

function actualCallerCheckController(env e) returns address {
    if(e.msg.sender == evc) {
        address onBehalf;
        bool unused;
        // Similar to EVCAuthenticateDeferred when checkController is true.
        onBehalf, unused = evc.getCurrentOnBehalfOfAccount(e, currentContract);
        return onBehalf;
    } else {
        return e.msg.sender;
    }
}

// Summarize trySafeTransferFrom as DummyERC20 transferFrom
function CVLTrySafeTransferFrom(env e, address from, address to, uint256 value) returns (bool, bytes) {
    bytes ret; // Ideally bytes("") if there is a way to do this
    return (ERC20a.transferFrom(e, from, to, value), ret);
}