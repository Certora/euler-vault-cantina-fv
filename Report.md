## Best rules catching mutants

### Mutant: Vault_1

* mutation: switch sender and owner
* note: remove from other without allowance < from basic erc20 properties>

**author:** alexzoid-eth
```
// COM-24 | Allowance decrease (unless equal to max_uint256) when user redeem from another account
rule allowanceChangedFromAnotherWithdraw(env e, method f, calldataarg args, address from)
    filtered { f -> !HARNESS_VIEW_METHODS(f) } {

    mathint fromBalancePrev = ghostUsersDataBalance[from];
    mathint usersETokenAllowancePrev = ghostUsersETokenAllowance[from][ghostOnBehalfOfAccount]; 

    f(e, args);

    mathint fromBalancePost = ghostUsersDataBalance[from];
    mathint usersETokenAllowancePost = ghostUsersETokenAllowance[from][ghostOnBehalfOfAccount]; 

    // Redeem shares to another account MUST decrease allowance, unless allowance is max_uint256
    assert(fromBalancePrev > fromBalancePost && from != ghostOnBehalfOfAccount
        => (usersETokenAllowancePrev == max_uint256
            ? usersETokenAllowancePrev == usersETokenAllowancePost
            : usersETokenAllowancePrev - usersETokenAllowancePost == fromBalancePrev - fromBalancePost
        )
    );
}
```

**author:** jraynaldi3

```
/// @notice approval Should decrease if caller and reduced balance owner is different
rule approval_shouldDecreaseAtBalanceDecrease(
    env e,
    method f,
    calldataarg args,
    address owner
) filtered {f -> !f.isView} {
    address caller = actualCaller(e);

    mathint allowanceBefore = allowance(e, owner, caller);
    mathint balanceBefore = balanceOf(e, owner);

    f(e,args);

    mathint allowanceAfter = allowance(e, owner, caller);
    mathint balanceAfter = balanceOf(e, owner);

    assert balanceAfter < balanceBefore 
        && allowanceBefore != max_uint256
        && owner != caller 
        => allowanceAfter < allowanceBefore;
}
```

```
/// @notice only owner and address with approval can decrease balance
rule decreaseBalance_onlyOwnerAndApproved(
    env e,
    method f,
    calldataarg args,
    address account
) filtered {f -> !f.isView} {
    address caller = actualCaller(e);
    mathint balanceBefore = balanceOf(e, account);
    uint256 allowance = allowance(e, account, caller);

    f(e,args);

    mathint balanceAfter = balanceOf(e, account);
    assert balanceBefore > balanceAfter => caller == account || allowance != 0;
}
```

### Mutant: BalanceUtils_1

* mutation: `==` => `!=`
* note: user can set allowance (satisfy rule or non revert)

**author:** jraynaldi3

```
/// @notice approval can only decreased by owner or the approved account
/// max uint256 approval cannot be decreased by spender
rule approval_onlyOwnerAndApprovedCanDecrease(
    env e,
    method f,
    calldataarg args,
    address owner,
    address spender
) filtered {f -> !f.isView} {
    address caller = actualCaller(e);

    mathint allowanceBefore = allowance(e, owner, spender);

    f(e,args);

    mathint allowanceAfter = allowance(e, owner, spender);

    assert allowanceAfter < allowanceBefore => owner == caller || spender == caller;
    assert allowanceBefore == max_uint256 && spender == caller => allowanceAfter == allowanceBefore;
}
```

### Mutant: RiskManager_0

* mutation: remove `!`
* note: state change of controller , lock the funds < a bit hard>

**author:** BlockianComp

```
/**
 * If a user has a borrow in a certain vault, they can't disable that vault from being their controller, otherwise can escape status check and steal funds.
 */
rule cantDisableControllerIfOwed(method f, address account) filtered { f-> !f.isView } {
    require(validateControllerExt(account));
    require(getUserOwedStorage(account) != 0);

    env e;
    calldataarg args;

    f(e, args);

    assert(validateControllerExt(account));
}
```

**author:** 0x00ffDa

```
invariant debtImpliesController(env e, address user)  
    debtOf(e, user) > 0 => vaultIsController(user)
    filtered {
        f -> SKIP_RM_METHODS_FILTER(f)
    }
    {
        preserved {
            preventDivByZero = true;            // see ghost def comment
            require storage_userInterestAccumulator(user) <= storage_interestAccumulator();
        }
    }
```


### Mutant: RiskManager_1

* note: go over the max, invariant 
* mutation: replace `>` with `==`

**author:** jraynaldi3

