import "./Base.spec";
import "./GhostPow.spec";
import "./LoadVaultSummaries.spec";

/*
    Declaration of methods that are used in the rules. envfree indicate that
    the method is not dependent on the environment (msg.value, msg.sender).
    Methods that are not declared here are assumed to be dependent on env.
*/
methods {
    function name() external returns string envfree;
    function symbol() external returns string envfree;
    function decimals() external returns uint8 envfree;
    function asset() external returns address envfree;
    function approve(address,uint256) external returns bool;
    function deposit(uint256,address) external;
    function mint(uint256,address) external;
    function withdraw(uint256,address,address) external;
    function redeem(uint256,address,address) external;
    function permit(address,address,uint256,uint256,uint8,bytes32,bytes32) external;
    function DOMAIN_SEPARATOR() external returns bytes32;

    /// Summaries
    // summary for rpow
    function RPow.rpow(uint256 x, uint256 y, uint256 base) internal returns (uint256, bool) => CVLPow(x, y, base);

    // See comment near CVLgetCurrentOnBehalfOfAccount definition in LoadVaultSummaries spec.
    function _.getCurrentOnBehalfOfAccount(address controller) external => CVLgetCurrentOnBehalfOfAccount(controller) expect (address, bool);

    function storage_lastInterestAccumulatorUpdate() external returns (uint48) envfree;
    function storage_cash() external returns (VaultHarness.Assets) envfree;
    function storage_supplyCap() external returns (uint256) envfree;
    function storage_borrowCap() external returns (uint256) envfree;
    function storage_hookedOps() external returns (VaultHarness.Flags) envfree;
    function storage_snapshotInitialized() external returns (bool) envfree;
    function storage_totalShares() external returns (VaultHarness.Shares) envfree;
    function storage_totalBorrows() external returns (VaultHarness.Owed) envfree;
    function storage_accumulatedFees() external returns (VaultHarness.Shares) envfree;
    function storage_interestAccumulator() external returns (uint256) envfree;
    function storage_configFlags() external returns (VaultHarness.Flags) envfree;

}

// used to test running time
use builtin rule sanity;

// This is not in the scene for this config, so we just want it to be
// an uninterpreted function rather than NONDET so that
// we get the same value when this is called for different parts
ghost CVLgetCurrentOnBehalfOfAccountAddr(address) returns address;
ghost CVLgetCurrentOnBehalfOfAccountBool(address) returns bool;

function CVLgetCurrentOnBehalfOfAccount(address addr) returns (address, bool) {
    return (CVLgetCurrentOnBehalfOfAccountAddr(addr),
        CVLgetCurrentOnBehalfOfAccountBool(addr));
}

// Assumptions for LTVConfig
function LTVConfigAssumptions(env e, VaultHarness.LTVConfig ltvConfig) returns bool {
    bool LTVLessOne = ltvConfig.liquidationLTV < 10000;
    bool initialLTVLessOne = ltvConfig.initialLiquidationLTV < 10000;
    bool target_less_original = ltvConfig.liquidationLTV < ltvConfig.initialLiquidationLTV;
    mathint timeRemaining = ltvConfig.targetTimestamp - e.block.timestamp;
    return LTVLessOne &&
        initialLTVLessOne &&
        target_less_original && 
        require_uint32(timeRemaining) < ltvConfig.rampDuration;
}



////////////////////////////////////////////////////////////////////////////////
////           #  asset To shares mathematical properties                  /////
////////////////////////////////////////////////////////////////////////////////

rule conversionOfZero {
    env e;
    uint256 convertZeroShares = convertToAssets(e, 0);
    uint256 convertZeroAssets = convertToShares(e, 0);

    assert convertZeroShares == 0,
        "converting zero shares must return zero assets";
    assert convertZeroAssets == 0,
        "converting zero assets must return zero shares";
}


rule convertToAssetsWeakAdditivity() {
    env e;
    uint256 sharesA; uint256 sharesB;
    require sharesA + sharesB < max_uint128
         && convertToAssets(e, sharesA) + convertToAssets(e, sharesB) < to_mathint(max_uint256)
         && convertToAssets(e, require_uint256(sharesA + sharesB)) < max_uint256;
    assert convertToAssets(e, sharesA) + convertToAssets(e, sharesB) <= to_mathint(convertToAssets(e, require_uint256(sharesA + sharesB))),
        "converting sharesA and sharesB to assets then summing them must yield a smaller or equal result to summing them then converting";
}


rule convertToSharesWeakAdditivity() {
    env e;
    uint256 assetsA; uint256 assetsB;
    require assetsA + assetsB < max_uint128
         && convertToAssets(e, assetsA) + convertToAssets(e, assetsB) < to_mathint(max_uint256)
         && convertToAssets(e, require_uint256(assetsA + assetsB)) < max_uint256;
    assert convertToAssets(e, assetsA) + convertToAssets(e, assetsB) <= to_mathint(convertToAssets(e, require_uint256(assetsA + assetsB))),
        "converting assetsA and assetsB to shares then summing them must yield a smaller or equal result to summing them then converting";
}


