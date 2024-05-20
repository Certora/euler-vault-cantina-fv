import "./Base.spec";

methods {
    // function Cache.loadVault() internal returns (VaultHarness.VaultCache memory) with (env e) => CVLloadVault(e);
    // assumes vault does not update, if you want to have a less strict assumption, use CVLLoadVault above
    function Cache.loadVault() internal returns (VaultHarness.VaultCache memory) with (env e) => CVLLoadVaultAssumeNoUpdate(e);
}

// parameter is meant to be block.timestamp
persistent ghost newInterestBorrows(uint256) returns uint256;


function CVLLoadVaultAssumeNoUpdate(env e) returns VaultHarness.VaultCache {
    VaultHarness.VaultCache vaultCache;
    uint48 lastUpdate = storage_lastInterestAccumulatorUpdate();
    VaultHarness.Owed oldTotalBorrows = storage_totalBorrows(); 
    VaultHarness.Shares oldTotalShares = storage_totalShares();
    require vaultCache.cash == storage_cash();
    uint48 timestamp48 = require_uint48(e.block.timestamp);
    bool updated = timestamp48 != lastUpdate;
    require !updated;
    require vaultCache.lastInterestAccumulatorUpdate == lastUpdate;
    require vaultCache.totalBorrows == oldTotalBorrows;
    require vaultCache.totalShares == oldTotalShares;
    require vaultCache.accumulatedFees == storage_accumulatedFees();
    require vaultCache.interestAccumulator == storage_interestAccumulator();
    // unmodified values
    require vaultCache.supplyCap == storage_supplyCap();
    require vaultCache.borrowCap == storage_borrowCap();
    require vaultCache.hookedOps == storage_hookedOps();
    require vaultCache.configFlags == storage_configFlags();
    require vaultCache.snapshotInitialized == storage_snapshotInitialized();

    require vaultCache.asset == ERC20a;
    require vaultCache.asset == asset();
    require vaultCache.oracle == oracleAddress;
    require vaultCache.unitOfAccount == unitOfAccount;

    return vaultCache;
}


// WIP summarization, use at your discretion
function CVLLoadVault(env e) returns VaultHarness.VaultCache {
    VaultHarness.VaultCache vaultCache;
    uint48 lastUpdate = storage_lastInterestAccumulatorUpdate();
    VaultHarness.Owed oldTotalBorrows = storage_totalBorrows(); 
    VaultHarness.Shares oldTotalShares = storage_totalShares();
    require vaultCache.cash == storage_cash();
    uint48 timestamp48 = require_uint48(e.block.timestamp);
    bool updated = timestamp48 != lastUpdate;
    if(updated) {
        require vaultCache.lastInterestAccumulatorUpdate == timestamp48;

        // totalBorrows
        uint256 interestBorrows = newInterestBorrows(e.block.timestamp);
        require vaultCache.totalBorrows == require_uint144(oldTotalBorrows + interestBorrows);

        // totalShares
        mathint newTotalAssets = vaultCache.cash + vaultCache.totalBorrows;
        // underapproximate interesteFee as 1 (1e4 in impl)
        // feeAssets is a separate variable just for readability.
        uint256 feeAssets = interestBorrows;
        require feeAssets < require_uint256(newTotalAssets);
        if (feeAssets > 0) {
            require vaultCache.totalShares == require_uint112(oldTotalShares * newTotalAssets / (newTotalAssets - feeAssets));
        } else {
            require vaultCache.totalShares == oldTotalShares;
        }

        // accumulatedFees
        mathint accFees = storage_accumulatedFees() +
            vaultCache.totalShares - oldTotalShares;
        require vaultCache.accumulatedFees == require_uint112(accFees);

        // interestAccumulator
        require vaultCache.interestAccumulator >= storage_interestAccumulator();

    } else {
        require vaultCache.lastInterestAccumulatorUpdate == lastUpdate;
        require vaultCache.totalBorrows == oldTotalBorrows;
        require vaultCache.totalShares == oldTotalShares;
        require vaultCache.accumulatedFees == storage_accumulatedFees();
        require vaultCache.interestAccumulator == storage_interestAccumulator();
    }

    // unmodified values
    require vaultCache.supplyCap == storage_supplyCap();
    require vaultCache.borrowCap == storage_borrowCap();
    require vaultCache.hookedOps == storage_hookedOps();
    require vaultCache.configFlags == storage_configFlags();
    require vaultCache.snapshotInitialized == storage_snapshotInitialized();

    require vaultCache.asset == ERC20a;
    require vaultCache.asset == asset();
    require vaultCache.oracle == oracleAddress;
    require vaultCache.unitOfAccount == unitOfAccount;

    return vaultCache;
}

