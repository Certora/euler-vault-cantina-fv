import "./VaultFull.spec";

use rule dustFavorsTheHouse;
use rule underlyingCannotChange;
use rule redeemingAllValidity;
use rule reclaimingProducesAssets;
use invariant totalSupplyIsSumOfBalances; 