rule conversionWeakMonotonicity {
    env e;
    uint256 smallerShares; uint256 largerShares;
    uint256 smallerAssets; uint256 largerAssets;

    assert smallerShares < largerShares => convertToAssets(e, smallerShares) <= convertToAssets(e, largerShares),
        "converting more shares must yield equal or greater assets";
    assert smallerAssets < largerAssets => convertToShares(e, smallerAssets) <= convertToShares(e, largerAssets),
        "converting more assets must yield equal or greater shares";
}


rule conversionWeakIntegrity() {
    env e;
    uint256 sharesOrAssets;
    assert convertToShares(e, convertToAssets(e, sharesOrAssets)) <= sharesOrAssets,
        "converting shares to assets then back to shares must return shares less than or equal to the original amount";
    assert convertToAssets(e, convertToShares(e, sharesOrAssets)) <= sharesOrAssets,
        "converting assets to shares then back to assets must return assets less than or equal to the original amount";
}


rule convertToCorrectness(uint256 amount, uint256 shares)
{
    env e;
    assert amount >= convertToAssets(e, convertToShares(e, amount));
    assert shares >= convertToShares(e, convertToAssets(e, shares));
}



////////////////////////////////////////////////////////////////////////////////
////                   #    Unit Test                                      /////
////////////////////////////////////////////////////////////////////////////////


rule zeroDepositZeroShares(uint assets, address receiver)
{
    env e;
    
    uint shares = deposit(e,assets, receiver);
    // In this Vault, max_uint256 as an argument will transfer all assets
    // to the vault . This precondition rules out the case where
    // the depositor calls deposit with a blance of 0 in the underlying
    // asset and gives max_uint256 as the shares.
    require assets < max_uint256;

    assert shares == 0 <=> assets == 0;
}



////////////////////////////////////////////////////////////////////////////////
////                    #    Valid State                                   /////
////////////////////////////////////////////////////////////////////////////////

invariant assetsMoreThanSupply(env e)
    totalAssets(e) >= totalSupply(e)
    {
        preserved {
            require e.msg.sender != currentContract;
            require actualCaller(e) != currentContract;
            require actualCallerCheckController(e) != currentContract;
            address any;
            safeAssumptions(e, any , actualCaller(e));
            safeAssumptions(e, any , actualCallerCheckController(e));
        }
    }


invariant noSupplyIfNoAssets(env e)
    noSupplyIfNoAssetsDef(e)     // see defition in "helpers and miscellaneous" section
    {
        preserved {
            safeAssumptions(e, _, e.msg.sender);
        }
    }


invariant noAssetsIfNoSupply(env e) 
    ( totalAssets(e) == 0 => ( totalSupply(e) == 0 ))

    {
        preserved {
            address any;
            safeAssumptions(e, any, actualCaller(e));
            safeAssumptions(e, any, actualCallerCheckController(e));
        }
    }


ghost mathint sumOfBalances {
    init_state axiom sumOfBalances == 0;
}

hook Sstore currentContract.vaultStorage.users[KEY address addy].data VaultHarness.PackedUserSlot newValue (VaultHarness.PackedUserSlot oldValue)  {
    sumOfBalances = sumOfBalances + newValue - oldValue;
}

hook Sload VaultHarness.PackedUserSlot val currentContract.vaultStorage.users[KEY address addy].data  {
    require sumOfBalances >= to_mathint(val);
}

invariant totalSupplyIsSumOfBalances(env e)
    to_mathint(totalSupply(e)) == sumOfBalances;



////////////////////////////////////////////////////////////////////////////////
////                    #     State Transition                             /////
////////////////////////////////////////////////////////////////////////////////

rule underlyingCannotChange() {
    address originalAsset = asset();

    method f; env e; calldataarg args;
    f(e, args);

    address newAsset = asset();

    assert originalAsset == newAsset,
        "the underlying asset of a contract must not change";
}



////////////////////////////////////////////////////////////////////////////////
////                    #   High Level                                    /////
////////////////////////////////////////////////////////////////////////////////

rule dustFavorsTheHouse(uint assetsIn )
{
    env e;
        
    require e.msg.sender != currentContract;
    safeAssumptions(e,e.msg.sender,e.msg.sender);
    uint256 totalSupplyBefore = totalSupply(e);

    // uint balanceBefore = ERC20a.balanceOf(e, currentContract);
    uint balanceBefore = currentContract.balanceOf(e, currentContract);

    uint shares = deposit(e,assetsIn, e.msg.sender);
    uint assetsOut = redeem(e,shares,e.msg.sender,e.msg.sender);

    // uint balanceAfter = ERC20a.balanceOf(e, currentContract);
    uint balanceAfter = currentContract.balanceOf(e, currentContract);
    assert balanceAfter >= balanceBefore;
}



////////////////////////////////////////////////////////////////////////////////
////                       #   Risk Analysis                           /////////
////////////////////////////////////////////////////////////////////////////////