```
/// @notice checkVaultStatus should return magicValue if totalSupply lesser than supplyCap
rule checkVaultStatus_supplyLTECap(
    env e
) {
    TypesHarness.Snapshot snapshot = storage_snapshot();
    mathint snapshotCash = snapshot.cash;
    mathint snapshotBorrows = snapshot.borrows;

    mathint prevSupply = snapshotCash + snapshotBorrows;
    
    TypesHarness.VaultCache cache = getVaultCache(e);

    mathint supply = totalAssetsExternal(cache);

    bytes4 magicValue = to_bytes4(0);
    magicValue = checkVaultStatus(e);

    assert  (cache.snapshotInitialized 
        => supply <= to_mathint(cache.supplyCap) 
        || supply <= prevSupply ) 
        <=> magicValue == to_bytes4(0x4b3d1223);
}
```


### Mutant: Liquidation_0

* mutation: switch liqCache.violator and liqCache.liquidator
* note: integrity of liquidation - reduced amount of the right account 

**author:** jraynaldi3

```
/// @notice debt socialization condition: no collateral mean no debt 
rule noCollateralNoDebt_debtSocialization(
    env e, 
    address account,
    address collateral, 
    uint256 amount,
    uint256 minYieldBalance
){
    bool notSocialization = getSocializeDebt();
    require userOwed[account] == getOwedExt(account);
    require ghost_collaterals[account][0] == ERC20a;
    require ghost_collaterals[account][1] == ERC20b;

    liquidate(e, account, ERC20b, amount, minYieldBalance);

    assert !notSocialization => (ERC20a.balanceOf(e, account) == 0 && ERC20b.balanceOf(e, account) == 0 => getCurrentOwedExt(e, account) == 0);
}
```


### Mutant: Liquidation_1

* mutation: switch liquidator and violator
* note: integrity of liquidation - reduced amount of the right account 

**author:** jraynaldi3

```
/// @notice debt socialization condition: no collateral mean no debt 
rule noCollateralNoDebt_debtSocialization(
    env e, 
    address account,
    address collateral, 
    uint256 amount,
    uint256 minYieldBalance
){
    bool notSocialization = getSocializeDebt();
    require userOwed[account] == getOwedExt(account);
    require ghost_collaterals[account][0] == ERC20a;
    require ghost_collaterals[account][1] == ERC20b;
    // require  !notSocialization => (ERC20a.balanceOf(e, account) == 0 && ERC20b.balanceOf(e, account) == 0 => userOwed[account] <= 0x80000000);
    

    liquidate(e, account, ERC20b, amount, minYieldBalance);

    assert !notSocialization => (ERC20a.balanceOf(e, account) == 0 && ERC20b.balanceOf(e, account) == 0 => getCurrentOwedExt(e, account) == 0);
}
```


### Mutant: Liquidation_2

* mutation: `==` => `>=`
* note: monotonicity of liquidation - something has to be paid for non worthless collateral 

**author:** BenRai1

```
    //calculateLiquidation works
    rule calculateLiquidationIntegraty(env e) {
        //FUNCTION PARAMETER
        LiquidationHarness.VaultCache vaultCache;
        address liquidator;
        address violator;
        address collateral;
        uint256 desiredRepay;
        bool isRecognizedCollateral = isRecognizedCollateralExt(collateral);
        bool isCollateralEnabled = isCollateralEnabledExt(violator, collateral);
        bool isAccountStatusCheckDeferred = isAccountStatusCheckDeferredExt(violator);
        bool isInLiquidationCoolOff = isInLiquidationCoolOffExt(e, violator);
        //VALUES CALCULATED
        LiquidationHarness.Assets liability = getCurrentOwedExt(e, vaultCache, violator);
        address[] collaterals = getCollateralsExt(violator);

        LiquidationHarness.Assets repayCalculated;
        uint256 yieldBalanceCalculated;
        repayCalculated, yieldBalanceCalculated = calculateMaxLiquidationHarness(e, vaultCache, violator, collateral, collaterals, liability, 0,0);

        //CAPED VALUES
        mathint yieldBalanceCapped; 
        if(repayCalculated != 0){
            yieldBalanceCapped = desiredRepay * yieldBalanceCalculated / repayCalculated;
        } else{
            yieldBalanceCapped = 0;
        }

        //FUNCTION CALL
        address liquidatorCall;
        address violatorCall;
        address collateralCall;
        address[] collateralsCall;
        LiquidationHarness.Assets liabilityCall;
        LiquidationHarness.Assets repayCall;
        uint256 yieldBalanceCall;
        liquidatorCall,violatorCall,collateralCall,collateralsCall,liabilityCall,repayCall,yieldBalanceCall  = calculateLiquidationExt(e, vaultCache,liquidator, violator, collateral, desiredRepay);

        // ASSERTS
        //assert1: if liabilities are 0, the returnValues are 0
        assert(liability == 0 => repayCall == 0 && yieldBalanceCall == 0, "Liabilities are 0, but the return values are not 0");

        //assert2: if liabilities are not 0 and desiredRepay == max_uint256, the returnValues are the same as in the calculated values
        assert(liability != 0 && desiredRepay == max_uint256 => to_mathint(repayCalculated) == to_mathint(repayCall) && yieldBalanceCalculated == yieldBalanceCall, "Liabilities are not 0 and desiredRepay == max_uint256, but the return values are not the same as in the calculated values");

        //assert3: if liabilities are not 0 and desiredRepay != max_uint256 and repay > 0, the returnValues are the same as in the caped values 
        assert(liability != 0 && desiredRepay != max_uint256 && to_mathint(repayCalculated) > 0 => to_mathint(desiredRepay) == to_mathint(repayCall) && yieldBalanceCapped == to_mathint(yieldBalanceCall), "Liabilities are not 0 and desiredRepay != max_uint256 and repay > 0, but the return values are not the same as in the caped values");
    }
```


### Mutant: Liquidation_3

* mutation: switch lines and use `liqCache.repay` instead of `maxRepay`, using the wrong units
* note: integrity of liquidation - reduced amount 

**author:** BenRai1

```
    //calculateLiquidation works
    rule calculateLiquidationIntegraty(env e) {
        //FUNCTION PARAMETER
        LiquidationHarness.VaultCache vaultCache;
        address liquidator;
        address violator;
        address collateral;
        uint256 desiredRepay;
        bool isRecognizedCollateral = isRecognizedCollateralExt(collateral);
        bool isCollateralEnabled = isCollateralEnabledExt(violator, collateral);
        bool isAccountStatusCheckDeferred = isAccountStatusCheckDeferredExt(violator);
        bool isInLiquidationCoolOff = isInLiquidationCoolOffExt(e, violator);
        //VALUES CALCULATED
        LiquidationHarness.Assets liability = getCurrentOwedExt(e, vaultCache, violator);
        address[] collaterals = getCollateralsExt(violator);

        LiquidationHarness.Assets repayCalculated;
        uint256 yieldBalanceCalculated;
        repayCalculated, yieldBalanceCalculated = calculateMaxLiquidationHarness(e, vaultCache, violator, collateral, collaterals, liability, 0,0);

        //CAPED VALUES
        mathint yieldBalanceCapped; 
        if(repayCalculated != 0){
            yieldBalanceCapped = desiredRepay * yieldBalanceCalculated / repayCalculated;
        } else{
            yieldBalanceCapped = 0;
        }

        //FUNCTION CALL
        address liquidatorCall;
        address violatorCall;
        address collateralCall;
        address[] collateralsCall;
        LiquidationHarness.Assets liabilityCall;
        LiquidationHarness.Assets repayCall;
        uint256 yieldBalanceCall;
        liquidatorCall,violatorCall,collateralCall,collateralsCall,liabilityCall,repayCall,yieldBalanceCall  = calculateLiquidationExt(e, vaultCache,liquidator, violator, collateral, desiredRepay);

        // ASSERTS
        //assert1: if liabilities are 0, the returnValues are 0
        assert(liability == 0 => repayCall == 0 && yieldBalanceCall == 0, "Liabilities are 0, but the return values are not 0");

        //assert2: if liabilities are not 0 and desiredRepay == max_uint256, the returnValues are the same as in the calculated values
        assert(liability != 0 && desiredRepay == max_uint256 => to_mathint(repayCalculated) == to_mathint(repayCall) && yieldBalanceCalculated == yieldBalanceCall, "Liabilities are not 0 and desiredRepay == max_uint256, but the return values are not the same as in the calculated values");

        //assert3: if liabilities are not 0 and desiredRepay != max_uint256 and repay > 0, the returnValues are the same as in the caped values 
        assert(liability != 0 && desiredRepay != max_uint256 && to_mathint(repayCalculated) > 0 => to_mathint(desiredRepay) == to_mathint(repayCall) && yieldBalanceCapped == to_mathint(yieldBalanceCall), "Liabilities are not 0 and desiredRepay != max_uint256 and repay > 0, but the return values are not the same as in the caped values");
    }
```


### Mutant: Governance_0

* mutation: remove governorOnly modifier
* note: governorOnly modifier integrity, accessControl

**author:** alexzoid-eth