invariant vaultSolvency(env e)
    totalAssets(e) >= totalSupply(e)  && userAssets(e, currentContract) >= require_uint256(cache_cash(e))  {
      preserved {
            requireInvariant totalSupplyIsSumOfBalances(e);
            require e.msg.sender != currentContract;
            require actualCaller(e) != currentContract;
            require actualCallerCheckController(e) != currentContract;
            require currentContract != asset(); 
        }
    }


rule redeemingAllValidity() { 
    env e;
    address owner; 
    uint256 shares; require shares == balanceOf(e, owner);
    
    safeAssumptions(e, _, owner);
    redeem(e, shares, _, owner);
    uint256 ownerBalanceAfter = balanceOf(e, owner);
    assert ownerBalanceAfter == 0;
}



////////////////////////////////////////////////////////////////////////////////
////               # stakeholder properties  (Risk Analysis )         //////////
////////////////////////////////////////////////////////////////////////////////

rule reclaimingProducesAssets(method f)
filtered {
    f -> f.selector == sig:withdraw(uint256,address,address).selector
      || f.selector == sig:redeem(uint256,address,address).selector
}
{
    env e; uint256 assets; uint256 shares;
    address receiver; address owner;
    require currentContract != e.msg.sender
         && currentContract != receiver
         && currentContract != owner;

    safeAssumptions(e, receiver, owner);

    uint256 ownerSharesBefore = balanceOf(e, owner);
    uint256 receiverAssetsBefore = userAssets(e, receiver);

    callReclaimingMethods(e, f, assets, shares, receiver, owner);

    uint256 ownerSharesAfter = balanceOf(e, owner);
    uint256 receiverAssetsAfter = userAssets(e, receiver);

    assert ownerSharesBefore > ownerSharesAfter <=> receiverAssetsBefore < receiverAssetsAfter,
        "an owner's shares must decrease if and only if the receiver's assets increase";
}



////////////////////////////////////////////////////////////////////////////////
////                        # helpers and miscellaneous                //////////
////////////////////////////////////////////////////////////////////////////////

definition noSupplyIfNoAssetsDef(env e) returns bool = 
    // for this ERC4626 implementation balanceOf(Vault) is not the same as total assets
    // ( userAssets(e, currentContract) == 0 => totalSupply(e) == 0 ) &&
    ( totalAssets(e) == 0 => ( totalSupply(e) == 0 ));


function safeAssumptions(env e, address receiver, address owner) {
    require currentContract != asset(); // Although this is not disallowed, we assume the contract's underlying asset is not the contract itself
    requireInvariant totalSupplyIsSumOfBalances(e);
    requireInvariant vaultSolvency(e);
    requireInvariant noAssetsIfNoSupply(e);
    requireInvariant noSupplyIfNoAssets(e);
    requireInvariant assetsMoreThanSupply(e); 

    require ( 
        (receiver != owner 
            =>  balanceOf(e, owner) + balanceOf(e, receiver) <= to_mathint(totalSupply(e)))
                && balanceOf(e, receiver) <= totalSupply(e)
                && balanceOf(e, owner) <= totalSupply(e));
}


// A helper function to set the receiver 
function callReceiverFunctions(method f, env e, address receiver) {
    uint256 amount;
    if (f.selector == sig:deposit(uint256,address).selector) {
        deposit(e, amount, receiver);
    } else if (f.selector == sig:mint(uint256,address).selector) {
        mint(e, amount, receiver);
    } else if (f.selector == sig:withdraw(uint256,address,address).selector) {
        address owner;
        withdraw(e, amount, receiver, owner);
    } else if (f.selector == sig:redeem(uint256,address,address).selector) {
        address owner;
        redeem(e, amount, receiver, owner);
    } else {
        calldataarg args;
        f(e, args);
    }
}


function callContributionMethods(env e, method f, uint256 assets, uint256 shares, address receiver) {
    if (f.selector == sig:deposit(uint256,address).selector) {
        deposit(e, assets, receiver);
    }
    if (f.selector == sig:mint(uint256,address).selector) {
        mint(e, shares, receiver);
    }
}


function callReclaimingMethods(env e, method f, uint256 assets, uint256 shares, address receiver, address owner) {
    if (f.selector == sig:withdraw(uint256,address,address).selector) {
        withdraw(e, assets, receiver, owner);
    }
    if (f.selector == sig:redeem(uint256,address,address).selector) {
        redeem(e, shares, receiver, owner);
    }
}


function callFunctionsWithReceiverAndOwner(env e, method f, uint256 assets, uint256 shares, address receiver, address owner) {
    if (f.selector == sig:withdraw(uint256,address,address).selector) {
        withdraw(e, assets, receiver, owner);
    }
    if (f.selector == sig:redeem(uint256,address,address).selector) {
        redeem(e, shares, receiver, owner);
    } 
    if (f.selector == sig:deposit(uint256,address).selector) {
        deposit(e, assets, receiver);
    }
    if (f.selector == sig:mint(uint256,address).selector) {
        mint(e, shares, receiver);
    }
     if (f.selector == sig:transferFrom(address,address,uint256).selector) {
        transferFrom(e, owner, receiver, shares);
    }
    else {
        calldataarg args;
        f(e, args);
    }
}