```
// GOV-02 | Only one governor can exist at one time
rule onlyOneGovernorExists(env e1, env e2, method f, calldataarg args)
    filtered { f -> GOVERNOR_ONLY_METHODS(f) } {

    // In this case EVCAuthenticateGovernor() in governorOnly() modifier returns msg.sender
    require(e1.msg.sender != EVC());
    require(e2.msg.sender != EVC());

    // First user is governor admin, second user is another
    require(e1.msg.sender == ghostGovernorAdmin);
    require(e1.msg.sender != e2.msg.sender);

    storage init = lastStorage;

    f@withrevert(e1, args) at init;
    bool revertedGovernor = lastReverted;

    f@withrevert(e2, args) at init;
    bool reverted = lastReverted;

    // If the call with first sender was successful, than the call with another sender shound fail
    assert(!revertedGovernor => reverted);
} 
```


### Mutant: Governance_1

* mutation: add `!` to the condition
* note: fee can be converted. satisfy rule that balance can increase 

**author:** alexzoid-eth

```
// GOV-12 | While distributing fees, total shares MUST not change and accumulated fees are cleared
rule feesDistributionClearAccumulatedFeesNotAffectTotalShares(env e) {

    mathint totalSharesBefore = ghostTotalShares;

    convertFees(e);

    mathint accumulatedFeesAfter = ghostAccumulatedFees;

    assert(accumulatedFeesAfter == 0 && ghostTotalShares == totalSharesBefore);
}
```


### Mutant: Governance_2

* mutation: fail to decrease totalShares by accumulatedFees
* note: totalShares is usm of balances

**author:** alexzoid-eth

```
// GOV-12 | While distributing fees, total shares MUST not change and accumulated fees are cleared
rule feesDistributionClearAccumulatedFeesNotAffectTotalShares(env e) {

    mathint totalSharesBefore = ghostTotalShares;

    convertFees(e);

    mathint accumulatedFeesAfter = ghostAccumulatedFees;

    assert(accumulatedFeesAfter == 0 && ghostTotalShares == totalSharesBefore);
}
```


### Mutant: Borrowing_0

* mutation: add function `sweep`
* note: no decrease in assets to other 

**author:** alexzoid-eth

```
// ST-06 | Cash amount MUST NOT be less than the ERC20 assets stored in the current contract
invariant cashNotLessThanAssets() 
    ghostErc20Balances[currentContract] >= ghostCash
    filtered { f -> !HARNESS_VIEW_METHODS(f) }
```


### Mutant: Borrowing_1

* mutation: mutation: update `<` to `==`, making flashloan repayment optional
* note: no lose of assets in flashloan, total assets of the system 

**author:** alexzoid-eth

```
// ST-06 | Cash amount MUST NOT be less than the ERC20 assets stored in the current contract
invariant cashNotLessThanAssets() 
    ghostErc20Balances[currentContract] >= ghostCash
    filtered { f -> !HARNESS_VIEW_METHODS(f) }
```


### Mutant: Borrowing_2

* mutation: replace `account` with `receiver`
* note: integrity of some token balance (easy mutation)

**author:** jraynaldi3

```
/// @notice only caller can increase their debt 
rule debtIncrease_onlyCaller(
    env e,
    method f,
    calldataarg args,
    address account 
) filtered {f -> !f.isView && f.selector != sig:flashLoan(uint256,bytes).selector} {
    setup(e,account);
    address caller = actualCaller(e);
    mathint before = debtOf(e, account);
    f(e,args);
    mathint after = debtOf(e, account);
    assert before < after => account == caller;
}
```

```
/// @notice adding debt should check user status first 
/// its important since certora prover have limitation to link between evc and vault contract
/// should check this interaction using ghost summarization
rule userCheck_decreaseHealthinessCheck(
    env e, 
    method f,
    calldataarg args,
    address account
) filtered {f-> !f.isView} {
    mathint debtBefore = debtOfExact(e, account);

    f(e, args);

    mathint debtAfter = debtOfExact(e, account);
    assert debtAfter > debtBefore => accountChecked[account];
}
```


### Mutant: Borrowing_3

* mutation: replace `CHECKACCOUNT_CALLER` to `CHECKACCOUNT_NONE`
* note: double counting, no gain (easy mutation)

**author:** jraynaldi3

```
/// @notice adding debt should check user status first 
/// its important since certora prover have limitation to link between evc and vault contract
/// should check this interaction using ghost summarization
rule userCheck_decreaseHealthinessCheck(
    env e, 
    method f,
    calldataarg args,
    address account
) filtered {f-> !f.isView} {
    mathint debtBefore = debtOfExact(e, account);

    f(e, args);

    mathint debtAfter = debtOfExact(e, account);
    assert debtAfter > debtBefore => accountChecked[account];
}
```


